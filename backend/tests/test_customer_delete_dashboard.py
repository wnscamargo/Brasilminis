"""Exclusão protegida de clientes + zeragem do Dashboard (baseline).

Roda contra o backend (HTTPS do preview, auth por cookie Secure).
"""
import os
import uuid
import random

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@brasilminis.com"
ADMIN_PASSWORD = "Admin@2025"


def _gen_cpf():
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
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return s


def _new_customer():
    email = f"TEST_cd_{uuid.uuid4().hex[:8]}@example.com"
    cpf = _gen_cpf()
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Cliente CD", "email": email, "password": "senha123", "cpf": cpf,
    }, timeout=30)
    assert r.status_code == 200, r.text
    return s, r.json()["id"], email, cpf


def _del(session, uid, reason="motivo", confirm="EXCLUIR", anonymize=False):
    return session.request("DELETE", f"{BASE_URL}/api/admin/customers/{uid}",
                           json={"reason": reason, "confirm": confirm, "anonymize": anonymize}, timeout=30)


# ---------------- Exclusão de cliente ----------------
class TestDeleteCustomer:
    def test_customer_forbidden(self, admin_session):
        cs, uid, _, _ = _new_customer()
        r = _del(cs, uid)  # cliente tentando excluir
        assert r.status_code == 403

    def test_wrong_confirm(self, admin_session):
        _, uid, _, _ = _new_customer()
        r = _del(admin_session, uid, confirm="EXCLUI")
        assert r.status_code == 400

    def test_reason_required(self, admin_session):
        _, uid, _, _ = _new_customer()
        r = _del(admin_session, uid, reason="")
        assert r.status_code == 400

    def test_delete_success_and_idempotent(self, admin_session):
        _, uid, _, _ = _new_customer()
        r1 = _del(admin_session, uid, reason="teste")
        assert r1.status_code == 200, r1.text
        assert r1.json()["customer"]["deleted_at"]
        r2 = _del(admin_session, uid, reason="teste")
        assert r2.status_code == 200
        assert r2.json().get("already_deleted") is True

    def test_scope_filter(self, admin_session):
        _, uid, _, _ = _new_customer()
        _del(admin_session, uid, reason="teste")
        active = admin_session.get(f"{BASE_URL}/api/admin/customers?scope=active", timeout=30).json()
        deleted = admin_session.get(f"{BASE_URL}/api/admin/customers?scope=deleted", timeout=30).json()
        allc = admin_session.get(f"{BASE_URL}/api/admin/customers?scope=all", timeout=30).json()
        assert not any(c["id"] == uid for c in active)
        assert any(c["id"] == uid for c in deleted)
        assert any(c["id"] == uid for c in allc)

    def test_deleted_cannot_login(self, admin_session):
        cs, uid, email, _ = _new_customer()
        _del(admin_session, uid, reason="teste")
        r = cs.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "senha123"}, timeout=30)
        assert r.status_code == 403

    def test_orders_history_preserved(self, admin_session):
        # cria produto com estoque, faz pedido, exclui cliente, pedido continua no banco
        pr = admin_session.post(f"{BASE_URL}/api/admin/products", json={
            "name": f"TEST CDprod {uuid.uuid4().hex[:6]}", "description": "", "price": 50.0,
            "stock": 20, "images": [], "badges": [], "specs": {},
        }, timeout=30)
        assert pr.status_code == 200, pr.text
        pid = pr.json()["id"]
        cs, uid, _, _ = _new_customer()
        order = cs.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": pid, "quantity": 1}], "shipping_method": "standard", "payment_method": "pix",
        }, timeout=30)
        assert order.status_code == 200, order.text
        oid = order.json()["id"]
        assert _del(admin_session, uid, reason="teste").status_code == 200
        # pedido ainda existe (visível no admin)
        orders = admin_session.get(f"{BASE_URL}/api/admin/orders?scope=all", timeout=30).json()
        assert any(o["id"] == oid for o in orders)

    def test_anonymize_frees_email_cpf(self, admin_session):
        cs, uid, email, cpf = _new_customer()
        assert _del(admin_session, uid, reason="lgpd", anonymize=True).status_code == 200
        # e-mail e CPF liberados: novo cadastro com os mesmos dados deve funcionar
        s2 = requests.Session()
        r = s2.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Reuso", "email": email, "password": "senha123", "cpf": cpf,
        }, timeout=30)
        assert r.status_code == 200, r.text


