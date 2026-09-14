"""SuperFrete — Etapa B: operação logística nos pedidos."""
import os, uuid, random, requests, pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
A = ("admin@brasilminis.com", "Admin@2025")

from app.services import superfrete_service as sf  # noqa: E402 (funções puras)


def _gen_cpf():
    while True:
        b = [random.randint(0, 9) for _ in range(9)]
        d1 = sum(b[i] * (10 - i) for i in range(9)) * 10 % 11 % 10
        d2 = (sum(b[i] * (11 - i) for i in range(9)) + d1 * 2) * 10 % 11 % 10
        c = "".join(map(str, b + [d1, d2]))
        if c != c[0] * 11:
            return c


@pytest.fixture(scope="module")
def adm():
    s = requests.Session()
    assert s.post(f"{BASE}/api/auth/login", json={"email": A[0], "password": A[1]}, timeout=30).status_code == 200
    # habilita SuperFrete (token fake) + remetente; desabilita no teardown
    s.put(f"{BASE}/api/admin/superfrete/config", json={
        "environment": "sandbox", "token": "tok_B_TEST_1234", "sender_postal_code": "01153000",
        "sender_email": "x@y.com", "is_enabled": True, "enabled_services": ["1", "2"],
        "default_weight": 0.3, "default_width": 11, "default_height": 2, "default_length": 16,
    }, timeout=30)
    yield s
    s.post(f"{BASE}/api/admin/superfrete/disconnect", timeout=30)


def _make_order(adm, approved: bool):
    pr = adm.post(f"{BASE}/api/admin/products", json={
        "name": f"SFB {uuid.uuid4().hex[:6]}", "price": 80.0, "stock": 10,
        "weight_kg": 0.4, "width_cm": 12, "height_cm": 4, "length_cm": 18,
        "images": [], "badges": [], "specs": {},
    }, timeout=30).json()
    cs = requests.Session()
    cs.post(f"{BASE}/api/auth/register", json={"name": "CliB", "email": f"TEST_b_{uuid.uuid4().hex[:8]}@e.com", "password": "senha123", "cpf": _gen_cpf()}, timeout=30)
    o = cs.post(f"{BASE}/api/orders", json={"items": [{"product_id": pr["id"], "quantity": 1}], "shipping_method": "standard", "payment_method": "pix"}, timeout=30).json()
    oid = o["id"]
    if approved:
        from app.db.session import SessionLocal
        from app.models import Order
        db = SessionLocal()
        ordr = db.get(Order, oid)
        ordr.payment_status = "approved"
        ordr.shipping_provider = "superfrete"
        ordr.shipping_service_id = 2
        ordr.shipping_service_name = "SEDEX"
        ordr.shipping_company_name = "Correios"
        ordr.shipping_price_customer = 31.40
        ordr.shipping_price_quoted = 28.00
        ordr.shipping_delivery_max = 4
        ordr.shipping_destination_postal_code = "20040002"
        ordr.shipping_quote_snapshot = {"package": {"weight": 0.4, "height": 4, "width": 12, "length": 18}, "items": [{"product_id": pr["id"], "quantity": 1}]}
        ordr.recipient_snapshot = {"postal_code": "20040002", "street": "Rua X", "number": "1"}
        db.commit(); db.close()
    return cs, oid


class TestStatusMapper:
    def test_known_and_unknown(self):
        assert sf.map_status("delivered") == "DELIVERED"
        assert sf.map_status("posted") == "POSTED"
        assert sf.map_status("QUALQUER_COISA_ESTRANHA") == "PENDING_LABEL"
        assert sf.map_status(None) == "PENDING_LABEL"


class TestLogistics:
    def test_pending_payment_blocks_creation(self, adm):
        _, oid = _make_order(adm, approved=False)
        r = adm.post(f"{BASE}/api/admin/orders/{oid}/logistics/create", timeout=30)
        assert r.status_code == 400
        assert "aprovado" in r.json()["detail"].lower()

    def test_rbac_forbidden(self, adm):
        _, oid = _make_order(adm, approved=True)
        cs = requests.Session()
        cs.post(f"{BASE}/api/auth/register", json={"name": "NA", "email": f"TEST_na_{uuid.uuid4().hex[:8]}@e.com", "password": "senha123", "cpf": _gen_cpf()}, timeout=30)
        assert cs.post(f"{BASE}/api/admin/orders/{oid}/logistics/create", timeout=30).status_code == 403

    def test_create_idempotent_and_flow(self, adm):
        _, oid = _make_order(adm, approved=True)
        r1 = adm.post(f"{BASE}/api/admin/orders/{oid}/logistics/create", timeout=30)
        assert r1.status_code == 200, r1.text
        assert r1.json()["shipment"]["shipment_status"] == "PENDING_LABEL"
        r2 = adm.post(f"{BASE}/api/admin/orders/{oid}/logistics/create", timeout=30)
        assert r2.json().get("already_exists") is True  # idempotente
        # sync sem external_id -> ok com nota
        rs = adm.post(f"{BASE}/api/admin/orders/{oid}/logistics/sync", timeout=30)
        assert rs.status_code == 200
        # tracking manual -> POSTED, auditado
        rt = adm.post(f"{BASE}/api/admin/orders/{oid}/logistics/tracking", json={"tracking_code": "BR123456789BR"}, timeout=30)
        assert rt.status_code == 200 and rt.json()["shipment"]["shipment_status"] == "POSTED"
        assert rt.json()["shipment"]["tracking_code"] == "BR123456789BR"
        # token nunca aparece
        assert "tok_B_TEST" not in str(rt.json())
        # logistics GET reflete
        g = adm.get(f"{BASE}/api/admin/orders/{oid}/logistics", timeout=30).json()
        assert g["shipment"]["shipment_status"] == "POSTED" and g["can_create"] is False
        assert "superfrete.com" in g["panel_url"]

    def test_tracking_requires_code(self, adm):
        _, oid = _make_order(adm, approved=True)
        adm.post(f"{BASE}/api/admin/orders/{oid}/logistics/create", timeout=30)
        assert adm.post(f"{BASE}/api/admin/orders/{oid}/logistics/tracking", json={"tracking_code": ""}, timeout=30).status_code == 400
