"""Backend tests for CPF: register, profile, admin, legacy support, PII."""
import os
import time
import uuid
import requests
from .test_helpers import preserve_auth_cookie, valid_cpf
import pytest

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
if not BASE_URL:
    # Fall back to reading frontend .env for BASE URL
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass

ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASS = os.environ["ADMIN_PASSWORD"]

VALID_CPFS = ["39053344705", "52998224725", "11144477735"]
INVALID_CPFS = ["11111111111", "12345678900"]


def _uniq_email(tag="cpf"):
    return f"TEST_{tag}_{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    preserve_auth_cookie(s, r)
    return s


# ---------------- REGISTER ----------------
class TestRegisterCpf:
    def test_register_valid_cpf(self):
        s = requests.Session()
        email = _uniq_email("reg_ok")
        cpf = _gen_cpf()
        r = s.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Reg OK", "email": email, "password": "senha123",
            "cpf": cpf, "newsletter": False,
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("cpf") == cpf, f"CPF should be normalized 11-digit, got {data.get('cpf')!r}"
        assert data.get("email", "").lower() == email.lower()

    def test_register_masked_cpf_accepted(self):
        s = requests.Session()
        cpf = _gen_cpf()
        masked = f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
        r = s.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Reg Mask", "email": _uniq_email("reg_mask"), "password": "senha123",
            "cpf": masked, "newsletter": False,
        })
        assert r.status_code == 200, r.text
        assert r.json().get("cpf") == cpf

    def test_register_invalid_cpf_check_digits(self):
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Bad", "email": _uniq_email("bad"), "password": "senha123",
            "cpf": "12345678900", "newsletter": False,
        })
        assert r.status_code == 400
        detail = r.json().get("detail", "")
        assert "CPF" in detail or "cpf" in detail.lower()
        # PII: mensagem NÃO deve conter o número
        assert "12345678900" not in detail and "123.456.789-00" not in detail

    def test_register_invalid_cpf_all_same(self):
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Bad2", "email": _uniq_email("bad2"), "password": "senha123",
            "cpf": "11111111111", "newsletter": False,
        })
        assert r.status_code == 400
        assert "11111111111" not in r.json().get("detail", "")

    def test_register_missing_cpf_422(self):
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "NoCpf", "email": _uniq_email("nocpf"), "password": "senha123",
            "newsletter": False,
        })
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    def test_register_duplicate_cpf(self):
        cpf = _gen_cpf()
        e1 = _uniq_email("dup1")
        e2 = _uniq_email("dup2")
        r1 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Dup1", "email": e1, "password": "senha123", "cpf": cpf, "newsletter": False,
        })
        assert r1.status_code == 200, r1.text
        masked = f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
        r2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Dup2", "email": e2, "password": "senha123",
            "cpf": masked, "newsletter": False,
        })
        assert r2.status_code == 400
        detail = r2.json().get("detail", "")
        assert "cadastrado" in detail.lower()
        # PII: não expor o CPF
        assert cpf not in detail and masked not in detail


