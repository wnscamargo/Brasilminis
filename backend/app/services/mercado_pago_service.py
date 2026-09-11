"""Mercado Pago (Orders API, TESTE). Access Token só no backend, cifrado.

Produção BLOQUEADA nesta fase: o backend recusa environment=production.
"""
import hashlib
import hmac
import logging
import re
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import mp_decrypt, mp_encrypt
from app.models import MpSettings, MpWebhookEvent, Order, PaymentAuditLog
from app.utils import to_dict

logger = logging.getLogger("mercado_pago")
TIMEOUT = httpx.Timeout(20.0, connect=10.0)


class MpUnavailable(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Orders API -> status interno (preserva original)
STATUS_MAP = {
    "processed": "approved", "approved": "approved", "accredited": "approved",
    "processing": "pending", "in_process": "pending", "pending": "pending", "action_required": "pending",
    "failed": "rejected", "rejected": "rejected",
    "canceled": "cancelled", "cancelled": "cancelled", "expired": "cancelled",
    "refunded": "refunded", "charged_back": "charged_back",
}


def _log(db: Session, order_id, event, detail=None):
    db.add(PaymentAuditLog(id=str(uuid.uuid4()), order_id=order_id, event=event, detail=detail, created_at=_now()))


# ---------------- Settings ----------------
def get_row(db: Session) -> MpSettings | None:
    return db.get(MpSettings, 1)


def status(db: Session) -> dict:
    row = get_row(db)
    if not row or not row.public_key or not row.access_token_enc:
        st = "not_configured"
    else:
        st = row.status or "configured"
    return {
        "environment": row.environment if row else "test",
        "public_key": row.public_key if row else None,
        "access_token_masked": "••••••••••" if (row and row.access_token_enc) else None,
        "is_enabled": bool(row.is_enabled) if row else False,
        "status": st,
        "last_test_at": row.last_test_at if row else None,
        "last_error": row.last_error if row else None,
    }


def save_settings(db: Session, data: dict) -> dict:
    if (data.get("environment") or "test") != "test":
        raise HTTPException(status_code=400, detail="Produção está bloqueada nesta fase. Use o ambiente de TESTE.")
    row = get_row(db)
    if not row:
        row = MpSettings(id=1, created_at=_now())
        db.add(row)
    row.environment = "test"
    if data.get("public_key"):
        row.public_key = data["public_key"].strip()
    if data.get("access_token"):
        row.access_token_enc = mp_encrypt(data["access_token"].strip())
    if data.get("webhook_secret"):
        row.webhook_secret_enc = mp_encrypt(data["webhook_secret"].strip())
    row.is_enabled = bool(data.get("is_enabled", row.is_enabled))
    row.status = "configured" if (row.public_key and row.access_token_enc) else "not_configured"
    row.last_error = None
    row.updated_at = _now()
    db.commit()
    return status(db)


def disconnect(db: Session) -> dict:
    row = get_row(db)
    if row:
        db.delete(row)
        db.commit()
    return {"status": "not_configured"}


def _access_token(db: Session) -> str:
    row = get_row(db)
    if not row or not row.access_token_enc:
        raise HTTPException(status_code=400, detail="Mercado Pago não configurado.")
    if row.environment != "test":
        raise HTTPException(status_code=400, detail="Produção bloqueada nesta fase.")
    token = mp_decrypt(row.access_token_enc)
    if not token:
        raise HTTPException(status_code=400, detail="Credencial inválida. Cadastre o Access Token novamente.")
    return token


def _headers(token: str, idem: str | None = None) -> dict:
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if idem:
        h["X-Idempotency-Key"] = idem
    return h


def _post(db: Session, path: str, payload: dict, idem: str):
    token = _access_token(db)
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.post(f"{settings.MERCADO_PAGO_API_BASE}{path}", headers=_headers(token, idem), json=payload)
    except httpx.HTTPError:
        raise MpUnavailable()
    if r.status_code >= 500:
        raise MpUnavailable()
    if r.is_error:
        detail = "Não foi possível processar o pagamento."
        try:
            body = r.json()
            if body.get("message"):
                detail = f"Mercado Pago: {body['message']}"
        except Exception:
            pass
        raise HTTPException(status_code=r.status_code, detail=detail)
    return r.json()


def _get(db: Session, path: str):
    token = _access_token(db)
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.get(f"{settings.MERCADO_PAGO_API_BASE}{path}", headers=_headers(token))
    except httpx.HTTPError:
        raise MpUnavailable()
    if r.status_code >= 500:
        raise MpUnavailable()
    if r.is_error:
        raise HTTPException(status_code=r.status_code, detail="Falha ao consultar o Mercado Pago.")
    return r.json()


def test_connection(db: Session) -> dict:
    row = get_row(db)
    if not row or not row.access_token_enc:
        return {"ok": False, "message": "Configure Public Key e Access Token."}
    try:
        _get(db, "/users/me")
    except MpUnavailable:
        row.status = "error"; row.last_error = "unavailable"; row.last_test_at = _now(); db.commit()
        return {"ok": False, "message": "Mercado Pago indisponível."}
    except HTTPException:
        row.status = "invalid"; row.last_error = "invalid_credentials"; row.last_test_at = _now(); db.commit()
        return {"ok": False, "message": "Credencial inválida."}
    row.status = "connected"; row.last_error = None; row.last_test_at = _now(); db.commit()
    return {"ok": True}


# ---------------- Payments (Orders API) ----------------
def _apply_payment_snapshot(db: Session, order: Order, data: dict):
    payments = (data.get("transactions") or {}).get("payments") or []
    p = payments[0] if payments else {}
    ext_status = p.get("status") or data.get("status")
    order.payment_provider = "mercado_pago"
    order.payment_external_id = data.get("id")
    order.payment_mp_id = p.get("id")
    order.payment_status_raw = ext_status
    order.payment_status_detail = p.get("status_detail") or data.get("status_detail")
    order.payment_status = STATUS_MAP.get(str(ext_status).lower(), "pending")
    if not order.payment_created_at:
        order.payment_created_at = _now()
    if order.payment_status == "approved" and not order.payment_approved_at:
        order.payment_approved_at = _now()


def _order_amount(order: Order) -> str:
    return f"{float(order.total):.2f}"


def create_pix(db: Session, order_id: str, user: dict) -> dict:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user["id"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if order.payment_external_id and order.payment_status in ("pending", "approved"):
        # idempotência: pagamento já criado
        return _pix_public(order)
    idem = order.payment_idempotency_key or str(uuid.uuid4())
    order.payment_idempotency_key = idem
    payload = {
        "type": "online", "processing_mode": "automatic",
        "total_amount": _order_amount(order),  # backend é a fonte da verdade
        "external_reference": order.id,
        "payer": {"email": order.user_email},
        "transactions": {"payments": [{
            "amount": _order_amount(order),
            "payment_method": {"id": "pix", "type": "bank_transfer"},
            "expiration_time": "PT30M",
        }]},
    }
    try:
        data = _post(db, "/v1/orders", payload, idem)
    except MpUnavailable:
        raise HTTPException(status_code=503, detail="Pagamento temporariamente indisponível. Tente novamente.")
    _apply_payment_snapshot(db, order, data)
    order.payment_amount = order.total
    order._mp_raw = data  # não persistido
    _log(db, order.id, "PAYMENT_CREATED", f"pix {order.payment_status}")
    db.commit()
    return _pix_public(order, data)


def _pix_public(order: Order, data: dict | None = None) -> dict:
    method = {}
    if data:
        payments = (data.get("transactions") or {}).get("payments") or []
        if payments:
            method = payments[0].get("payment_method") or {}
    return {
        "order_id": order.id,
        "payment_provider": "mercado_pago",
        "payment_external_id": order.payment_external_id,
        "payment_id": order.payment_mp_id,
        "status": order.payment_status,
        "status_detail": order.payment_status_detail,
        "qr_code": method.get("qr_code"),
        "qr_code_base64": method.get("qr_code_base64"),
        "copy_paste": method.get("qr_code"),
        "ticket_url": method.get("ticket_url"),
        "expiration": "PT30M",
    }


def create_card(db: Session, order_id: str, user: dict, card: dict) -> dict:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user["id"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if order.payment_external_id and order.payment_status in ("approved",):
        return {"order_id": order.id, "status": order.payment_status, "status_detail": order.payment_status_detail}
    idem = order.payment_idempotency_key or str(uuid.uuid4())
    order.payment_idempotency_key = idem
    pm = {"id": card["payment_method_id"], "type": "credit_card",
          "token": card["token"], "installments": int(card.get("installments") or 1)}
    if card.get("issuer_id"):
        pm["issuer_id"] = int(card["issuer_id"])
    payload = {
        "type": "online", "processing_mode": "automatic",
        "total_amount": _order_amount(order),
        "external_reference": order.id,
        "payer": {"email": card.get("payer_email") or order.user_email},
        "transactions": {"payments": [{"amount": _order_amount(order), "payment_method": pm}]},
    }
    try:
        data = _post(db, "/v1/orders", payload, idem)
    except MpUnavailable:
        raise HTTPException(status_code=503, detail="Pagamento temporariamente indisponível. Tente novamente.")
    _apply_payment_snapshot(db, order, data)
    order.payment_amount = order.total
    order.payment_method = "card"
    _log(db, order.id, "PAYMENT_CREATED", f"card {order.payment_status}")
    if order.payment_status == "approved":
        _log(db, order.id, "PAYMENT_APPROVED")
    db.commit()
    return {"order_id": order.id, "payment_id": order.payment_mp_id,
            "status": order.payment_status, "status_detail": order.payment_status_detail}


def query_payment(db: Session, order_id: str) -> dict:
    order = db.get(Order, order_id)
    if not order or not order.payment_external_id:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado para este pedido.")
    try:
        data = _get(db, f"/v1/orders/{order.payment_external_id}")
    except MpUnavailable:
        raise HTTPException(status_code=503, detail="Mercado Pago indisponível.")
    _apply_payment_snapshot(db, order, data)
    _log(db, order.id, "PAYMENT_" + (order.payment_status or "PENDING").upper())
    db.commit()
    return payment_admin_view(order)


def payment_admin_view(order: Order) -> dict:
    return {
        "provider": order.payment_provider,
        "method": order.payment_method,
        "status": order.payment_status,
        "status_detail": order.payment_status_detail,
        "status_raw": order.payment_status_raw,
        "amount": float(order.payment_amount) if order.payment_amount is not None else None,
        "external_id": order.payment_external_id,
        "mp_id": order.payment_mp_id,
        "created_at": order.payment_created_at,
        "approved_at": order.payment_approved_at,
    }


# ---------------- Webhook ----------------
def verify_signature(x_signature: str, x_request_id: str, data_id: str, secret: str) -> bool:
    if not x_signature or not secret:
        return False
    vals = dict(re.findall(r"(?:^|,)\s*(ts|v1)=([^,]+)", x_signature))
    if not vals.get("ts") or not vals.get("v1"):
        return False
    manifest = ""
    if data_id:
        manifest += f"id:{data_id.lower()};"
    if x_request_id:
        manifest += f"request-id:{x_request_id};"
    manifest += f"ts:{vals['ts']};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, vals["v1"])


def process_webhook(db: Session, body: dict, data_id: str, x_signature: str, x_request_id: str) -> dict:
    row = get_row(db)
    secret = mp_decrypt(row.webhook_secret_enc) if (row and row.webhook_secret_enc) else None
    if secret and not verify_signature(x_signature, x_request_id, data_id, secret):
        raise HTTPException(status_code=401, detail="assinatura inválida")

    ts = ""
    m = re.search(r"ts=([^,]+)", x_signature or "")
    if m:
        ts = m.group(1)
    dedup = hashlib.sha256(f"{body.get('type')}:{data_id}:{ts}".encode()).hexdigest()
    if db.get(MpWebhookEvent, dedup):
        return {"ok": True, "deduplicated": True}
    db.add(MpWebhookEvent(id=dedup, type=body.get("type"), data_id=data_id, payload=body, received_at=_now()))
    _log(db, None, "WEBHOOK_RECEIVED", body.get("type"))
    db.commit()

    # Confirma pelo backend consultando a Order/payment (nunca confia só no webhook)
    if data_id:
        try:
            data = _get(db, f"/v1/orders/{data_id}")
            order = db.query(Order).filter(Order.payment_external_id == data.get("id")).first()
            if not order and data.get("external_reference"):
                order = db.get(Order, data["external_reference"])
            if order:
                prev = order.payment_status
                _apply_payment_snapshot(db, order, data)
                if order.payment_status != prev:
                    _log(db, order.id, "PAYMENT_" + (order.payment_status or "PENDING").upper())
                db.commit()
        except (MpUnavailable, HTTPException):
            pass
    return {"ok": True}
