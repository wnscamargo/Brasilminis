"""Tests for institutional site-content, social-links, CEP autofill flow (iteration 9)."""
import os
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
ADMIN_EMAIL = "admin@brasilminis.com"
ADMIN_PASSWORD = "Admin@2025"


def _admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    # Some environments send Partitioned cookies which requests may not persist; force via header.
    tok = None
    for c in r.cookies:
        if c.name == "access_token":
            tok = c.value
            break
    if not tok:
        # Parse from raw Set-Cookie headers
        raw = r.raw.headers.getlist("Set-Cookie") if hasattr(r.raw.headers, "getlist") else r.headers.get("set-cookie", "").split(",")
        for h in raw:
            if "access_token=" in h:
                tok = h.split("access_token=", 1)[1].split(";", 1)[0]
                break
    if tok:
        s.headers.update({"Cookie": f"access_token={tok}"})
    return s


# -------- Public endpoints --------
def test_public_site_content_shape():
    r = requests.get(f"{BASE_URL}/api/site-content", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "pages" in data and "social_links" in data
    assert isinstance(data["pages"], dict)
    assert isinstance(data["social_links"], dict)
    # Only active pages are returned
    for k, v in data["pages"].items():
        assert k in ("about", "contact", "returns", "shipping")
        assert "title" in v and "content" in v


def test_public_site_config_has_social():
    r = requests.get(f"{BASE_URL}/api/site-config", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "social_links" in data
    assert isinstance(data["social_links"], dict)


# -------- RBAC --------
def test_admin_site_content_requires_auth():
    r = requests.get(f"{BASE_URL}/api/admin/site-content", timeout=15)
    assert r.status_code in (401, 403), f"unexpected {r.status_code}"


def test_admin_social_links_requires_auth():
    r = requests.get(f"{BASE_URL}/api/admin/social-links", timeout=15)
    assert r.status_code in (401, 403)
    r2 = requests.put(f"{BASE_URL}/api/admin/social-links", json={"instagram": {"url": "https://x", "active": True}}, timeout=15)
    assert r2.status_code in (401, 403)


def test_admin_login_works():
    s = _admin_session()
    r = s.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 200
    assert r.json().get("email") == ADMIN_EMAIL


# -------- Sanitization --------
def test_content_sanitization_removes_script_and_iframe():
    s = _admin_session()
    payload = {
        "about": {
            "title": "Sobre Nós Teste",
            "content": "Ola <script>alert(1)</script> mundo <iframe src='x'></iframe> **negrito**",
            "active": True,
        }
    }
    r = s.put(f"{BASE_URL}/api/admin/site-content", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    about = body["content"]["about"]
    assert "<script" not in about["content"].lower()
    assert "</script>" not in about["content"].lower()
    assert "<iframe" not in about["content"]
    assert "**negrito**" in about["content"]  # markdown preservado
    # Public GET reflects sanitized content
    pub = requests.get(f"{BASE_URL}/api/site-content", timeout=15).json()
    assert "<script>" not in pub["pages"]["about"]["content"]


def test_social_link_invalid_url_returns_400():
    s = _admin_session()
    r = s.put(f"{BASE_URL}/api/admin/social-links",
              json={"instagram": {"url": "javascript:alert(1)", "active": True}}, timeout=15)
    assert r.status_code == 400
    r2 = s.put(f"{BASE_URL}/api/admin/social-links",
               json={"facebook": {"url": "notaurl.com", "active": True}}, timeout=15)
    assert r2.status_code == 400


# -------- Inactive pages hidden from public --------
def test_inactive_page_hidden_public_visible_admin():
    s = _admin_session()
    # Deactivate returns
    r = s.put(f"{BASE_URL}/api/admin/site-content",
              json={"returns": {"active": False}}, timeout=15)
    assert r.status_code == 200
    pub = requests.get(f"{BASE_URL}/api/site-content", timeout=15).json()
    assert "returns" not in pub["pages"], f"returns should be hidden, got: {list(pub['pages'].keys())}"
    # Admin sees it
    adm = s.get(f"{BASE_URL}/api/admin/site-content", timeout=15).json()
    assert "returns" in adm["content"]
    assert adm["content"]["returns"]["active"] is False
    # Reactivate for regression cleanup
    s.put(f"{BASE_URL}/api/admin/site-content", json={"returns": {"active": True}}, timeout=15)
    pub2 = requests.get(f"{BASE_URL}/api/site-content", timeout=15).json()
    assert "returns" in pub2["pages"]


# -------- Social active/inactive rules --------
def test_social_active_visibility_rules():
    s = _admin_session()
    payload = {
        "instagram": {"url": "https://instagram.com/brasilminis", "active": True},
        "tiktok": {"url": "", "active": True},  # empty url => stored inactive
        "pinterest": {"url": "", "active": False},
    }
    r = s.put(f"{BASE_URL}/api/admin/social-links", json=payload, timeout=15)
    assert r.status_code == 200
    body = r.json()["social_links"]
    assert body["instagram"]["active"] is True
    assert body["tiktok"]["active"] is False  # forced inactive
    # Public payload
    pub = requests.get(f"{BASE_URL}/api/site-content", timeout=15).json()
    assert "instagram" in pub["social_links"]
    assert "tiktok" not in pub["social_links"]
    assert "pinterest" not in pub["social_links"]


# -------- CEP internal service --------
def test_cep_lookup_valid():
    r = requests.get(f"{BASE_URL}/api/cep/01310100", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    # Expect address fields
    assert data.get("state") in ("SP",) or data.get("uf") in ("SP",)
    combined = (data.get("street") or "") + (data.get("logradouro") or "")
    assert "Paulista" in combined


def test_cep_lookup_invalid():
    r = requests.get(f"{BASE_URL}/api/cep/00000000", timeout=20)
    assert r.status_code in (400, 404)
