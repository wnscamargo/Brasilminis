"""Testes mockados do Melhor Envio (SANDBOX) — não dependem da internet (respx)."""
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx

from app.core.config import settings
from app.core.crypto import decrypt
from app.db.session import SessionLocal
from app.models import (
    MelhorEnvioSender,
    MelhorEnvioShipment,
    MelhorEnvioToken,
    Order,
    Product,
    ShippingQuote,
)
from app.services import melhor_envio_auth_service as auth
from app.services import melhor_envio_client as client
from app.services import melhor_envio_quote_service as quote_svc
from app.services import melhor_envio_shipment_service as ship_svc
from app.services import melhor_envio_tracking_service as track_svc

BASE = settings.MELHOR_ENVIO_BASE_URL


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "MELHOR_ENVIO_CLIENT_ID", "123", raising=False)
    monkeypatch.setattr(settings, "MELHOR_ENVIO_CLIENT_SECRET", "secret", raising=False)
    monkeypatch.setattr(settings, "MELHOR_ENVIO_REDIRECT_URI", "https://x.test/api/admin/melhor-envio/callback", raising=False)
    # Isolamento: garante linha limpa (env sandbox) entre testes.
    s = SessionLocal()
    try:
        row = s.get(MelhorEnvioToken, 1)
        if row:
            s.delete(row)
            s.commit()
    finally:
        s.close()
    yield


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


def _seed_token(db, expires_in_s=3600):
    row = db.get(MelhorEnvioToken, 1)
    if not row:
        row = MelhorEnvioToken(id=1)
        db.add(row)
    from app.core.crypto import encrypt
    row.access_token_enc = encrypt("access-abc")
    row.refresh_token_enc = encrypt("refresh-xyz")
    row.expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in_s)).isoformat()
    row.last_error = None
    db.commit()
    return row


def _seed_sender(db):
    row = db.get(MelhorEnvioSender, 1) or MelhorEnvioSender(id=1)
    row.name = "Brasil Minis"; row.email = "c@b.com"; row.document = "12345678000199"
    row.postal_code = "01018020"; row.address = "Rua A"; row.number = "10"
    row.district = "Centro"; row.city = "SP"; row.state_abbr = "SP"
    db.add(row); db.commit()
    return row


def _mk_product(db, with_dims=True):
    p = Product(id=str(uuid.uuid4()), name="Teste Frete", slug=f"tf-{uuid.uuid4().hex[:6]}",
                price=100, stock=50, is_active=True)
    if with_dims:
        p.weight_kg = 0.3; p.width_cm = 11; p.height_cm = 4; p.length_cm = 16
    db.add(p); db.commit()
    return p


# ---------------- Credenciais no banco / troca de ambiente ----------------
def test_credentials_saved_in_db_and_secret_encrypted(db, monkeypatch):
    # Zera o fallback do .env para garantir que a config vem do banco.
    monkeypatch.setattr(settings, "MELHOR_ENVIO_CLIENT_ID", "", raising=False)
    monkeypatch.setattr(settings, "MELHOR_ENVIO_CLIENT_SECRET", "", raising=False)
    monkeypatch.setattr(settings, "MELHOR_ENVIO_REDIRECT_URI", "", raising=False)
    auth.save_credentials(db, {
        "environment": "sandbox", "client_id": "APPID", "client_secret": "APPSECRET",
        "redirect_uri": "https://x.test/api/admin/melhor-envio/callback",
    })
    row = db.get(MelhorEnvioToken, 1)
    assert row.client_id == "APPID"
    assert row.client_secret_enc and row.client_secret_enc != "APPSECRET"
    assert decrypt(row.client_secret_enc) == "APPSECRET"
    cfg = client.get_config(db)
    assert cfg["configured"] is True and cfg["client_secret"] == "APPSECRET"
    creds = auth.get_credentials(db)
    assert creds["client_secret_masked"] == "••••••"
    assert "APPSECRET" not in str(creds)


def test_environment_switch_clears_session(db, monkeypatch):
    monkeypatch.setattr(settings, "MELHOR_ENVIO_CLIENT_ID", "", raising=False)
    monkeypatch.setattr(settings, "MELHOR_ENVIO_CLIENT_SECRET", "", raising=False)
    monkeypatch.setattr(settings, "MELHOR_ENVIO_REDIRECT_URI", "", raising=False)
    auth.save_credentials(db, {"environment": "sandbox", "client_id": "A", "client_secret": "S",
                               "redirect_uri": "https://x.test/cb"})
    _seed_token(db)  # simula conta conectada
    row = db.get(MelhorEnvioToken, 1)
    row.environment = "sandbox"; row.account_email = "conta@sandbox.com"; db.commit()
    # Trocar de ambiente desassocia a sessão anterior.
    auth.save_credentials(db, {"environment": "production"})
    row = db.get(MelhorEnvioToken, 1)
    assert row.environment == "production"
    assert row.access_token_enc is None and row.refresh_token_enc is None
    assert row.account_email is None


