"""Testes mockados do Mercado Pago (Orders API) — sem internet (respx)."""
import uuid
from datetime import datetime, timezone

import httpx
import pytest
import respx

from app.core.config import settings
from app.core.crypto import mp_decrypt
from app.db.session import SessionLocal
from app.models import MpSettings, MpWebhookEvent, Order
from app.services import mercado_pago_service as mp

API = settings.MERCADO_PAGO_API_BASE


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(autouse=True)
def _clean_state():
    """Isolamento: limpa eventos, settings e pedidos de teste (Postgres compartilhado)."""
    s = SessionLocal()
    try:
        s.query(MpWebhookEvent).delete()
        s.query(Order).filter(Order.user_id == "u1").delete()
        row = s.get(MpSettings, 1)
        if row:
            s.delete(row)
        s.commit()
    finally:
        s.close()
    yield


def _seed_settings(db, enabled=True):
    row = db.get(MpSettings, 1) or MpSettings(id=1)
    row.environment = "test"
    row.public_key = "TEST-PUBKEY"
    from app.core.crypto import mp_encrypt
    row.access_token_enc = mp_encrypt("APP_USR-TEST-TOKEN")
    row.webhook_secret_enc = mp_encrypt("whsecret")
    row.is_enabled = enabled
    row.status = "configured"
    db.add(row); db.commit()
    return row


def _mk_order(db, total=150.0):
    o = Order(id=str(uuid.uuid4()), order_number="BM777", user_id="u1", user_name="C",
              user_email="c@e.com", items=[], subtotal=total, discount=0, shipping=0, total=total,
              status="confirmado", payment_method="pix", payment_status="pending",
              created_at=datetime.now(timezone.utc).isoformat())
    db.add(o); db.commit()
    return o


def test_settings_encrypt_and_no_plain_token(db):
    mp.save_settings(db, {"environment": "test", "public_key": "PK", "access_token": "SECRET-TOKEN"})
    row = db.get(MpSettings, 1)
    assert row.access_token_enc != "SECRET-TOKEN"
    assert mp_decrypt(row.access_token_enc) == "SECRET-TOKEN"
    st = mp.status(db)
    assert st["access_token_masked"] == "••••••••••"
    assert "SECRET-TOKEN" not in str(st)  # nunca vaza


def test_production_requires_confirmation_and_test(db):
    # Salvar produção NÃO ativa automaticamente.
    mp.save_settings(db, {"environment": "production", "public_key": "PK-PROD", "access_token": "APP-PROD"})
    row = db.get(MpSettings, 1)
    assert row.environment == "production"
    assert row.is_enabled is False  # nunca ativa automaticamente
    # Ativar sem teste prévio (status != connected) deve falhar.
    with pytest.raises(Exception) as e:
        mp.activate_production(db, confirm=True)
    assert "teste" in str(e.value).lower()
    # Simula teste OK e tenta ativar sem confirmação.
    row.status = "connected"; db.commit()
    with pytest.raises(Exception) as e2:
        mp.activate_production(db, confirm=False)
    assert "confirma" in str(e2.value).lower()
    # Com teste OK + confirmação, ativa.
    out = mp.activate_production(db, confirm=True)
    assert out["is_enabled"] is True


def test_environment_switch_clears_credentials(db):
    mp.save_settings(db, {"environment": "test", "public_key": "PK-TEST", "access_token": "APP-TEST", "is_enabled": True})
    row = db.get(MpSettings, 1)
    assert row.is_enabled is True and row.public_key == "PK-TEST"
    # Trocar para produção limpa credenciais e desabilita (isolamento).
    mp.save_settings(db, {"environment": "production"})
    row = db.get(MpSettings, 1)
    assert row.environment == "production"
    assert row.public_key is None and row.access_token_enc is None
    assert row.is_enabled is False


def test_is_active_only_when_enabled_and_configured(db):
    assert mp.is_active(db) is False
    mp.save_settings(db, {"environment": "test", "public_key": "PK", "access_token": "T", "is_enabled": True})
    assert mp.is_active(db) is True


