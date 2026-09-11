"""Ciclo de vida do envio no Melhor Envio: preparar → carrinho → compra → gerar → imprimir.

Transições idempotentes: nunca cria duas etiquetas por clique duplo.
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import MelhorEnvioSender, MelhorEnvioShipment, Order
from app.services import melhor_envio_client as client
from app.services.melhor_envio_client import MelhorEnvioUnavailable
from app.utils import to_dict

# Ações permitidas por estado interno (evita ação incompatível)
ALLOWED_ACTIONS = {
    "pending": ["prepare"],
    "prepared": ["cart"],
    "in_cart": ["checkout"],
    "purchased": ["generate"],
    "generated": ["print", "tracking"],
    "posted": ["print", "tracking"],
    "delivered": ["print", "tracking"],
    "error": ["prepare", "cart"],
    "cancelled": [],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _unavailable():
    raise HTTPException(status_code=503, detail="Melhor Envio indisponível no momento. Tente novamente.")


def _get_order(db: Session, order_id: str) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


def get_or_create_shipment(db: Session, order_id: str) -> MelhorEnvioShipment:
    sh = db.query(MelhorEnvioShipment).filter(MelhorEnvioShipment.order_id == order_id).first()
    if not sh:
        _get_order(db, order_id)
        sh = MelhorEnvioShipment(id=str(uuid.uuid4()), order_id=order_id, internal_status="pending",
                                 timeline=[], created_at=_now(), updated_at=_now())
        db.add(sh)
        db.commit()
        db.refresh(sh)
    return sh


def _push_timeline(sh: MelhorEnvioShipment, label: str):
    tl = list(sh.timeline or [])
    tl.append({"label": label, "at": _now()})
    sh.timeline = tl


def serialize(db: Session, order_id: str) -> dict:
    sh = get_or_create_shipment(db, order_id)
    data = to_dict(sh)
    data["allowed_actions"] = ALLOWED_ACTIONS.get(sh.internal_status, [])
    return data


def prepare(db: Session, order_id: str) -> dict:
    """Valida remetente/destinatário/snapshot e marca como pronto para o carrinho."""
    order = _get_order(db, order_id)
    sender = db.get(MelhorEnvioSender, 1)
    if not sender or not (sender.postal_code or "").strip():
        raise HTTPException(status_code=400, detail="Remetente não configurado no admin.")
    if not order.shipping_quote_snapshot or not order.recipient_snapshot:
        raise HTTPException(status_code=400, detail="Pedido sem cotação/destinatário congelados (frete não selecionado).")
    sh = get_or_create_shipment(db, order_id)
    if sh.internal_status in ("in_cart", "purchased", "generated", "posted", "delivered"):
        return serialize(db, order_id)  # idempotente
    sh.service_id = order.shipping_service_id
    sh.service_name = order.shipping_service_name
    sh.company_name = order.shipping_company_name
    sh.price = order.shipping_price_quoted
    sh.internal_status = "prepared"
    sh.last_error = None
    _push_timeline(sh, "Envio preparado")
    sh.updated_at = _now()
    db.commit()
    return serialize(db, order_id)


def _build_cart_payload(order: Order, sender: MelhorEnvioSender) -> dict:
    snap = order.shipping_quote_snapshot or {}
    rec = order.recipient_snapshot or {}
    volumes_src = snap.get("volumes") or []
    volumes = []
    for v in volumes_src:
        qty = int(v.get("quantity", 1) or 1)
        for _ in range(max(qty, 1)):
            volumes.append({
                "height": v.get("height"), "width": v.get("width"),
                "length": v.get("length"), "weight": v.get("weight"),
            })
    products = snap.get("products") or [
        {"name": i.get("name"), "quantity": i.get("quantity"), "unitary_value": i.get("price")}
        for i in (order.items or [])
    ]
    insurance = round(sum((p.get("unitary_value") or 0) * (p.get("quantity") or 1) for p in products), 2)
    return {
        "service": order.shipping_service_id,
        "from": {
            "name": sender.name, "company_document": sender.document if len(sender.document or "") > 11 else None,
            "document": sender.document, "state_register": sender.state_register or None,
            "email": sender.email, "phone": sender.phone,
            "address": sender.address, "number": sender.number, "complement": sender.complement or "",
            "district": sender.district, "city": sender.city, "state_abbr": sender.state_abbr,
            "country_id": "BR", "postal_code": "".join(c for c in (sender.postal_code or "") if c.isdigit()),
        },
        "to": {
            "name": rec.get("name"), "document": rec.get("document"),
            "email": rec.get("email"), "phone": rec.get("phone"),
            "address": rec.get("street"), "number": rec.get("number"), "complement": rec.get("complement") or "",
            "district": rec.get("district"), "city": rec.get("city"), "state_abbr": rec.get("uf") or rec.get("state"),
            "country_id": "BR", "postal_code": "".join(c for c in (rec.get("zip") or rec.get("cep") or "") if c.isdigit()),
        },
        "products": products,
        "volumes": volumes,
        "options": {"insurance_value": insurance, "receipt": False, "own_hand": False, "reverse": False, "non_commercial": True},
    }


def insert_cart(db: Session, order_id: str) -> dict:
    order = _get_order(db, order_id)
    sender = db.get(MelhorEnvioSender, 1)
    sh = get_or_create_shipment(db, order_id)
    if sh.cart_order_id:  # idempotência: já inserido
        return serialize(db, order_id)
    if sh.internal_status not in ("prepared", "error", "pending"):
        raise HTTPException(status_code=409, detail="Envio não está pronto para inserir no carrinho.")
    payload = _build_cart_payload(order, sender)
    try:
        resp = client.api_request(db, "POST", "/api/v2/me/cart", json=payload)
    except MelhorEnvioUnavailable:
        sh.last_error = "unavailable"; db.commit(); _unavailable()
    cart_id = resp.get("id") if isinstance(resp, dict) else None
    if not cart_id:
        raise HTTPException(status_code=502, detail="Melhor Envio não retornou o ID do carrinho.")
    sh.cart_order_id = cart_id
    sh.protocol = resp.get("protocol")
    sh.internal_status = "in_cart"
    sh.raw = resp if isinstance(resp, dict) else {"raw": str(resp)}
    sh.last_error = None
    _push_timeline(sh, "Etiqueta inserida no carrinho Melhor Envio")
    sh.updated_at = _now()
    db.commit()
    return serialize(db, order_id)


def checkout(db: Session, order_id: str) -> dict:
    """Compra da etiqueta (paga com saldo Sandbox)."""
    sh = get_or_create_shipment(db, order_id)
    if not sh.cart_order_id:
        raise HTTPException(status_code=409, detail="Insira a etiqueta no carrinho antes de comprar.")
    if sh.internal_status in ("purchased", "generated", "posted", "delivered"):
        return serialize(db, order_id)  # idempotente
    try:
        resp = client.api_request(db, "POST", "/api/v2/me/shipment/checkout", json={"orders": [sh.cart_order_id]})
    except MelhorEnvioUnavailable:
        sh.last_error = "unavailable"; db.commit(); _unavailable()
    sh.internal_status = "purchased"
    sh.purchased_at = _now()
    sh.last_error = None
    _extract_purchase(sh, resp)
    _push_timeline(sh, "Etiqueta comprada (Sandbox)")
    sh.updated_at = _now()
    db.commit()
    return serialize(db, order_id)


def _extract_purchase(sh: MelhorEnvioShipment, resp):
    """Extrai preço/status da resposta de checkout (formato pode variar)."""
    try:
        purchase = resp.get("purchase") if isinstance(resp, dict) else None
        if purchase:
            orders = purchase.get("orders") or []
            if orders:
                o = orders[0]
                sh.external_status = o.get("status") or sh.external_status
                if o.get("price"):
                    sh.price = o.get("price")
                sh.tracking_code = o.get("tracking") or sh.tracking_code
    except Exception:
        pass


def generate(db: Session, order_id: str) -> dict:
    sh = get_or_create_shipment(db, order_id)
    if sh.internal_status not in ("purchased", "generated", "posted", "delivered"):
        raise HTTPException(status_code=409, detail="Compre a etiqueta antes de gerar.")
    if sh.internal_status in ("generated", "posted", "delivered") and sh.generated_at:
        return serialize(db, order_id)  # idempotente
    try:
        resp = client.api_request(db, "POST", "/api/v2/me/shipment/generate", json={"orders": [sh.cart_order_id]})
    except MelhorEnvioUnavailable:
        sh.last_error = "unavailable"; db.commit(); _unavailable()
    info = resp.get(sh.cart_order_id) if isinstance(resp, dict) else None
    if isinstance(info, dict):
        sh.tracking_code = info.get("tracking") or sh.tracking_code
        sh.external_status = info.get("status") or sh.external_status
    sh.internal_status = "generated"
    sh.generated_at = _now()
    sh.last_error = None
    _push_timeline(sh, "Etiqueta gerada")
    sh.updated_at = _now()
    db.commit()
    return serialize(db, order_id)


def print_label(db: Session, order_id: str) -> dict:
    sh = get_or_create_shipment(db, order_id)
    if sh.internal_status not in ("generated", "posted", "delivered"):
        raise HTTPException(status_code=409, detail="Gere a etiqueta antes de imprimir.")
    try:
        resp = client.api_request(db, "POST", "/api/v2/me/shipment/print",
                                  json={"orders": [sh.cart_order_id], "mode": "private"})
    except MelhorEnvioUnavailable:
        _unavailable()
    url = resp.get("url") if isinstance(resp, dict) else None
    if url:
        sh.label_url = url
        sh.updated_at = _now()
        db.commit()
    return {"url": url}
