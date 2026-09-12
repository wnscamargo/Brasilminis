"""E2E tests via public backend URL for Central de Integrações (MP + Melhor Envio).

Focus:
 - /admin/integrations overview
 - Melhor Envio credentials save/get/mask/scopes/environment isolation
 - Mercado Pago settings save/mask/production gating/env switch/public-key
 - Order in simulated mode (MP not configured)
"""
import os
import re
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:3000"
ADMIN_EMAIL = "admin@brasilminis.com"
ADMIN_PASSWORD = "Admin@2025"


def _gen_cpf():
    import random
    while True:
        base = [random.randint(0, 9) for _ in range(9)]
        d1 = sum(base[i] * (10 - i) for i in range(9)) * 10 % 11 % 10
        d2 = (sum(base[i] * (11 - i) for i in range(9)) + d1 * 2) * 10 % 11 % 10
        cpf = "".join(map(str, base + [d1, d2]))
        if cpf != cpf[0] * 11:
            return cpf


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"admin login falhou: {r.status_code} {r.text}"
    yield s
    # cleanup - disconnect MP
    try:
        s.post(f"{BASE_URL}/api/admin/mercado-pago/disconnect", timeout=15)
    except Exception:
        pass


@pytest.fixture(scope="module")
def customer_session():
    """Create a customer session for order tests."""
    s = requests.Session()
    email = f"TEST_cli_{uuid.uuid4().hex[:8]}@test.com"
    reg = s.post(f"{BASE_URL}/api/auth/register",
                 json={"name": "Test Client", "email": email, "password": "Teste@123", "cpf": _gen_cpf()}, timeout=20)
    if reg.status_code not in (200, 201):
        # try login (fallback)
        s.post(f"{BASE_URL}/api/auth/login",
               json={"email": email, "password": "Teste@123"}, timeout=15)
    return s, email


# ---------- MP: ensure disconnected before tests ----------
@pytest.fixture(autouse=True)
def _mp_reset(admin_session):
    admin_session.post(f"{BASE_URL}/api/admin/mercado-pago/disconnect", timeout=15)
    yield


