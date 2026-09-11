"""Rotas Melhor Envio (SANDBOX). Segredos e tokens ficam SOMENTE no backend."""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_current_admin, get_current_user, get_db
from app.models import MelhorEnvioWebhookEvent
from app.schemas import MelhorEnvioCredentialsInput, SenderInput, ShippingQuoteInput
from app.services import melhor_envio_auth_service as auth_service
from app.services import melhor_envio_quote_service as quote_service
from app.services import melhor_envio_shipment_service as shipment_service
from app.services import melhor_envio_tracking_service as tracking_service
from app.services.melhor_envio_client import MelhorEnvioUnavailable

logger = logging.getLogger("melhor_envio")
router = APIRouter(prefix="/api", tags=["melhor-envio"])


# ---------------- Admin: conexão/configuração ----------------
@router.get("/admin/melhor-envio/status")
def me_status(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return auth_service.status(db)


@router.get("/admin/melhor-envio/credentials")
def me_get_credentials(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return auth_service.get_credentials(db)


@router.put("/admin/melhor-envio/credentials")
def me_save_credentials(payload: MelhorEnvioCredentialsInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        return auth_service.save_credentials(db, payload.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/melhor-envio/auth-url")
def me_auth_url(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        return auth_service.build_auth_url(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/melhor-envio/test")
def me_test(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return auth_service.test_connection(db)


@router.post("/admin/melhor-envio/disconnect")
def me_disconnect(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return auth_service.disconnect(db)


@router.get("/admin/melhor-envio/sender")
def me_get_sender(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return auth_service.get_sender(db)


@router.put("/admin/melhor-envio/sender")
def me_update_sender(payload: SenderInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return auth_service.update_sender(db, payload.model_dump(exclude_unset=True))


# ---------------- Callback OAuth (público, validado por state) ----------------
@router.get("/admin/melhor-envio/callback")
def me_callback(code: str = "", state: str = "", error: str = "", db: Session = Depends(get_db)):
    front = settings.FRONTEND_URL or ""
    target = f"{front}/admin/melhor-envio"
    if error:
        return RedirectResponse(f"{target}?connected=0&reason=denied")
    if not code or not auth_service.validate_state(db, state):
        return RedirectResponse(f"{target}?connected=0&reason=invalid_state")
    try:
        auth_service.exchange_code(db, code)
    except (HTTPException, MelhorEnvioUnavailable):
        return RedirectResponse(f"{target}?connected=0&reason=exchange_failed")
    return RedirectResponse(f"{target}?connected=1")


# ---------------- Cotação (cliente autenticado) ----------------
@router.post("/shipping/quote")
def shipping_quote(payload: ShippingQuoteInput, request: Request, db: Session = Depends(get_db)):
    user_id = None
    try:
        user = get_current_user(request, db)
        user_id = user["id"]
    except HTTPException:
        pass  # cotação pode ser feita por visitante
    items = [i.model_dump() for i in payload.items]
    return quote_service.quote(db, payload.postal_code, items, user_id=user_id)


# ---------------- Admin: envio por pedido ----------------
@router.get("/admin/orders/{order_id}/shipment")
def get_shipment(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return shipment_service.serialize(db, order_id)


@router.post("/admin/orders/{order_id}/shipment/prepare")
def prepare_shipment(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return shipment_service.prepare(db, order_id)


@router.post("/admin/orders/{order_id}/shipment/cart")
def cart_shipment(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return shipment_service.insert_cart(db, order_id)


@router.post("/admin/orders/{order_id}/shipment/checkout")
def checkout_shipment(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return shipment_service.checkout(db, order_id)


@router.post("/admin/orders/{order_id}/shipment/generate")
def generate_shipment(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return shipment_service.generate(db, order_id)


@router.get("/admin/orders/{order_id}/shipment/print")
def print_shipment(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return shipment_service.print_label(db, order_id)


@router.post("/admin/orders/{order_id}/shipment/tracking")
def tracking_shipment(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return tracking_service.refresh_tracking(db, order_id)


# ---------------- Webhook (público, HMAC + idempotência) ----------------
@router.post("/webhooks/melhor-envio")
async def me_webhook(request: Request, x_me_signature: str = Header(default=""), db: Session = Depends(get_db)):
    raw = await request.body()
    secret = auth_service.client.get_config(db)["client_secret"] or ""
    if secret and x_me_signature:
        expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        expected_b64 = __import__("base64").b64encode(
            hmac.new(secret.encode(), raw, hashlib.sha256).digest()
        ).decode()
        if not (hmac.compare_digest(expected, x_me_signature) or hmac.compare_digest(expected_b64, x_me_signature)):
            raise HTTPException(status_code=401, detail="assinatura inválida")
    try:
        event = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="payload inválido")

    dedup_id = hashlib.sha256(raw).hexdigest()
    if db.get(MelhorEnvioWebhookEvent, dedup_id):
        return {"ok": True, "deduplicated": True}

    event_name = event.get("event") if isinstance(event, dict) else None
    data = event.get("data") if isinstance(event, dict) else {}
    cart_order_id = (data or {}).get("id") if isinstance(data, dict) else None
    external_status = (data or {}).get("status") if isinstance(data, dict) else None

    db.add(MelhorEnvioWebhookEvent(id=dedup_id, event=event_name, order_ref=cart_order_id, payload=event))
    db.commit()

    if cart_order_id and external_status:
        tracking_service.apply_external_status(db, cart_order_id, external_status, extra=data)
    return {"ok": True}