# ---------------- Restauração ----------------
class TestRestoreCustomer:
    def test_restore_success(self, admin_session):
        cs, uid, email, _ = _new_customer()
        _del(admin_session, uid, reason="teste")
        r = admin_session.post(f"{BASE_URL}/api/admin/customers/{uid}/restore", timeout=30)
        assert r.status_code == 200, r.text
        # volta a logar
        r2 = cs.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "senha123"}, timeout=30)
        assert r2.status_code == 200

    def test_restore_conflict(self, admin_session):
        # A excluído+anonimizado libera CPF; B novo usa o CPF; restaurar A não gera conflito
        # (A ficou sem CPF). Conflito de e-mail: A excluído (não anonimizado) mantém e-mail único,
        # logo B não consegue registrar -> testamos o caminho amigável forçando colisão de e-mail.
        csA, uidA, emailA, cpfA = _new_customer()
        assert _del(admin_session, uidA, reason="lgpd", anonymize=True).status_code == 200
        # B reusa o e-mail liberado
        sB = requests.Session()
        rB = sB.post(f"{BASE_URL}/api/auth/register", json={
            "name": "B", "email": emailA, "password": "senha123", "cpf": _gen_cpf(),
        }, timeout=30)
        assert rB.status_code == 200, rB.text
        # restaurar A: e-mail de A foi anonimizado (deleted+...), então NÃO conflita -> restaura ok
        r = admin_session.post(f"{BASE_URL}/api/admin/customers/{uidA}/restore", timeout=30)
        assert r.status_code == 200, r.text

    def test_rbac_restore_forbidden(self, admin_session):
        _, uid, _, _ = _new_customer()
        _del(admin_session, uid, reason="teste")
        other, _, _, _ = _new_customer()  # cliente ATIVO separado
        r = other.post(f"{BASE_URL}/api/admin/customers/{uid}/restore", timeout=30)
        assert r.status_code == 403


# ---------------- Zeragem do Dashboard ----------------
class TestDashboardReset:
    def test_rbac_forbidden(self):
        cs, _, _, _ = _new_customer()
        r = cs.post(f"{BASE_URL}/api/admin/dashboard/reset", json={"reason": "x", "confirm": "ZERAR DASHBOARD"}, timeout=30)
        assert r.status_code == 403
        r2 = cs.get(f"{BASE_URL}/api/admin/dashboard/baseline", timeout=30)
        assert r2.status_code == 403

    def test_wrong_confirm(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/admin/dashboard/reset", json={"reason": "fechamento", "confirm": "ZERAR"}, timeout=30)
        assert r.status_code == 400

    def test_reason_required(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/admin/dashboard/reset", json={"reason": "", "confirm": "ZERAR DASHBOARD"}, timeout=30)
        assert r.status_code == 400

    def test_reset_creates_baseline_and_history(self, admin_session):
        before = admin_session.get(f"{BASE_URL}/api/admin/dashboard/baseline", timeout=30).json()
        r = admin_session.post(f"{BASE_URL}/api/admin/dashboard/reset", json={"reason": "fechamento mensal", "confirm": "ZERAR DASHBOARD"}, timeout=30)
        assert r.status_code == 200, r.text
        after = admin_session.get(f"{BASE_URL}/api/admin/dashboard/baseline", timeout=30).json()
        assert after["baseline"] and after["baseline"] != before.get("baseline")
        assert len(after["history"]) == len(before.get("history", [])) + 1

    def test_default_period_zeroes_after_reset(self, admin_session):
        # cria produto+pedido, zera, e o período padrão 30d passa a NÃO contar o pedido anterior
        pr = admin_session.post(f"{BASE_URL}/api/admin/products", json={
            "name": f"TEST RZprod {uuid.uuid4().hex[:6]}", "description": "", "price": 40.0,
            "stock": 10, "images": [], "badges": [], "specs": {},
        }, timeout=30)
        pid = pr.json()["id"]
        cs, uid, _, _ = _new_customer()
        cs.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": pid, "quantity": 1}], "shipping_method": "standard", "payment_method": "pix",
        }, timeout=30)
        # zera
        admin_session.post(f"{BASE_URL}/api/admin/dashboard/reset", json={"reason": "reset teste", "confirm": "ZERAR DASHBOARD"}, timeout=30)
        an = admin_session.get(f"{BASE_URL}/api/admin/analytics?period=30d", timeout=30).json()
        assert an["orders_count"] == 0, "período padrão deve iniciar em zero após zeragem"
        assert an.get("baseline")

    def test_new_orders_count_after_reset(self, admin_session):
        admin_session.post(f"{BASE_URL}/api/admin/dashboard/reset", json={"reason": "reset base", "confirm": "ZERAR DASHBOARD"}, timeout=30)
        pr = admin_session.post(f"{BASE_URL}/api/admin/products", json={
            "name": f"TEST NEWord {uuid.uuid4().hex[:6]}", "description": "", "price": 30.0,
            "stock": 10, "images": [], "badges": [], "specs": {},
        }, timeout=30)
        pid = pr.json()["id"]
        cs, uid, _, _ = _new_customer()
        cs.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": pid, "quantity": 1}], "shipping_method": "standard", "payment_method": "pix",
        }, timeout=30)
        an = admin_session.get(f"{BASE_URL}/api/admin/analytics?period=30d", timeout=30).json()
        assert an["orders_count"] >= 1, "novos pedidos após o reset devem contar"

    def test_custom_period_accesses_history(self, admin_session):
        # período custom amplo deve enxergar dados anteriores ao marco (histórico acessível)
        an = admin_session.get(f"{BASE_URL}/api/admin/analytics",
                               params={"period": "custom", "start": "2020-01-01", "end": "2999-12-31"}, timeout=30).json()
        assert an.get("baseline") is None  # custom NÃO aplica baseline
        assert an["orders_count"] >= 1