# ---------- Integrations overview ----------
class TestIntegrationsOverview:
    def test_overview_has_both_keys(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/integrations", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "mercado_pago" in data
        assert "melhor_envio" in data
        mp = data["mercado_pago"]
        me = data["melhor_envio"]
        assert "status" in mp and "environment" in mp
        assert "status" in me and "environment" in me and "configured" in me


# ---------- Melhor Envio ----------
class TestMelhorEnvioCredentials:
    def test_save_and_get_masked(self, admin_session):
        payload = {
            "environment": "sandbox",
            "client_id": "12345",
            "client_secret": "s3cr3t-me-value",
            "redirect_uri": "https://brasilminis.com/api/admin/melhor-envio/callback",
        }
        r = admin_session.put(f"{BASE_URL}/api/admin/melhor-envio/credentials",
                              json=payload, timeout=15)
        assert r.status_code == 200, r.text

        g = admin_session.get(f"{BASE_URL}/api/admin/melhor-envio/credentials", timeout=15)
        assert g.status_code == 200
        data = g.json()
        assert data["client_id"] == "12345"
        assert data.get("configured") is True
        # secret NEVER returned in plain text
        assert "client_secret" not in data or data.get("client_secret") in (None, "")
        assert data.get("client_secret_masked") == "••••••"
        # Full body must not contain the plain secret anywhere
        assert "s3cr3t-me-value" not in g.text

    def test_env_switch_clears_session_but_keeps_configured(self, admin_session):
        # save sandbox with all creds
        admin_session.put(f"{BASE_URL}/api/admin/melhor-envio/credentials",
                          json={"environment": "sandbox", "client_id": "cid-sb",
                                "client_secret": "secret-sb",
                                "redirect_uri": "https://brasilminis.com/cb"}, timeout=15)
        # switch env=production WITHOUT sending new creds -> client_id/secret should remain but session cleared
        r = admin_session.put(f"{BASE_URL}/api/admin/melhor-envio/credentials",
                              json={"environment": "production"}, timeout=15)
        assert r.status_code == 200, r.text
        st = admin_session.get(f"{BASE_URL}/api/admin/melhor-envio/status", timeout=15).json()
        assert st["environment"] == "production"
        # Previous OAuth session invalidated (no access_token)
        assert st.get("access_token_masked") in (None,)
        # Re-save prod credentials to test the auth-url scopes
        admin_session.put(f"{BASE_URL}/api/admin/melhor-envio/credentials",
                          json={"environment": "production", "client_id": "cid-prd",
                                "client_secret": "secret-prd",
                                "redirect_uri": "https://brasilminis.com/cb"}, timeout=15)

    def test_auth_url_scopes(self, admin_session):
        admin_session.put(f"{BASE_URL}/api/admin/melhor-envio/credentials",
                          json={"environment": "sandbox", "client_id": "cid-scope",
                                "client_secret": "secret-scope",
                                "redirect_uri": "https://brasilminis.com/cb"}, timeout=15)
        r = admin_session.get(f"{BASE_URL}/api/admin/melhor-envio/auth-url", timeout=15)
        assert r.status_code == 200, r.text
        url = r.json().get("authorization_url", "")
        assert "shipping-calculate" in url
        assert "cart-write" in url
        assert "cart-read" in url
        assert "shipping-checkout" in url
        assert "shipping-generate" in url
        assert "shipping-print" in url
        assert "shipping-cancel" not in url
        assert "shipping-tracking" not in url


# ---------- Mercado Pago ----------
class TestMercadoPago:
    def test_save_test_env_enables_and_masks(self, admin_session):
        payload = {"environment": "test",
                   "public_key": "TEST-abcdefgh-pubkey",
                   "access_token": "TEST-plain-access-token-xyz",
                   "is_enabled": True}
        r = admin_session.put(f"{BASE_URL}/api/admin/mercado-pago/settings",
                              json=payload, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["environment"] == "test"
        assert data["status"] == "configured"
        assert data["is_enabled"] is True
        # access token must never be returned in plain
        assert "access_token" not in data or not str(data.get("access_token", ""))
        assert data.get("access_token_masked") == "••••••••••"
        # Full body must not leak plain token
        assert "TEST-plain-access-token-xyz" not in r.text

        # GET status must NOT leak the plain token either
        st = admin_session.get(f"{BASE_URL}/api/admin/mercado-pago/status", timeout=15)
        assert st.status_code == 200
        assert "TEST-plain-access-token-xyz" not in st.text
        assert st.json().get("access_token_masked") == "••••••••••"

    def test_public_key_503_when_not_configured(self, admin_session):
        # ensure disconnected first (autouse fixture)
        r = requests.get(f"{BASE_URL}/api/mercado-pago/public-key", timeout=15)
        assert r.status_code == 503

    def test_public_key_when_configured(self, admin_session):
        admin_session.put(f"{BASE_URL}/api/admin/mercado-pago/settings",
                          json={"environment": "test",
                                "public_key": "TEST-pk-forpublic",
                                "access_token": "TEST-at-forpublic",
                                "is_enabled": True}, timeout=15)
        r = requests.get(f"{BASE_URL}/api/mercado-pago/public-key", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["public_key"] == "TEST-pk-forpublic"
        assert d["environment"] == "test"
        assert d["enabled"] is True

    def test_production_gating(self, admin_session):
        # save production creds -> is_enabled should be False (no auto-activate)
        r = admin_session.put(f"{BASE_URL}/api/admin/mercado-pago/settings",
                              json={"environment": "production",
                                    "public_key": "APP_USR-prod-pk",
                                    "access_token": "APP_USR-prod-at",
                                    "is_enabled": True}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["environment"] == "production"
        assert data["is_enabled"] is False, "produção não pode ativar sozinha"
        # activate without test-connection -> 400
        act = admin_session.post(f"{BASE_URL}/api/admin/mercado-pago/activate",
                                 json={"confirm": True}, timeout=15)
        assert act.status_code == 400
        # Portuguese message
        msg = (act.json().get("detail") or "").lower()
        assert any(word in msg for word in ["teste", "conex", "ativ"])

    def test_env_switch_clears_creds(self, admin_session):
        # Start in test with creds
        admin_session.put(f"{BASE_URL}/api/admin/mercado-pago/settings",
                          json={"environment": "test",
                                "public_key": "TEST-clr-pk",
                                "access_token": "TEST-clr-at",
                                "is_enabled": True}, timeout=15)
        # Switch to production WITHOUT sending new creds -> should clear
        r = admin_session.put(f"{BASE_URL}/api/admin/mercado-pago/settings",
                              json={"environment": "production"}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["environment"] == "production"
        assert d["is_enabled"] is False
        assert d.get("public_key") in (None, "")
        assert d.get("access_token_masked") in (None,)
        assert d["status"] == "not_configured"


# ---------- Simulated checkout when MP not configured ----------
class TestSimulatedCheckout:
    def test_create_order_simulated(self, admin_session, customer_session):
        # ensure MP disconnected (autouse handles it)
        # Need a product id and stock. Try to list products.
        prods = requests.get(f"{BASE_URL}/api/products", timeout=15)
        if prods.status_code != 200 or not prods.json():
            pytest.skip("Sem produtos disponíveis para teste de checkout.")
        pjson = prods.json()
        products = pjson.get("items") if isinstance(pjson, dict) else pjson
        # filter to products with stock > 0
        products = [p for p in (products or []) if (p.get("stock") or 0) > 0]
        if not products:
            pytest.skip("Sem produtos disponíveis com estoque para teste de checkout.")
        pid = products[0].get("id")
        price = products[0].get("price", 100)
        assert pid, "produto sem id"

        cs, email = customer_session
        payload = {
            "items": [{"product_id": pid, "quantity": 1}],
            "payment_method": "pix",
            "shipping_method": "standard",
            "address": {
                "label": "Casa",
                "recipient": "TEST Cliente",
                "street": "Av Paulista",
                "number": "1000",
                "district": "Bela Vista",
                "city": "São Paulo",
                "state": "SP",
                "zip": "01310100",
            },
        }
        r = cs.post(f"{BASE_URL}/api/orders", json=payload, timeout=30)
        assert r.status_code in (200, 201), f"order create falhou: {r.status_code} {r.text[:400]}"
        data = r.json()
        # payment block should indicate simulated
        payment = data.get("payment") or {}
        # accept either requires_payment=false or payment_status hint
        rp = payment.get("requires_payment")
        assert rp is False or rp is None, f"esperado requires_payment=false em modo simulado, obtido {payment}"
        # order should appear in account/orders
        o = cs.get(f"{BASE_URL}/api/orders", timeout=15)
        assert o.status_code == 200
        result = o.json()
        # accept dict or list response
        assert isinstance(result, (list, dict))
