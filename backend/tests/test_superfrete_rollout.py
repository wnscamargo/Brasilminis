"""SuperFrete — Etapa D: rollout de produção controlada e teste ponta a ponta.

In-process (SessionLocal) + client HTTP mockado. Nenhuma chamada real. RBAC via HTTP.
NÃO altera pedidos reais. NÃO faz deploy.
"""
import os
import uuid

import requests

from app.db.session import SessionLocal
from app.core.crypto import encrypt
from app.models import Order, SuperfreteSettings, SuperfreteShipment, User
from app.services import superfrete_client as client
from app.services import superfrete_service as sf
from app.services import superfrete_controlled_test_service as ctest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _settings(db, *, mode="ENABLED", pct=0, enabled=True, token="tok_D_TEST_1234"):
    s = db.get(SuperfreteSettings, 1) or SuperfreteSettings(id=1)
    if s.id != 1:
        db.add(s)
    s.environment = "sandbox"
    s.token_enc = encrypt(token) if token else None
    s.is_enabled = enabled
    s.status = "connected"
    s.sync_enabled = True
    s.sync_suspended = False
    s.sender_postal_code = "01153000"
    s.sender_email = "x@y.com"
    s.rollout_mode = mode
    s.rollout_percentage = pct
    s.controlled_test_state = None
    s.test_order_id = None
    db.commit()
    return s


def _mock(monkeypatch, *, payload=None, exc=None):
    def fake(environment, token, method, path, user_agent=None, **kw):
        if exc is not None:
            raise exc
        return payload if payload is not None else {}
    monkeypatch.setattr(client, "request", fake)


class TestEligibility:
    def test_disabled_uses_melhor_envio(self):
        db = SessionLocal()
        try:
            _settings(db, mode="DISABLED")
            assert sf.is_public_eligible(db, "u1", is_admin=False) is False
            assert sf.is_public_eligible(db, "u1", is_admin=True) is False
        finally:
            db.close()

    def test_test_order_only_blocks_public(self):
        db = SessionLocal()
        try:
            _settings(db, mode="TEST_ORDER_ONLY")
            assert sf.is_public_eligible(db, "u1", is_admin=False) is False
            assert sf.is_public_eligible(db, "u1", is_admin=True) is False
        finally:
            db.close()

    def test_admin_only(self):
        db = SessionLocal()
        try:
            _settings(db, mode="ADMIN_ONLY")
            assert sf.is_public_eligible(db, "u1", is_admin=False) is False
            assert sf.is_public_eligible(db, "u1", is_admin=True) is True
        finally:
            db.close()

    def test_enabled_all(self):
        db = SessionLocal()
        try:
            _settings(db, mode="ENABLED")
            assert sf.is_public_eligible(db, "u1", is_admin=False) is True
            assert sf.is_public_eligible(db, None, is_admin=False) is True
        finally:
            db.close()

    def test_percentage_deterministic(self):
        db = SessionLocal()
        try:
            _settings(db, mode="PERCENTAGE", pct=0)
            uid = "user-xyz"
            b = sf._bucket(uid)
            assert sf.is_public_eligible(db, uid, is_admin=False) is False  # pct 0 => ninguém
            _settings(db, mode="PERCENTAGE", pct=100)
            assert sf.is_public_eligible(db, uid, is_admin=False) is True   # pct 100 => todos
            # determinístico: mesmo user, borda exata
            _settings(db, mode="PERCENTAGE", pct=b + 1)
            r1 = sf.is_public_eligible(db, uid, is_admin=False)
            r2 = sf.is_public_eligible(db, uid, is_admin=False)
            assert r1 is True and r1 == r2
            # visitante sem login volta ao ME mesmo em 100%
            _settings(db, mode="PERCENTAGE", pct=100)
            assert sf.is_public_eligible(db, None, is_admin=False) is False
        finally:
            db.close()

    def test_disabled_when_no_token(self):
        db = SessionLocal()
        try:
            _settings(db, mode="ENABLED", token=None, enabled=True)
            assert sf.is_public_eligible(db, "u1", is_admin=True) is False
        finally:
            db.close()


class TestRolloutHistory:
    def test_mode_change_does_not_touch_existing(self):
        db = SessionLocal()
        try:
            _settings(db, mode="ENABLED")
            uid = str(uuid.uuid4())
            db.add(User(id=uid, name="X", email=f"h_{uuid.uuid4().hex[:6]}@e.com", password_hash="x", role="customer"))
            oid = str(uuid.uuid4())
            db.add(Order(id=oid, user_id=uid, shipping_provider="melhor_envio"))
            db.commit()
            sh = SuperfreteShipment(id=str(uuid.uuid4()), order_id=oid, external_id="ext-hist",
                                    shipment_status="POSTED", service_name="SEDEX")
            db.add(sh); db.commit()
            # troca de rollout
            _settings(db, mode="DISABLED")
            o2 = db.get(Order, oid)
            sh2 = db.get(SuperfreteShipment, sh.id)
            assert o2.shipping_provider == "melhor_envio"      # provider não muda retroativamente
            assert sh2.shipment_status == "POSTED"             # histórico intacto
        finally:
            db.close()