# ---------------- PROFILE (legado adiciona depois) ----------------
class TestProfileCpf:
    def test_profile_update_cpf_valid(self):
        # Register user WITH cpf first (register is required), then update to another valid CPF
        # But we want to test the "legacy adds later" scenario -- register requires CPF, so we test update-to-new-valid.
        s = requests.Session()
        email = _uniq_email("prof_ok")
        # Generate a unique valid cpf (use algorithm)
        cpf1 = _gen_cpf()
        cpf2 = _gen_cpf()
        r = s.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Prof", "email": email, "password": "senha123",
            "cpf": cpf1, "newsletter": False,
        })
        assert r.status_code == 200, r.text
        preserve_auth_cookie(s, r)
        r2 = s.put(f"{BASE_URL}/api/account/profile", json={"cpf": cpf2})
        assert r2.status_code == 200, r2.text
        assert r2.json().get("cpf") == cpf2

    def test_profile_update_cpf_invalid(self):
        s = requests.Session()
        cpf1 = _gen_cpf()
        r = s.post(f"{BASE_URL}/api/auth/register", json={
            "name": "P2", "email": _uniq_email("p2"), "password": "senha123",
            "cpf": cpf1, "newsletter": False,
        })
        assert r.status_code == 200
        preserve_auth_cookie(s, r)
        r2 = s.put(f"{BASE_URL}/api/account/profile", json={"cpf": "12345678900"})
        assert r2.status_code == 400
        assert "12345678900" not in r2.json().get("detail", "")

    def test_profile_update_cpf_duplicate_other_user(self):
        # user A
        sa = requests.Session()
        cpf_a = _gen_cpf()
        ra = sa.post(f"{BASE_URL}/api/auth/register", json={
            "name": "A", "email": _uniq_email("ua"), "password": "senha123",
            "cpf": cpf_a, "newsletter": False,
        })
        assert ra.status_code == 200
        # user B
        sb = requests.Session()
        cpf_b = _gen_cpf()
        rb = sb.post(f"{BASE_URL}/api/auth/register", json={
            "name": "B", "email": _uniq_email("ub"), "password": "senha123",
            "cpf": cpf_b, "newsletter": False,
        })
        assert rb.status_code == 200
        preserve_auth_cookie(sb, rb)
        # B tries to update to A's CPF
        r2 = sb.put(f"{BASE_URL}/api/account/profile", json={"cpf": cpf_a})
        assert r2.status_code == 400
        assert "cadastrado" in r2.json().get("detail", "").lower()

    def test_profile_update_cpf_same_user_ok(self):
        s = requests.Session()
        cpf = _gen_cpf()
        r = s.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Same", "email": _uniq_email("same"), "password": "senha123",
            "cpf": cpf, "newsletter": False,
        })
        assert r.status_code == 200
        preserve_auth_cookie(s, r)
        # Update to same CPF — should not fail (dup filter excludes self)
        r2 = s.put(f"{BASE_URL}/api/account/profile", json={"cpf": cpf})
        assert r2.status_code == 200, r2.text


# ---------------- ADMIN ----------------
class TestAdminCpf:
    def test_admin_list_customers_has_cpf(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/customers")
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list)
        if arr:
            assert "cpf" in arr[0]

    def test_admin_edit_cpf(self, admin_session):
        # Create a customer to edit
        s = requests.Session()
        cpf1 = _gen_cpf()
        rr = s.post(f"{BASE_URL}/api/auth/register", json={
            "name": "AdmEdit", "email": _uniq_email("adm_edit"), "password": "senha123",
            "cpf": cpf1, "newsletter": False,
        })
        assert rr.status_code == 200
        uid = rr.json()["id"]
        cpf2 = _gen_cpf()
        r = admin_session.put(f"{BASE_URL}/api/admin/customers/{uid}", json={"cpf": cpf2})
        assert r.status_code == 200, r.text
        assert r.json().get("cpf") == cpf2

    def test_admin_edit_cpf_invalid(self, admin_session):
        s = requests.Session()
        cpf1 = _gen_cpf()
        rr = s.post(f"{BASE_URL}/api/auth/register", json={
            "name": "AdmInv", "email": _uniq_email("adm_inv"), "password": "senha123",
            "cpf": cpf1, "newsletter": False,
        })
        uid = rr.json()["id"]
        r = admin_session.put(f"{BASE_URL}/api/admin/customers/{uid}", json={"cpf": "11111111111"})
        assert r.status_code == 400

    def test_admin_customers_requires_admin(self):
        r = requests.get(f"{BASE_URL}/api/admin/customers")
        assert r.status_code in (401, 403)

    def test_customer_cannot_admin_edit(self):
        s = requests.Session()
        rr = s.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Cust", "email": _uniq_email("cust_admin"), "password": "senha123",
            "cpf": _gen_cpf(), "newsletter": False,
        })
        uid = rr.json()["id"]
        preserve_auth_cookie(s, rr)
        r = s.put(f"{BASE_URL}/api/admin/customers/{uid}", json={"cpf": _gen_cpf()})
        assert r.status_code in (401, 403)


# ---------------- LEGACY (admin without CPF) ----------------
class TestLegacyNoCpf:
    def test_admin_login_and_me_no_cpf(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        data = r.json()
        # admin is legacy — cpf can be empty/null
        assert data.get("role") == "admin"


# ---------------- CPF generator (for uniqueness) ----------------
def _gen_cpf():
    import random
    while True:
        base = [random.randint(0, 9) for _ in range(9)]
        d1 = sum(base[i] * (10 - i) for i in range(9)) * 10 % 11 % 10
        d2 = (sum(base[i] * (11 - i) for i in range(9)) + d1 * 2) * 10 % 11 % 10
        cpf = "".join(map(str, base + [d1, d2]))
        if cpf != cpf[0] * 11:
            return cpf
