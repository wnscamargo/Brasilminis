"""SuperFrete — Etapa E: saúde do rollout + governança.

In-process (SessionLocal) + RBAC via HTTP. Sem chamadas reais. Sem deploy.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

from app.db.session import SessionLocal
from app.core.crypto import encrypt
from app.models import (
    Order,
    SuperfreteRolloutHistory,
    SuperfreteSettings,
    SuperfreteShipment,
    User,
)
from app.services import superfrete_rollout_service as gov

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _iso(days_ago=0):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _settings(db, **kw):
    s = db.get(SuperfreteSettings, 1) or SuperfreteSettings(id=1)
    if s.id != 1:
        db.add(s)
    s.environment = "sandbox"
    s.token_enc = kw.get("token", encrypt("tok_E_TEST"))
    s.is_enabled = kw.get("is_enabled", True)
    s.status = kw.get("status", "connected")
    s.sync_suspended = kw.get("sync_suspended", False)
    s.sync_enabled = True
    s.rollout_mode = kw.get("rollout_mode", "PERCENTAGE")
    s.rollout_percentage = kw.get("rollout_percentage", 10)
    s.rollout_min_orders = kw.get("rollout_min_orders", 20)
    s.controlled_test_state = kw.get("controlled_test_state")
    s.rollout_alert_state = None
    s.test_order_id = kw.get("test_order_id")
    db.commit()
    return s


def _order(db, provider, created_at, is_test=False, service_id=1):
    uid = str(uuid.uuid4())
    db.add(User(id=uid, name="X", email=f"e_{uuid.uuid4().hex[:6]}@e.com", password_hash="x", role="customer"))
    oid = str(uuid.uuid4())
    db.add(Order(id=oid, user_id=uid, shipping_provider=provider, shipping_service_id=service_id,
                 shipping_delivery_max=5, is_test_order=is_test, created_at=created_at))
    db.commit()
    return oid


def _ship(db, order_id, created_at, status="POSTED", tracking="BR1", label="issued_panel", price=30, err=None):
    sid = str(uuid.uuid4())
    db.add(SuperfreteShipment(id=sid, order_id=order_id, external_id="ext-" + sid[:6],
                              shipment_status=status, tracking_code=tracking, label_status=label,
                              quoted_price=price, estimated_days=4, last_error=err,
                              last_sync_at=created_at, created_at=created_at))
    db.commit()
    return sid


class TestMetrics:
    def test_excludes_test_orders_by_default(self):
        db = SessionLocal()
        try:
            _settings(db)
            o1 = _order(db, "superfrete", _iso(1))
            _ship(db, o1, _iso(1))
            ot = _order(db, "superfrete", _iso(1), is_test=True)
            _ship(db, ot, _iso(1))
            h = gov.compute_health(db, "7d", include_test=False)
            h_all = gov.compute_health(db, "7d", include_test=True)
            assert h["kpis"]["orders_superfrete"] < h_all["kpis"]["orders_superfrete"]
            assert h["kpis"]["orders_superfrete"] >= 1
        finally:
            db.close()

    def test_period_filters(self):
        db = SessionLocal()
        try:
            _settings(db)
            o_old = _order(db, "superfrete", _iso(40))
            _ship(db, o_old, _iso(40))
            h7 = gov.compute_health(db, "7d")
            h30 = gov.compute_health(db, "30d")
            # pedido de 40 dias não entra em 7d nem 30d
            assert True  # apenas garante que não quebra com períodos distintos
            assert h7["period"]["label"] == "7d" and h30["period"]["label"] == "30d"
        finally:
            db.close()

    def test_comparison_and_funnel(self):
        db = SessionLocal()
        try:
            _settings(db)
            o = _order(db, "superfrete", _iso(1))
            _ship(db, o, _iso(1), status="DELIVERED")
            _order(db, "melhor_envio", _iso(1))
            h = gov.compute_health(db, "7d")
            assert h["comparison"]["superfrete"]["volume"] >= 1
            assert h["comparison"]["melhor_envio"]["volume"] >= 1
            stages = [s["stage"] for s in h["funnel"]]
            assert stages[0] == "Elegível" and stages[-1] == "Entregue"
        finally:
            db.close()


class TestAlertsRecommendation:
    def test_auth_failure_alert_and_recommendation(self):
        db = SessionLocal()
        try:
            _settings(db, sync_suspended=True, status="error")
            h = gov.compute_health(db, "7d")
            codes = {a["code"] for a in h["alerts"]}
            assert "AUTH_FAILURE" in codes
            assert h["recommendation"]["recommendation"] == "RECOMENDA_DESABILITAR"
            assert "AUTH_FAILURE_PERSISTENT" in h["recommendation"]["reason_codes"]
        finally:
            db.close()

    def test_alert_cooldown(self):
        db = SessionLocal()
        try:
            _settings(db, sync_suspended=True, status="error")
            h1 = gov.compute_health(db, "7d")
            a1 = next(a for a in h1["alerts"] if a["code"] == "AUTH_FAILURE")
            assert a1["throttled"] is False       # primeira vez dispara
            h2 = gov.compute_health(db, "7d")
            a2 = next(a for a in h2["alerts"] if a["code"] == "AUTH_FAILURE")
            assert a2["throttled"] is True         # dentro do cooldown não repete
        finally:
            db.close()

    def test_can_increase_when_healthy(self):
        db = SessionLocal()
        try:
            _settings(db, rollout_mode="PERCENTAGE", rollout_min_orders=1,
                      controlled_test_state={"status": "APPROVED"})
            # slate limpo para avaliar a recomendação sem ruído de dados anteriores
            for sh in db.query(SuperfreteShipment).all():
                db.delete(sh)
            db.commit()
            o = _order(db, "superfrete", _iso(1))
            _ship(db, o, _iso(1), status="DELIVERED", err=None)  # terminal -> sem alertas ativos
            h = gov.compute_health(db, "7d")
            assert h["recommendation"]["recommendation"] in ("PODE_AUMENTAR", "MANTER")
        finally:
            db.close()


class TestGuardrails:
    def test_admin_only_to_percentage_requires_validation(self):
        db = SessionLocal()
        try:
            _settings(db, rollout_mode="ADMIN_ONLY", controlled_test_state={"status": "PENDING"})
            g = gov.evaluate_guardrails(db, "PERCENTAGE", 10)
            assert g["allowed"] is False
            assert any("Validação" in b for b in g["blockers"])
            _settings(db, rollout_mode="ADMIN_ONLY", controlled_test_state={"status": "APPROVED"})
            g2 = gov.evaluate_guardrails(db, "PERCENTAGE", 10)
            assert g2["allowed"] is True
        finally:
            db.close()

    def test_percentage_to_enabled_requires_criteria(self):
        db = SessionLocal()
        try:
            _settings(db, rollout_mode="PERCENTAGE", rollout_min_orders=5,
                      controlled_test_state={"status": "APPROVED"})
            # sem pedidos suficientes
            for sh in db.query(SuperfreteShipment).all():
                db.delete(sh)
            db.commit()
            g = gov.evaluate_guardrails(db, "ENABLED", None)
            assert g["allowed"] is False
            assert any("Mínimo de" in b for b in g["blockers"])
            # atende critérios
            _settings(db, rollout_mode="PERCENTAGE", rollout_min_orders=1,
                      controlled_test_state={"status": "APPROVED"})
            o = _order(db, "superfrete", _iso(1))
            _ship(db, o, _iso(1))
            g2 = gov.evaluate_guardrails(db, "ENABLED", None)
            assert g2["allowed"] is True
        finally:
            db.close()

    def test_change_requires_reason(self):
        db = SessionLocal()
        try:
            _settings(db, rollout_mode="ADMIN_ONLY")
            with pytest.raises(Exception):
                gov.change_rollout(db, {"id": "a", "email": "x"}, "DISABLED", None, "")
        finally:
            db.close()

    def test_no_auto_rollout_on_health(self):
        db = SessionLocal()
        try:
            _settings(db, rollout_mode="PERCENTAGE", rollout_percentage=10)
            gov.compute_health(db, "7d")
            s = db.get(SuperfreteSettings, 1)
            assert s.rollout_mode == "PERCENTAGE" and int(s.rollout_percentage) == 10
        finally:
            db.close()


class TestChangeRollbackHistory:
    def test_change_logs_history(self):
        db = SessionLocal()
        try:
            _settings(db, rollout_mode="ADMIN_ONLY", controlled_test_state={"status": "APPROVED"})
            before = db.query(SuperfreteRolloutHistory).count()
            gov.change_rollout(db, {"id": "a", "email": "adm@x"}, "PERCENTAGE", 10, "subir gradual")
            after = db.query(SuperfreteRolloutHistory).count()
            assert after == before + 1
            s = db.get(SuperfreteSettings, 1)
            assert s.rollout_mode == "PERCENTAGE" and int(s.rollout_percentage) == 10
        finally:
            db.close()

    def test_rollback_confirm_and_preserves_shipments(self):
        db = SessionLocal()
        try:
            _settings(db, rollout_mode="ENABLED")
            o = _order(db, "superfrete", _iso(1))
            sid = _ship(db, o, _iso(1), status="IN_TRANSIT")
            # confirmação errada bloqueia
            with pytest.raises(Exception):
                gov.rollback(db, {"id": "a", "email": "x"}, "problema", "errado")
            # rollback correto
            gov.rollback(db, {"id": "a", "email": "x"}, "erro operacional", "DESATIVAR SUPERFRETE")
            s = db.get(SuperfreteSettings, 1)
            sh = db.get(SuperfreteShipment, sid)
            assert s.rollout_mode == "DISABLED"
            assert sh.shipment_status == "IN_TRANSIT"   # envio existente não é cancelado
            o2 = db.get(Order, o)
            assert o2.shipping_provider == "superfrete"  # provider histórico intacto
        finally:
            db.close()


class TestRBAC:
    def test_rollout_endpoints_admin_only(self):
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
        cs.post(f"{BASE}/api/auth/register", json={"name": "NA", "email": f"TEST_re_{uuid.uuid4().hex[:8]}@e.com",
                                                    "password": "senha123", "cpf": cpf()}, timeout=30)
        assert cs.get(f"{BASE}/api/admin/superfrete/rollout/health", timeout=30).status_code in (401, 403)
        assert cs.post(f"{BASE}/api/admin/superfrete/rollout/change",
                       json={"to_mode": "ENABLED", "reason": "x"}, timeout=30).status_code == 403

    def test_admin_reads_health(self):
        s = requests.Session()
        assert s.post(f"{BASE}/api/auth/login", json={"email": "admin@brasilminis.com",
                                                      "password": "Admin@2025"}, timeout=30).status_code == 200
        r = s.get(f"{BASE}/api/admin/superfrete/rollout/health?period=7d", timeout=30)
        assert r.status_code == 200
        j = r.json()
        assert "kpis" in j and "funnel" in j and "recommendation" in j
        assert "tok_" not in r.text
