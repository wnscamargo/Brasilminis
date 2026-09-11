"""Rotas Mercado Pago (TESTE) e consulta de CEP."""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_current_user, get_db
from app.schemas import CardPaymentInput, MpActivateInput, MpSettingsInput, PixPaymentInput
from app.services import cep_service
from app.services import mercado_pago_service as mp

logger = logging.getLogger("payments")
router = APIRouter(prefix="/api", tags=["payments"])


# ---------- CEP ----------
@router.get("/cep/{cep}")
def cep_lookup(cep: str):
    return cep_service.lookup(cep)


# ---------- Admin: Central de Integrações (visão unificada) ----------
@router.get("/admin/integrations")
def integrations_overview(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    from app.services import melhor_envio_auth_service as me_auth
    return {
        "mercado_pago": mp.status(db),
        "melhor_envio": {**me_auth.status(db), **me_auth.get_credentials(db)},
    }


# ---------- Admin: Mercado Pago ----------
@router.get("/admin/mercado-pago/status")
def mp_status(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return mp.status(db)


@router.put("/admin/mercado-pago/settings")
def mp_save(payload: MpSettingsInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return mp.save_settings(db, payload.model_dump(exclude_unset=True))


@router.post("/admin/mercado-pago/test")
def mp_test(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return mp.test_connection(db)


@router.post("/admin/mercado-pago/activate")
def mp_activate(payload: MpActivateInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return mp.activate_production(db, payload.confirm)


@router.post("/admin/mercado-pago/disconnect")
def mp_disconnect(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return mp.disconnect(db)


@router.get("/admin/orders/{order_id}/payment")
def mp_query(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return mp.query_payment(db, order_id)


# ---------- Public: Public Key para o SDK (nunca o Access Token) ----------
@router.get("/mercado-pago/public-key")
def mp_public_key(db: Session = Depends(get_db)):
    st = mp.status(db)
    if not st.get("public_key"):
        raise HTTPException(status_code=503, detail="Mercado Pago não configurado.")
    return {"public_key": st["public_key"], "environment": st["environment"], "enabled": mp.is_active(db)}


# ---------- Cliente: criação de pagamento ----------
@router.post("/payments/pix")
def pay_pix(payload: PixPaymentInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return mp.create_pix(db, payload.order_id, user)


@router.post("/payments/card")
def pay_card(payload: CardPaymentInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    card = payload.model_dump()
    card.pop("order_id", None)
    return mp.create_card(db, payload.order_id, user, card)


@router.get("/payments/{order_id}/status")
def payment_status(order_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import Order
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user["id"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if order.payment_external_id:
        return mp.query_payment(db, order_id)
    return {"status": order.payment_status, "status_detail": order.payment_status_detail}


# ---------- Webhook (público, HMAC + idempotência) ----------
@router.post("/webhooks/mercado-pago")
async def mp_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    try:
        body = json.loads(raw) if raw else {}
    except Exception:
        body = {}
    data_id = request.query_params.get("data.id") or (body.get("data") or {}).get("id")
    x_signature = request.headers.get("x-signature", "")
    x_request_id = request.headers.get("x-request-id", "")
    return mp.process_webhook(db, body, str(data_id) if data_id else "", x_signature, x_request_id)
