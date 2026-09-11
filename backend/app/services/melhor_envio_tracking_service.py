"""Rastreamento do envio e timeline. Preserva o status externo original do Melhor Envio."""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import MelhorEnvioShipment
from app.services import melhor_envio_client as client
from app.services.melhor_envio_client import MelhorEnvioUnavailable

# Mapa status externo ME -> status interno normalizado
STATUS_MAP = {
    "pending": "purchased",
    "released": "purchased",
    "generated": "generated",
    "posted": "posted",
    "in_transit": "posted",
    "delivering": "posted",
    "delivered": "delivered",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "undelivered": "posted",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def refresh_tracking(db: Session, order_id: str) -> dict:
    from app.services.melhor_envio_shipment_service import get_or_create_shipment, serialize

    sh = get_or_create_shipment(db, order_id)
    if not sh.cart_order_id:
        raise HTTPException(status_code=409, detail="Envio ainda não possui etiqueta no Melhor Envio.")
    try:
        resp = client.api_request(db, "POST", "/api/v2/me/shipment/tracking", json={"orders": [sh.cart_order_id]})
    except MelhorEnvioUnavailable:
        raise HTTPException(status_code=503, detail="Rastreamento indisponível no momento. Tente novamente.")

    info = resp.get(sh.cart_order_id) if isinstance(resp, dict) else None
    if isinstance(info, dict):
        ext = info.get("status")
        if ext:
            sh.external_status = ext  # nunca perder o status original
            mapped = STATUS_MAP.get(str(ext).lower())
            if mapped and _rank(mapped) >= _rank(sh.internal_status):
                sh.internal_status = mapped
        if info.get("tracking"):
            sh.tracking_code = info.get("tracking")
        if info.get("melhorenvio_tracking") and not sh.tracking_code:
            sh.tracking_code = info.get("melhorenvio_tracking")
        if info.get("posted_at") and not sh.posted_at:
            sh.posted_at = info.get("posted_at")
        if info.get("delivered_at") and not sh.delivered_at:
            sh.delivered_at = info.get("delivered_at")
        sh.raw = info
    sh.last_tracking_update_at = _now()
    sh.updated_at = _now()
    db.commit()
    return serialize(db, order_id)


_ORDER = ["pending", "prepared", "in_cart", "purchased", "generated", "posted", "delivered"]


def _rank(status: str) -> int:
    try:
        return _ORDER.index(status)
    except ValueError:
        return -1


def apply_external_status(db: Session, cart_order_id: str, external_status: str, extra: dict | None = None):
    """Usado pelo webhook: atualiza pelo cart_order_id sem perder o status original."""
    sh = db.query(MelhorEnvioShipment).filter(MelhorEnvioShipment.cart_order_id == cart_order_id).first()
    if not sh:
        return None
    sh.external_status = external_status
    mapped = STATUS_MAP.get(str(external_status).lower())
    if mapped and _rank(mapped) >= _rank(sh.internal_status):
        sh.internal_status = mapped
    if extra:
        if extra.get("tracking"):
            sh.tracking_code = extra["tracking"]
        if extra.get("posted_at") and not sh.posted_at:
            sh.posted_at = extra["posted_at"]
        if extra.get("delivered_at") and not sh.delivered_at:
            sh.delivered_at = extra["delivered_at"]
    tl = list(sh.timeline or [])
    tl.append({"label": f"Webhook: {external_status}", "at": _now()})
    sh.timeline = tl
    sh.last_tracking_update_at = _now()
    sh.updated_at = _now()
    db.commit()
    return sh