@respx.mock
def test_pix_uses_backend_amount(db):
    _seed_settings(db)
    order = _mk_order(db, total=199.90)
    route = respx.post(f"{API}/v1/orders").mock(return_value=httpx.Response(200, json={
        "id": "ORD-1", "external_reference": order.id,
        "transactions": {"payments": [{"id": "PAY-1", "status": "action_required", "status_detail": "waiting_transfer",
            "payment_method": {"qr_code": "PIXCOPYPASTE", "qr_code_base64": "QkFTRTY0"}}]}}))
    out = mp.create_pix(db, order.id, {"id": "u1"})
    assert out["copy_paste"] == "PIXCOPYPASTE"
    assert out["qr_code_base64"] == "QkFTRTY0"
    assert out["status"] == "pending"  # action_required -> pending
    sent = route.calls[0].request
    assert b'"total_amount":"199.90"' in sent.content  # valor vem do backend
    db.refresh(order)
    assert order.payment_provider == "mercado_pago"
    assert order.payment_external_id == "ORD-1"


@respx.mock
def test_pix_idempotent_no_double_create(db):
    _seed_settings(db)
    order = _mk_order(db)
    route = respx.post(f"{API}/v1/orders").mock(return_value=httpx.Response(200, json={
        "id": "ORD-2", "transactions": {"payments": [{"id": "PAY-2", "status": "action_required",
            "payment_method": {"qr_code": "X"}}]}}))
    mp.create_pix(db, order.id, {"id": "u1"})
    mp.create_pix(db, order.id, {"id": "u1"})  # segunda chamada não cria outra order
    assert route.call_count == 1


@respx.mock
def test_card_approved(db):
    _seed_settings(db)
    order = _mk_order(db, total=50.0)
    respx.post(f"{API}/v1/orders").mock(return_value=httpx.Response(200, json={
        "id": "ORD-3", "transactions": {"payments": [{"id": "PAY-3", "status": "processed", "status_detail": "accredited"}]}}))
    out = mp.create_card(db, order.id, {"id": "u1"}, {
        "token": "card-token", "installments": 1, "payment_method_id": "visa", "issuer_id": 310})
    assert out["status"] == "approved"
    db.refresh(order)
    assert order.payment_approved_at is not None


def test_webhook_hmac_valid_and_invalid(db):
    _seed_settings(db)
    secret = "whsecret"
    data_id = "123456"
    ts = "1700000000"
    import hashlib, hmac
    manifest = f"id:{data_id};request-id:req-1;ts:{ts};"
    good = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    assert mp.verify_signature(f"ts={ts},v1={good}", "req-1", data_id, secret) is True
    assert mp.verify_signature(f"ts={ts},v1=deadbeef", "req-1", data_id, secret) is False


@respx.mock
def test_webhook_dedup(db):
    _seed_settings(db)
    order = _mk_order(db)
    order.payment_external_id = "ORD-9"; db.commit()
    respx.get(f"{API}/v1/orders/ORD-9").mock(return_value=httpx.Response(200, json={
        "id": "ORD-9", "external_reference": order.id,
        "transactions": {"payments": [{"id": "P9", "status": "processed", "status_detail": "accredited"}]}}))
    body = {"type": "order", "data": {"id": "ORD-9"}}
    # sem secret válido? seed tem secret -> precisa assinatura; passamos secret vazio removendo webhook_secret
    row = db.get(MpSettings, 1); row.webhook_secret_enc = None; db.commit()
    r1 = mp.process_webhook(db, body, "ORD-9", "", "")
    r2 = mp.process_webhook(db, body, "ORD-9", "", "")
    assert r1.get("ok") and r2.get("deduplicated") is True
    assert db.query(MpWebhookEvent).count() == 1
    db.refresh(order)
    assert order.payment_status == "approved"


def test_status_mapping(db):
    assert mp.STATUS_MAP["processed"] == "approved"
    assert mp.STATUS_MAP["rejected"] == "rejected"
    assert mp.STATUS_MAP["action_required"] == "pending"
    assert mp.STATUS_MAP["refunded"] == "refunded"
    assert mp.STATUS_MAP["charged_back"] == "charged_back"