def test_scopes_exclude_cancel_and_tracking():
    assert "shipping-cancel" not in auth.SCOPES
    assert "shipping-tracking" not in auth.SCOPES
    assert "shipping-calculate" in auth.SCOPES


# ---------------- OAuth ----------------
def test_auth_url_and_state(db):
    out = auth.build_auth_url(db)
    assert "oauth/authorize" in out["authorization_url"]
    assert "scope=" in out["authorization_url"]
    st = out["state"]
    assert auth.validate_state(db, st) is True
    assert auth.validate_state(db, st) is False  # state consumido


@respx.mock
def test_exchange_code_encrypts_token(db):
    respx.post(f"{BASE}/oauth/token").mock(return_value=httpx.Response(200, json={
        "access_token": "ACCESS123", "refresh_token": "REFRESH123", "expires_in": 2592000, "token_type": "Bearer"
    }))
    auth.exchange_code(db, "code-abc")
    row = db.get(MelhorEnvioToken, 1)
    assert row.access_token_enc and row.access_token_enc != "ACCESS123"  # criptografado
    assert decrypt(row.access_token_enc) == "ACCESS123"


@respx.mock
def test_refresh_when_expired(db):
    _seed_token(db, expires_in_s=-10)  # já expirado
    token_route = respx.post(f"{BASE}/oauth/token").mock(return_value=httpx.Response(200, json={
        "access_token": "NEWACCESS", "refresh_token": "NEWREFRESH", "expires_in": 3600}))
    api_route = respx.get(f"{BASE}/api/v2/me/user").mock(return_value=httpx.Response(200, json={"email": "u@e.com"}))
    out = client.api_request(db, "GET", "/api/v2/me/user")
    assert token_route.called and api_route.called
    assert out["email"] == "u@e.com"
    assert decrypt(db.get(MelhorEnvioToken, 1).access_token_enc) == "NEWACCESS"


@respx.mock
def test_401_triggers_single_retry(db):
    _seed_token(db)
    respx.post(f"{BASE}/oauth/token").mock(return_value=httpx.Response(200, json={
        "access_token": "REFRESHED", "expires_in": 3600}))
    route = respx.get(f"{BASE}/api/v2/me/user").mock(side_effect=[
        httpx.Response(401), httpx.Response(200, json={"email": "ok@e.com"})])
    out = client.api_request(db, "GET", "/api/v2/me/user")
    assert out["email"] == "ok@e.com"
    assert route.call_count == 2


@respx.mock
def test_api_down_raises_unavailable(db):
    _seed_token(db)
    respx.get(f"{BASE}/api/v2/me/user").mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(client.MelhorEnvioUnavailable):
        client.api_request(db, "GET", "/api/v2/me/user")


# ---------------- Cotação ----------------
@respx.mock
def test_quote_success_and_normalization(db):
    _seed_token(db); _seed_sender(db)
    p = _mk_product(db, with_dims=True)
    respx.post(f"{BASE}/api/v2/me/shipment/calculate").mock(return_value=httpx.Response(200, json=[
        {"id": 1, "name": "PAC", "price": "24.90", "custom_price": "24.90", "delivery_time": 5,
         "company": {"id": 1, "name": "Correios"}, "delivery_range": {"min": 4, "max": 6}},
        {"id": 2, "name": "SEDEX", "price": "39.90", "delivery_time": 2, "company": {"id": 1, "name": "Correios"}},
        {"id": 3, "name": "X", "error": "sem cobertura"},
    ]))
    out = quote_svc.quote(db, "20010-000", [{"product_id": p.id, "quantity": 2}], user_id=None)
    assert out["quote_id"]
    assert len(out["options"]) == 2  # o com erro é descartado
    assert out["options"][0]["price"] == 24.90
    assert out["destination_postal_code"] == "20010000"


def test_quote_invalid_cep(db):
    _seed_sender(db)
    p = _mk_product(db)
    with pytest.raises(Exception) as e:
        quote_svc.quote(db, "123", [{"product_id": p.id, "quantity": 1}])
    assert "CEP" in str(e.value)


def test_quote_missing_dimensions(db):
    _seed_token(db); _seed_sender(db)
    p = _mk_product(db, with_dims=False)
    with pytest.raises(Exception) as e:
        quote_svc.quote(db, "20010000", [{"product_id": p.id, "quantity": 1}])
    assert "incompletos" in str(e.value).lower()


