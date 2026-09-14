"""SuperFrete — Etapa A: config segura, RBAC, máscara de token, teste de conexão."""
import os, requests, pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
A = ("admin@brasilminis.com", "Admin@2025")


@pytest.fixture(scope="module")
def adm():
    s = requests.Session()
    assert s.post(f"{BASE}/api/auth/login", json={"email": A[0], "password": A[1]}, timeout=30).status_code == 200
    return s


class TestConfig:
    def test_rbac_forbidden(self):
        assert requests.get(f"{BASE}/api/admin/superfrete/config", timeout=30).status_code == 401

    def test_public_status(self):
        d = requests.get(f"{BASE}/api/superfrete/status", timeout=30).json()
        assert d["provider"] == "superfrete" and "is_enabled" in d

    def test_save_masks_token(self, adm):
        r = adm.put(f"{BASE}/api/admin/superfrete/config", json={
            "environment": "sandbox", "token": "tok_SECRET_ABCDEF1234",
            "sender_postal_code": "01153000", "sender_email": "x@y.com",
            "enabled_services": ["1", "2", "17"], "is_enabled": False,
        }, timeout=30)
        assert r.status_code == 200
        c = adm.get(f"{BASE}/api/admin/superfrete/config", timeout=30).json()
        assert c["has_token"] is True
        assert "token" not in c                      # token pleno nunca retorna
        assert "SECRET" not in str(c)                # nada do token em claro
        assert c["token_masked"].endswith("1234") and "••" in c["token_masked"]

    def test_invalid_environment(self, adm):
        assert adm.put(f"{BASE}/api/admin/superfrete/config", json={"environment": "prod"}, timeout=30).status_code == 400

    def test_connection_graceful_with_bad_token(self, adm):
        r = adm.post(f"{BASE}/api/admin/superfrete/test", timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] in ("error", "unavailable", "connected")
        assert "SECRET" not in str(r.json())         # nunca vaza token

    def test_disconnect(self, adm):
        assert adm.post(f"{BASE}/api/admin/superfrete/disconnect", timeout=30).status_code == 200
        assert requests.get(f"{BASE}/api/superfrete/status", timeout=30).json()["is_enabled"] is False
