"""Cotação de frete via Melhor Envio. Peso/dimensões/preço vêm SEMPRE do PostgreSQL."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import MelhorEnvioSender, Product
from app.services import melhor_envio_client as client
from app.services.melhor_envio_client import MelhorEnvioUnavailable

QUOTE_TTL_MINUTES = 15


def _now():
    return datetime.now(timezone.utc)


def _clean_cep(cep: str) -> str:
    digits = "".join(ch for ch in (cep or "") if ch.isdigit())
    if len(digits) != 8:
        raise HTTPException(status_code=400, detail="CEP inválido. Informe um CEP com 8 dígitos.")
    return digits


def _build_products(db: Session, items: list) -> tuple[list, list, float]:
    """Monta a lista de produtos ME a partir do banco. Valida dados logísticos."""
    me_products, snapshot, insurance_total = [], [], 0.0
    for it in items:
        pid = it.get("product_id")
        qty = int(it.get("quantity", 1) or 1)
        if qty < 1:
            continue
        p = db.get(Product, pid)
        if not p or not p.is_active:
            raise HTTPException(status_code=400, detail="Produto indisponível no carrinho.")
        missing = [f for f, v in (
            ("peso", p.weight_kg), ("largura", p.width_cm), ("altura", p.height_cm), ("comprimento", p.length_cm)
        ) if v is None or float(v) <= 0]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Dados de frete incompletos para '{p.name}'. Cadastre peso e dimensões do produto.",
            )
        price = float(p.price)
        insurance_total += price * qty
        me_products.append({
            "id": p.id,
            "width": float(p.width_cm),
            "height": float(p.height_cm),
            "length": float(p.length_cm),
            "weight": float(p.weight_kg),
            "insurance_value": round(price, 2),
            "quantity": qty,
        })
        snapshot.append({"product_id": p.id, "name": p.name, "quantity": qty, "unitary_value": round(price, 2)})
    if not me_products:
        raise HTTPException(status_code=400, detail="Carrinho vazio.")
    return me_products, snapshot, round(insurance_total, 2)


def _normalize(results: list) -> list:
    options = []
    for s in results or []:
        if not isinstance(s, dict):
            continue
        if s.get("error"):
            continue
        price = s.get("custom_price") or s.get("price")
        if price is None:
            continue
        delivery = s.get("custom_delivery_time") or s.get("delivery_time")
        company = s.get("company") or {}
        options.append({
            "service_id": s.get("id"),
            "name": s.get("name"),
            "company_id": company.get("id"),
            "company_name": company.get("name"),
            "company_picture": company.get("picture"),
            "price": round(float(price), 2),
            "delivery_min": s.get("delivery_range", {}).get("min") if isinstance(s.get("delivery_range"), dict) else None,
            "delivery_max": s.get("delivery_range", {}).get("max") if isinstance(s.get("delivery_range"), dict) else None,
            "delivery_time": delivery,
        })
    options.sort(key=lambda o: o["price"])
    return options


def quote(db: Session, postal_code: str, items: list, user_id: str | None = None) -> dict:
    from app.models import ShippingQuote

    dest = _clean_cep(postal_code)
    sender = db.get(MelhorEnvioSender, 1)
    if not sender or not (sender.postal_code or "").strip():
        raise HTTPException(status_code=400, detail="Remetente não configurado. Configure o endereço de origem no admin.")
    origin = _clean_cep(sender.postal_code)

    me_products, snapshot, insurance = _build_products(db, items)
    payload = {
        "from": {"postal_code": origin},
        "to": {"postal_code": dest},
        "products": me_products,
        "options": {"receipt": False, "own_hand": False, "insurance_value": insurance},
    }
    try:
        raw = client.api_request(db, "POST", "/api/v2/me/shipment/calculate", json=payload)
    except MelhorEnvioUnavailable:
        raise HTTPException(status_code=503, detail="Frete temporariamente indisponível. Tente novamente.")

    options = _normalize(raw)
    if not options:
        raise HTTPException(status_code=422, detail="Não conseguimos calcular o frete para este CEP. Verifique e tente novamente.")

    q = ShippingQuote(
        id=str(uuid.uuid4()),
        user_id=user_id,
        destination_postal_code=dest,
        items=[{"product_id": i["product_id"], "quantity": i["quantity"]} for i in snapshot],
        volumes=me_products,
        results=options,
        created_at=_now().isoformat(),
        expires_at=(_now() + timedelta(minutes=QUOTE_TTL_MINUTES)).isoformat(),
    )
    db.add(q)
    db.commit()
    return {"quote_id": q.id, "expires_at": q.expires_at, "destination_postal_code": dest, "options": options}


def get_valid_quote(db: Session, quote_id: str):
    from app.models import ShippingQuote

    q = db.get(ShippingQuote, quote_id)
    if not q:
        raise HTTPException(status_code=404, detail="Cotação não encontrada. Calcule o frete novamente.")
    try:
        exp = datetime.fromisoformat(q.expires_at)
    except Exception:
        exp = _now()
    if exp <= _now():
        raise HTTPException(status_code=409, detail="A cotação de frete expirou. Recalcule o frete.")
    return q