@respx.mock
def test_quote_api_down(db):
    _seed_token(db); _seed_sender(db)
    p = _mk_product(db)
    respx.post(f"{BASE}/api/v2/me/shipment/calculate").mock(side_effect=httpx.ConnectError("x"))
    with pytest.raises(Exception) as e:
        quote_svc.quote(db, "20010000", [{"product_id": p.id, "quantity": 1}])
    assert "503" in str(getattr(e.value, "status_code", "")) or "indisponível" in str(e.value).lower()


def test_quote_expiration(db):
    q = ShippingQuote(id=str(uuid.uuid4()), destination_postal_code="20010000", items=[], volumes=[],
                      results=[], created_at=datetime.now(timezone.utc).isoformat(),
                      expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())
    db.add(q); db.commit()
    with pytest.raises(Exception) as e:
        quote_svc.get_valid_quote(db, q.id)
    assert "expirou" in str(e.value).lower()


# ---------------- Envio: idempotência e transições ----------------
def _prepare_order_with_shipment(db):
    _seed_token(db); _seed_sender(db)
    p = _mk_product(db)
    order = Order(id=str(uuid.uuid4()), order_number="BM999999", user_id="u1", user_name="C",
                  user_email="c@e.com", items=[{"name": "Teste Frete", "quantity": 1, "price": 100}],
                  subtotal=100, discount=0, shipping=24.90, total=124.90, status="confirmado",
                  shipping_provider="melhor_envio", shipping_service_id=1, shipping_service_name="PAC",
                  shipping_company_name="Correios", shipping_price_quoted=24.90, shipping_price_customer=24.90,
                  shipping_quote_snapshot={"service_id": 1, "volumes": [{"height": 4, "width": 11, "length": 16, "weight": 0.3, "quantity": 1}],
                                            "products": [{"name": "Teste Frete", "quantity": 1, "unitary_value": 100}]},
                  recipient_snapshot={"name": "Cli", "document": "12345678900", "email": "c@e.com", "phone": "11",
                                       "street": "R", "number": "1", "district": "C", "city": "RJ", "uf": "RJ", "zip": "20010000"},
                  created_at=datetime.now(timezone.utc).isoformat())
    db.add(order); db.commit()
    return order


@respx.mock
def test_cart_idempotency(db):
    order = _prepare_order_with_shipment(db)
    ship_svc.prepare(db, order.id)
    route = respx.post(f"{BASE}/api/v2/me/cart").mock(return_value=httpx.Response(200, json={"id": "CART-UUID-1", "protocol": "ORD-1"}))
    r1 = ship_svc.insert_cart(db, order.id)
    r2 = ship_svc.insert_cart(db, order.id)  # segunda chamada não cria outra etiqueta
    assert r1["cart_order_id"] == "CART-UUID-1" == r2["cart_order_id"]
    assert route.call_count == 1


@respx.mock
def test_full_shipment_flow(db):
    order = _prepare_order_with_shipment(db)
    ship_svc.prepare(db, order.id)
    respx.post(f"{BASE}/api/v2/me/cart").mock(return_value=httpx.Response(200, json={"id": "CART-2", "protocol": "P2"}))
    ship_svc.insert_cart(db, order.id)
    respx.post(f"{BASE}/api/v2/me/shipment/checkout").mock(return_value=httpx.Response(200, json={"purchase": {"orders": [{"status": "released", "price": 22.80}]}}))
    r = ship_svc.checkout(db, order.id)
    assert r["internal_status"] == "purchased"
    respx.post(f"{BASE}/api/v2/me/shipment/generate").mock(return_value=httpx.Response(200, json={"CART-2": {"status": "generated", "tracking": "BR123"}}))
    r = ship_svc.generate(db, order.id)
    assert r["internal_status"] == "generated"
    respx.post(f"{BASE}/api/v2/me/shipment/print").mock(return_value=httpx.Response(200, json={"url": "https://label.pdf"}))
    r = ship_svc.print_label(db, order.id)
    assert r["url"] == "https://label.pdf"
    respx.post(f"{BASE}/api/v2/me/shipment/tracking").mock(return_value=httpx.Response(200, json={"CART-2": {"status": "posted", "tracking": "BR123"}}))
    r = track_svc.refresh_tracking(db, order.id)
    assert r["internal_status"] == "posted"
    assert r["external_status"] == "posted"


def test_print_before_generate_blocked(db):
    order = _prepare_order_with_shipment(db)
    ship_svc.prepare(db, order.id)
    with pytest.raises(Exception) as e:
        ship_svc.print_label(db, order.id)
    assert "gere" in str(e.value).lower()
