"""SuperFrete — Etapa C: job de sincronização, eventos idempotentes, transições.

Testes in-process (SessionLocal) com o client HTTP mockado (monkeypatch).
NÃO usa internet. NÃO toca Melhor Envio. NÃO faz deploy.
"""
import os
import uuid

import pytest
import requests
from sqlalchemy import text

from app.db.session import SessionLocal
from app.core.crypto import encrypt
from app.models import (
    Order,
    SuperfreteEvent,
    SuperfreteSettings,
    SuperfreteShipment,
    User,
)
from app.services import superfrete_client as client
from app.services import superfrete_sync_service as sync

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


# ------------------ helpers ------------------
def _enable_superfrete(db, *, suspended=False, sync_enabled=True):
    s = db.get(SuperfreteSettings, 1)
    if s is None:
        s = SuperfreteSettings(id=1)
        db.add(s)
    s.environment = "sandbox"
    s.token_enc = encrypt("tok_C_TEST_1234")
    s.is_enabled = True
    s.status = "connected"
    s.sync_enabled = sync_enabled
    s.sync_suspended = suspended
    s.sync_suspended_reason = None
    s.sender_postal_code = "01153000"
    s.sender_email = "x@y.com"
    db.commit()


def _mk_user(db):
    u = User(id=str(uuid.uuid4()), name="SyncTest", email=f"sync_{uuid.uuid4().hex[:8]}@e.com",
             password_hash="x", role="customer")
    db.add(u)
    db.commit()
    return u.id


def _mk_shipment(db, *, status="POSTED", external_id="ext-123", next_sync_at="2000-01-01T00:00:00+00:00",
                 sync_enabled=True):
    uid = _mk_user(db)
    oid = str(uuid.uuid4())
    db.add(Order(id=oid, user_id=uid, shipping_provider="superfrete"))
    db.commit()
    sh = SuperfreteShipment(
        id=str(uuid.uuid4()), order_id=oid, external_id=external_id,
        service_code="2", service_name="SEDEX", shipment_status=status,
        sync_enabled=sync_enabled, next_sync_at=next_sync_at, sync_attempts=0,
    )
    db.add(sh)
    db.commit()
    return sh.id, oid


class _Resp:
    def __init__(self, status=None, tracking=None, updated_at=None):
        self.payload = {"status": status, "tracking": tracking, "updated_at": updated_at}


def _mock_request(monkeypatch, *, payload=None, exc=None):
    def fake(environment, token, method, path, user_agent=None, **kw):
        if exc is not None:
            raise exc
        return payload or {}
    monkeypatch.setattr(client, "request", fake)


# ------------------ funções puras ------------------
class TestPure:
    def test_normalize_unknown_returns_none(self):
        assert sync.normalize_status("delivered") == "DELIVERED"
        assert sync.normalize_status("posted") == "POSTED"
        assert sync.normalize_status("XPTO_DESCONHECIDO") is None
        assert sync.normalize_status(None) is None

    def test_no_regression(self):
        assert sync.can_transition("IN_TRANSIT", "OUT_FOR_DELIVERY") is True
        assert sync.can_transition("DELIVERED", "IN_TRANSIT") is False  # não regride
        assert sync.can_transition("OUT_FOR_DELIVERY", "POSTED") is False
        assert sync.can_transition("POSTED", "POSTED") is False  # sem mudança
        assert sync.can_transition("DELIVERED", "RETURNED") is True  # exceção permitida

    def test_next_sync_terminal_and_backoff(self):
        assert sync.compute_next_sync_at("DELIVERED") is None
        assert sync.compute_next_sync_at("CANCELED") is None
        n1 = sync.compute_next_sync_at("ERROR", attempts=1, temporary_error=True)
        n2 = sync.compute_next_sync_at("ERROR", attempts=3, temporary_error=True)
        assert n1 is not None and n2 is not None and n2 > n1  # backoff cresce
        # Retry-After respeitado
        ra = sync.compute_next_sync_at("POSTED", attempts=1, temporary_error=True, retry_after=30)
        assert ra is not None