class TestControlledTest:
    def _run(self, monkeypatch, mode="TEST_ORDER_ONLY"):
        db = SessionLocal()
        try:
            _settings(db, mode=mode)
        finally:
            db.close()
        admin = {"id": "admin-ct", "email": "admin@ct"}
        db = SessionLocal()
        try:
            ctest.set_params(db, {"origin_postal_code": "01153000", "dest_postal_code": "20040002",
                                  "weight": 0.3, "width": 11, "height": 2, "length": 16,
                                  "insurance_value": 50, "product_name": "Miniatura Teste"}, admin)
        finally:
            db.close()
        # conexão
        _mock(monkeypatch, payload={"id": 1})
        db = SessionLocal()
        try:
            ctest.run_connection(db, admin)
        finally:
            db.close()
        # cotação
        _mock(monkeypatch, payload=[{"id": 2, "name": "SEDEX", "price": 31.4, "company": {"name": "Correios", "id": 1},
                                     "delivery_max": 4}])
        db = SessionLocal()
        try:
            st = ctest.run_quote(db, admin)
            assert st["checklist"]["quote_returned"] is True
            ctest.select_service(db, "2", admin)
        finally:
            db.close()
        # criar envio (idempotente)
        db = SessionLocal()
        try:
            st = ctest.create_shipment(db, admin)
        finally:
            db.close()
        return admin, st

    def test_controlled_test_flow_and_idempotency(self, monkeypatch):
        admin, st = self._run(monkeypatch)
        assert st["checklist"]["shipment_created"] is True
        assert st["checklist"]["idempotency_validated"] is True   # recriar não duplicou
        assert st["checklist"]["service_selected"] is True
        toid = st["test_order_id"]
        db = SessionLocal()
        try:
            # exatamente 1 shipment para o pedido de teste
            n = db.query(SuperfreteShipment).filter(SuperfreteShipment.order_id == toid).count()
            assert n == 1
            o = db.get(Order, toid)
            assert o.is_test_order is True                        # inequivocamente teste
        finally:
            db.close()
        # tracking + sync + finalize
        db = SessionLocal()
        try:
            ctest.capture_tracking(db, "BR123456789BR", None, admin)
            ctest.run_sync(db, admin)
            final = ctest.finalize(db, admin)
            assert final["checklist"]["tracking_received"] is True
            assert final["checklist"]["polling_synced"] is True
            assert final["checklist"]["melhor_envio_intact"] is True
            assert final["status"] in ("APPROVED", "PARTIAL")
            assert "tok_D_TEST" not in str(final)                 # token nunca vaza
        finally:
            db.close()

    def test_controlled_test_works_in_test_order_only(self, monkeypatch):
        # mesmo com rollout TEST_ORDER_ONLY (público bloqueado), o teste do admin cria o envio
        _, st = self._run(monkeypatch, mode="TEST_ORDER_ONLY")
        assert st["checklist"]["shipment_created"] is True

    def test_rerun_creates_no_duplicate_order(self, monkeypatch):
        admin, st = self._run(monkeypatch)
        toid1 = st["test_order_id"]
        # rodar create de novo reaproveita o mesmo pedido de teste
        db = SessionLocal()
        try:
            st2 = ctest.create_shipment(db, admin)
            assert st2["test_order_id"] == toid1
            n_orders = db.query(Order).filter(Order.is_test_order.is_(True),
                                              Order.id == toid1).count()
            assert n_orders == 1
        finally:
            db.close()


class TestRBAC:
    def test_controlled_test_admin_only(self):
        import random
        def cpf():
            while True:
                b = [random.randint(0, 9) for _ in range(9)]
                d1 = sum(b[i] * (10 - i) for i in range(9)) * 10 % 11 % 10
                d2 = (sum(b[i] * (11 - i) for i in range(9)) + d1 * 2) * 10 % 11 % 10
                c = "".join(map(str, b + [d1, d2]))
                if c != c[0] * 11:
                    return c
        cs = requests.Session()
        cs.post(f"{BASE}/api/auth/register", json={"name": "NA", "email": f"TEST_rd_{uuid.uuid4().hex[:8]}@e.com",
                                                    "password": "senha123", "cpf": cpf()}, timeout=30)
        assert cs.get(f"{BASE}/api/admin/superfrete/controlled-test", timeout=30).status_code in (401, 403)
        assert cs.post(f"{BASE}/api/admin/superfrete/controlled-test/connection", timeout=30).status_code == 403

    def test_admin_can_read_controlled_test(self):
        s = requests.Session()
        assert s.post(f"{BASE}/api/auth/login", json={"email": "admin@brasilminis.com",
                                                      "password": "Admin@2025"}, timeout=30).status_code == 200
        r = s.get(f"{BASE}/api/admin/superfrete/controlled-test", timeout=30)
        assert r.status_code == 200 and "checklist" in r.json()
        assert "tok_" not in r.text