# ------------------ ciclo / elegibilidade ------------------
class TestCycle:
    def test_only_eligible_and_terminal_ignored(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid_active, _ = _mk_shipment(db, status="POSTED")
            sid_term, _ = _mk_shipment(db, status="DELIVERED")
            sid_noext, _ = _mk_shipment(db, status="POSTED", external_id=None)
            ids = sync._eligible_ids(db, 50)
            assert sid_active in ids
            assert sid_term not in ids       # terminal ignorado
            assert sid_noext not in ids       # sem external_id ignorado
        finally:
            db.close()

    def test_full_cycle_advance(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, oid = _mk_shipment(db, status="POSTED")
        finally:
            db.close()
        _mock_request(monkeypatch, payload={"status": "in_transit", "updated_at": "2026-06-14T10:00:00+00:00"})
        res = sync.run_sync_cycle(trigger="manual")
        assert res["status"] == "ok"
        assert res["updated"] >= 1
        db = SessionLocal()
        try:
            sh = db.get(SuperfreteShipment, sid)
            assert sh.shipment_status == "IN_TRANSIT"
            assert sh.locked_at is None       # lock liberado
            evs = db.query(SuperfreteEvent).filter(SuperfreteEvent.shipment_id == sid).all()
            assert any(e.normalized_status == "IN_TRANSIT" and e.source == "POLL" for e in evs)
        finally:
            db.close()

    def test_no_change_counts_unchanged(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, _ = _mk_shipment(db, status="IN_TRANSIT")
        finally:
            db.close()
        _mock_request(monkeypatch, payload={"status": "in_transit"})
        r = sync.sync_one(sid, worker="t")
        assert r == "unchanged"

    def test_unknown_preserves_state(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, _ = _mk_shipment(db, status="POSTED")
        finally:
            db.close()
        _mock_request(monkeypatch, payload={"status": "algo_muito_estranho"})
        r = sync.sync_one(sid, worker="t")
        db = SessionLocal()
        try:
            sh = db.get(SuperfreteShipment, sid)
            assert sh.shipment_status == "POSTED"  # preserva
        finally:
            db.close()

    def test_delivered_not_back_to_transit(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            # força DELIVERED já elegível para simular resposta atrasada
            sid, _ = _mk_shipment(db, status="DELIVERED")
        finally:
            db.close()
        _mock_request(monkeypatch, payload={"status": "in_transit"})
        # DELIVERED é terminal -> não elegível pelo job; e sync_one direto não deve regredir
        sync.sync_one(sid, worker="t")
        db = SessionLocal()
        try:
            sh = db.get(SuperfreteShipment, sid)
            assert sh.shipment_status == "DELIVERED"
        finally:
            db.close()

    def test_event_dedup(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, _ = _mk_shipment(db, status="IN_TRANSIT")
            sh = db.get(SuperfreteShipment, sid)
            a = sync.record_event(db, sh, source="POLL", raw_status="delivered",
                                  normalized_status="DELIVERED", provider_event_at="2026-06-14T10:00:00+00:00")
            db.commit()
            b = sync.record_event(db, sh, source="POLL", raw_status="delivered",
                                  normalized_status="DELIVERED", provider_event_at="2026-06-14T10:00:00+00:00")
            db.commit()
            assert a is True and b is False  # segundo é idempotente
            n = db.query(SuperfreteEvent).filter(SuperfreteEvent.shipment_id == sid,
                                                 SuperfreteEvent.raw_status == "delivered").count()
            assert n == 1
        finally:
            db.close()


# ------------------ falhas / auth ------------------
class TestFailures:
    def test_temporary_error_backoff(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, _ = _mk_shipment(db, status="POSTED")
        finally:
            db.close()
        _mock_request(monkeypatch, exc=client.SuperfreteUnavailable("timeout"))
        r = sync.sync_one(sid, worker="t")
        assert r == "failed"
        db = SessionLocal()
        try:
            sh = db.get(SuperfreteShipment, sid)
            assert sh.sync_attempts == 1
            assert sh.next_sync_at is not None
            assert sh.shipment_status == "POSTED"  # erro temporário não vira ERROR
            assert sh.locked_at is None
        finally:
            db.close()

    def test_auth_error_suspends_globally(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, _ = _mk_shipment(db, status="POSTED")
        finally:
            db.close()
        _mock_request(monkeypatch, exc=client.SuperfreteAuthError(401, "token inválido"))
        r = sync.sync_one(sid, worker="t")
        assert r == "failed"
        db = SessionLocal()
        try:
            s = db.get(SuperfreteSettings, 1)
            assert s.sync_suspended is True
            # ciclo agora pula por suspensão global
            res = sync.run_sync_cycle(trigger="manual")
            assert res["status"] == "skipped_locked"
        finally:
            db.close()

    def test_token_replace_and_success_reenables(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db, suspended=True)
            assert db.get(SuperfreteSettings, 1).sync_suspended is True
        finally:
            db.close()
        # troca+teste bem-sucedido do token via serviço -> reativa
        from app.services import superfrete_service as svc
        _mock_request(monkeypatch, payload={"id": 1})  # /user ok
        db = SessionLocal()
        try:
            svc.test_connection(db, {"id": "a", "email": "admin@x"})
            s = db.get(SuperfreteSettings, 1)
            assert s.sync_suspended is False
            assert s.status == "connected"
        finally:
            db.close()

    def test_token_never_leaks(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, oid = _mk_shipment(db, status="POSTED")
        finally:
            db.close()
        _mock_request(monkeypatch, payload={"status": "posted"})
        sync.sync_one(sid, worker="t")
        db = SessionLocal()
        try:
            st = sync.get_sync_status(db)
            assert "tok_C_TEST" not in str(st)
            tl = sync.timeline(db, sid)
            assert "tok_C_TEST" not in str(tl)
        finally:
            db.close()


# ------------------ concorrência / reconciliação ------------------
class TestConcurrencyReconcile:
    def test_concurrent_cycle_skips(self, monkeypatch):
        from app.db.session import engine
        conn = engine.connect()
        try:
            got = conn.execute(text("SELECT pg_try_advisory_lock(:k)"),
                               {"k": sync._ADVISORY_LOCK_KEY}).scalar()
            assert got is True
            res = sync.run_sync_cycle(trigger="manual")  # outro "worker" segurando o lock
            assert res["status"] == "skipped_locked"
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": sync._ADVISORY_LOCK_KEY})
            conn.close()

    def test_expired_lock_recovered(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, _ = _mk_shipment(db, status="POSTED")
            sh = db.get(SuperfreteShipment, sid)
            sh.locked_at = "2000-01-01T00:00:00+00:00"  # lock antigo/expirado
            sh.locked_by = "morto"
            db.commit()
            ids = sync._eligible_ids(db, 50)
            assert sid in ids  # lock expirado é recuperável
        finally:
            db.close()

    def test_reconcile_never_creates_shipment(self, monkeypatch):
        db = SessionLocal()
        try:
            before = db.query(SuperfreteShipment).count()
        finally:
            db.close()
        sync.reconcile()
        db = SessionLocal()
        try:
            after = db.query(SuperfreteShipment).count()
            assert after == before  # nunca cria envio
        finally:
            db.close()

    def test_reprocess_failures_resets_error(self, monkeypatch):
        db = SessionLocal()
        try:
            _enable_superfrete(db)
            sid, _ = _mk_shipment(db, status="ERROR")
        finally:
            db.close()
        sync.reprocess_failures()
        db = SessionLocal()
        try:
            sh = db.get(SuperfreteShipment, sid)
            assert sh.shipment_status == "PENDING_LABEL"
            assert sh.last_error is None
        finally:
            db.close()


# ------------------ RBAC (HTTP) ------------------
class TestRBAC:
    def test_manual_run_requires_admin(self):
        cs = requests.Session()
        import random
        def cpf():
            while True:
                b = [random.randint(0, 9) for _ in range(9)]
                d1 = sum(b[i] * (10 - i) for i in range(9)) * 10 % 11 % 10
                d2 = (sum(b[i] * (11 - i) for i in range(9)) + d1 * 2) * 10 % 11 % 10
                c = "".join(map(str, b + [d1, d2]))
                if c != c[0] * 11:
                    return c
        cs.post(f"{BASE}/api/auth/register", json={"name": "NA", "email": f"TEST_sc_{uuid.uuid4().hex[:8]}@e.com",
                                                    "password": "senha123", "cpf": cpf()}, timeout=30)
        assert cs.post(f"{BASE}/api/admin/superfrete/sync/run", timeout=30).status_code == 403
        assert cs.get(f"{BASE}/api/admin/superfrete/sync/status", timeout=30).status_code in (401, 403)

    def test_admin_sync_status_ok(self):
        s = requests.Session()
        assert s.post(f"{BASE}/api/auth/login", json={"email": "admin@brasilminis.com",
                                                      "password": "Admin@2025"}, timeout=30).status_code == 200
        r = s.get(f"{BASE}/api/admin/superfrete/sync/status", timeout=30)
        assert r.status_code == 200
        assert "scheduler_running" in r.json()
        assert "tok_" not in r.text
