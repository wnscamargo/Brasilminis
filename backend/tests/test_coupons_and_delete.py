"""Backend tests for the review request (iteration 10):
- Coupon /coupons/preview (server-side computation, limits, scope, free_shipping)
- Order creation freezes coupon_snapshot and increments used_count
- Admin coupon CRUD RBAC
- Admin delete order (protected soft-delete, EXCLUIR confirm, MP block, RBAC, idempotency, stock return)
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "admin@brasilminis.com"
ADMIN_PASSWORD = "Admin@2025"


# ------------- Fixtures -------------
@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return s


def _new_customer():
    email = f"TEST_{uuid.uuid4().hex[:8]}@example.com"
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Cliente Cupom", "email": email, "password": "senha123", "newsletter": False,
    }, timeout=30)
    assert r.status_code == 200, r.text
    return s, r.json()["id"], email


@pytest.fixture(scope="module")
def customer_session():
    s, _, _ = _new_customer()
    return s


@pytest.fixture(scope="module")
def bm10(admin_session):
    """Create BM10 (10% off, min R$50) if it doesn't exist, else return current state."""
    r = admin_session.get(f"{BASE_URL}/api/admin/coupons", timeout=15)
    assert r.status_code == 200
    existing = next((c for c in r.json() if c["code"] == "BM10"), None)
    payload = {
        "code": "BM10", "type": "percent", "value": 10, "min_order": 50,
        "active": True, "description": "Teste BM10",
    }
    if existing:
        r = admin_session.put(f"{BASE_URL}/api/admin/coupons/BM10", json=payload, timeout=15)
    else:
        r = admin_session.post(f"{BASE_URL}/api/admin/coupons", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def sample_products():
    r = requests.get(f"{BASE_URL}/api/products?limit=5", timeout=15)
    assert r.status_code == 200
    items = r.json()["items"]
    assert items, "Expected seed products"
    return items


# ------------- Preview (server-side calc) -------------
class TestCouponPreview:
    def test_requires_auth(self, sample_products):
        p = sample_products[0]
        r = requests.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": "BM10", "items": [{"product_id": p["id"], "quantity": 1}],
        }, timeout=15)
        assert r.status_code in (401, 403), r.text

    def test_bm10_ok(self, customer_session, bm10, sample_products):
        # find product/qty so subtotal >= 50
        p = sample_products[0]
        qty = max(1, int(60 / max(1, float(p["price"]))) + 1)
        r = customer_session.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": "BM10", "items": [{"product_id": p["id"], "quantity": qty}],
        }, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        subtotal = body["subtotal"]
        assert subtotal >= 50.0
        expected = round(subtotal * 0.10 + 1e-9, 2)
        assert abs(body["discount"] - expected) < 0.02, body
        assert body["code"] == "BM10"
        assert body["type"] == "percent"

    def test_below_min_order(self, customer_session, bm10, sample_products):
        # cheapest product qty=1
        cheapest = sorted(sample_products, key=lambda x: x["price"])[0]
        if cheapest["price"] * 1 >= 50:
            pytest.skip("Todos os produtos custam >= R$50; não dá pra testar mínimo")
        r = customer_session.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": "BM10", "items": [{"product_id": cheapest["id"], "quantity": 1}],
        }, timeout=15)
        assert r.status_code == 400
        assert "mínimo" in r.json()["detail"].lower() or "minimo" in r.json()["detail"].lower()

    def test_invalid_coupon(self, customer_session, sample_products):
        p = sample_products[0]
        r = customer_session.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": "DOESNOTEXIST", "items": [{"product_id": p["id"], "quantity": 2}],
        }, timeout=15)
        assert r.status_code == 400
        assert "inválido" in r.json()["detail"].lower() or "invalido" in r.json()["detail"].lower()


# ------------- Order with coupon -> snapshot + used_count -------------
class TestOrderCoupon:
    def test_order_freezes_snapshot_and_increments_used_count(self, admin_session, bm10, sample_products):
        # get baseline used_count for BM10
        base = next(c for c in admin_session.get(f"{BASE_URL}/api/admin/coupons").json() if c["code"] == "BM10")
        base_used = base["used_count"] or 0

        # fresh customer
        s, uid, email = _new_customer()
        p = sample_products[0]
        qty = max(1, int(60 / max(1, float(p["price"]))) + 1)
        r = s.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": p["id"], "quantity": qty}],
            "shipping_method": "standard",
            "payment_method": "pix",
            "coupon": "BM10",
        }, timeout=30)
        assert r.status_code == 200, r.text
        order = r.json()
        assert order["coupon"] == "BM10"
        assert order["discount"] and order["discount"] > 0
        snap = order.get("coupon_snapshot")
        assert snap, "coupon_snapshot deve estar congelado"
        assert snap["code"] == "BM10"
        assert snap["type"] == "percent"
        assert snap["value"] == 10.0
        assert snap["discount"] == order["discount"]
        assert snap["free_shipping"] is False

        after = next(c for c in admin_session.get(f"{BASE_URL}/api/admin/coupons").json() if c["code"] == "BM10")
        assert (after["used_count"] or 0) == base_used + 1, f"used_count deveria ir de {base_used} para {base_used+1}"


# ------------- Coupon limits -------------
class TestCouponLimits:
    def _create(self, admin_session, **overrides):
        code = f"TEST{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "code": code, "type": "percent", "value": 10, "min_order": 0,
            "active": True,
        }
        payload.update(overrides)
        r = admin_session.post(f"{BASE_URL}/api/admin/coupons", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        return code

    def test_inactive(self, admin_session, customer_session, sample_products):
        code = self._create(admin_session, active=False)
        p = sample_products[0]
        r = customer_session.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": code, "items": [{"product_id": p["id"], "quantity": 2}],
        }, timeout=15)
        assert r.status_code == 400
        assert "inativo" in r.json()["detail"].lower()
        admin_session.delete(f"{BASE_URL}/api/admin/coupons/{code}")

    def test_expired(self, admin_session, customer_session, sample_products):
        code = self._create(admin_session, expires_at="2000-01-01T00:00:00+00:00")
        p = sample_products[0]
        r = customer_session.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": code, "items": [{"product_id": p["id"], "quantity": 2}],
        }, timeout=15)
        assert r.status_code == 400
        assert "expirado" in r.json()["detail"].lower()
        admin_session.delete(f"{BASE_URL}/api/admin/coupons/{code}")

    def test_usage_limit_exhausted(self, admin_session, customer_session, sample_products):
        code = self._create(admin_session, usage_limit=1)
        # Manually bump used_count via update? The service exposes used_count only through orders.
        # Simulate by updating via PUT? update_coupon doesn't accept used_count. Instead, place one order.
        s, _, _ = _new_customer()
        p = sample_products[0]
        r1 = s.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": p["id"], "quantity": 1}],
            "shipping_method": "standard", "payment_method": "pix", "coupon": code,
        }, timeout=30)
        assert r1.status_code == 200, r1.text
        # Second attempt: should fail
        r2 = customer_session.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": code, "items": [{"product_id": p["id"], "quantity": 1}],
        }, timeout=15)
        assert r2.status_code == 400
        assert "esgotado" in r2.json()["detail"].lower() or "limite" in r2.json()["detail"].lower()
        admin_session.delete(f"{BASE_URL}/api/admin/coupons/{code}")

    def test_per_user_limit(self, admin_session, sample_products):
        code = self._create(admin_session, per_user_limit=1)
        s, _, _ = _new_customer()
        p = sample_products[0]
        r1 = s.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": p["id"], "quantity": 1}],
            "shipping_method": "standard", "payment_method": "pix", "coupon": code,
        }, timeout=30)
        assert r1.status_code == 200
        # Same user preview second time
        r2 = s.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": code, "items": [{"product_id": p["id"], "quantity": 1}],
        }, timeout=15)
        assert r2.status_code == 400
        assert "máximo" in r2.json()["detail"].lower() or "maximo" in r2.json()["detail"].lower() or "utiliz" in r2.json()["detail"].lower()
        admin_session.delete(f"{BASE_URL}/api/admin/coupons/{code}")

    def test_first_purchase_only(self, admin_session, sample_products):
        code = self._create(admin_session, first_purchase_only=True)
        s, _, _ = _new_customer()
        p = sample_products[0]
        # place a first order WITHOUT coupon so user is no longer "first purchase"
        r_first = s.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": p["id"], "quantity": 1}],
            "shipping_method": "standard", "payment_method": "pix",
        }, timeout=30)
        assert r_first.status_code == 200
        r = s.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": code, "items": [{"product_id": p["id"], "quantity": 1}],
        }, timeout=15)
        assert r.status_code == 400
        assert "primeira" in r.json()["detail"].lower()
        admin_session.delete(f"{BASE_URL}/api/admin/coupons/{code}")


# ------------- Coupon scope (categories/products) -------------
class TestCouponScope:
    def test_products_scope_not_applicable(self, admin_session, customer_session, sample_products):
        assert len(sample_products) >= 2
        elig = sample_products[0]
        other = sample_products[1]
        code = f"TEST{uuid.uuid4().hex[:6].upper()}"
        r = admin_session.post(f"{BASE_URL}/api/admin/coupons", json={
            "code": code, "type": "percent", "value": 10, "active": True,
            "scope_type": "products", "scope_product_ids": [elig["id"]],
        }, timeout=15)
        assert r.status_code == 200
        # Cart contains only the other product -> not eligible
        r2 = customer_session.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": code, "items": [{"product_id": other["id"], "quantity": 2}],
        }, timeout=15)
        assert r2.status_code == 400
        assert "aplicável" in r2.json()["detail"].lower() or "aplicavel" in r2.json()["detail"].lower()

        # Cart contains eligible product -> works
        r3 = customer_session.post(f"{BASE_URL}/api/coupons/preview", json={
            "code": code, "items": [{"product_id": elig["id"], "quantity": 1}],
        }, timeout=15)
        assert r3.status_code == 200
        admin_session.delete(f"{BASE_URL}/api/admin/coupons/{code}")


# ------------- Free shipping coupon -------------
class TestFreeShipping:
    def test_free_shipping_applies(self, admin_session, sample_products):
        # Ensure FRETEGRATIS is a free_shipping coupon (NB: seed originally has type=fixed value=29.9)
        # Update to correct definition for the test.
        admin_session.put(f"{BASE_URL}/api/admin/coupons/FRETEGRATIS", json={
            "code": "FRETEGRATIS", "type": "percent", "value": 0, "min_order": 0,
            "active": True, "free_shipping": True, "description": "Frete grátis",
        }, timeout=15)
        s, _, _ = _new_customer()
        p = sample_products[0]
        r = s.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": p["id"], "quantity": 1}],
            "shipping_method": "standard", "payment_method": "pix",
            "coupon": "FRETEGRATIS",
        }, timeout=30)
        assert r.status_code == 200, r.text
        order = r.json()
        assert float(order["shipping"]) == 0.0
        snap = order.get("coupon_snapshot")
        assert snap and snap.get("free_shipping") is True


# ------------- Admin CRUD RBAC on coupons -------------
class TestCouponRBAC:
    def test_anon_forbidden(self):
        for m, url in [
            ("get", f"{BASE_URL}/api/admin/coupons"),
            ("post", f"{BASE_URL}/api/admin/coupons"),
            ("post", f"{BASE_URL}/api/admin/coupons/generate-code"),
        ]:
            fn = getattr(requests, m)
            kw = {"timeout": 15}
            if m == "post":
                kw["json"] = {"code": "X"}
            r = fn(url, **kw)
            assert r.status_code in (401, 403), f"{m} {url} -> {r.status_code}"

    def test_customer_forbidden(self, customer_session):
        r = customer_session.get(f"{BASE_URL}/api/admin/coupons", timeout=15)
        assert r.status_code == 403

    def test_admin_generate_code(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/admin/coupons/generate-code",
                               json={"prefix": "BM", "length": 8}, timeout=15)
        assert r.status_code == 200
        code = r.json()["code"]
        assert code.startswith("BM") and len(code) >= 6


# ------------- Delete order (protected) -------------
class TestDeleteOrder:
    @pytest.fixture(scope="class")
    def order_and_stock(self, admin_session):
        # place a fresh order to be deleted
        s, uid, email = _new_customer()
        prods = requests.get(f"{BASE_URL}/api/products?limit=5", timeout=15).json()["items"]
        p = next(x for x in prods if x["stock"] >= 3)
        stock_before = p["stock"]
        r = s.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": p["id"], "quantity": 2}],
            "shipping_method": "standard", "payment_method": "pix",
        }, timeout=30)
        assert r.status_code == 200
        oid = r.json()["id"]
        # verify stock decremented
        p2 = requests.get(f"{BASE_URL}/api/products/{p['slug']}", timeout=15).json()
        assert p2["stock"] == stock_before - 2
        return {"session": s, "order_id": oid, "product": p, "stock_before": stock_before}

    def test_confirm_wrong(self, admin_session, order_and_stock):
        r = admin_session.request("DELETE", f"{BASE_URL}/api/admin/orders/{order_and_stock['order_id']}",
                                  json={"reason": "teste", "confirm": "nope"}, timeout=15)
        assert r.status_code == 400
        assert "EXCLUIR" in r.json()["detail"]

    def test_reason_empty(self, admin_session, order_and_stock):
        r = admin_session.request("DELETE", f"{BASE_URL}/api/admin/orders/{order_and_stock['order_id']}",
                                  json={"reason": "", "confirm": "EXCLUIR"}, timeout=15)
        # pydantic may accept empty string; service should reject 400
        assert r.status_code == 400

    def test_rbac_customer_forbidden(self, order_and_stock):
        s = order_and_stock["session"]
        r = s.request("DELETE", f"{BASE_URL}/api/admin/orders/{order_and_stock['order_id']}",
                      json={"reason": "x", "confirm": "EXCLUIR"}, timeout=15)
        assert r.status_code == 403

    def test_delete_success_returns_stock_once(self, admin_session, order_and_stock):
        oid = order_and_stock["order_id"]
        p = order_and_stock["product"]
        stock_before_delete = requests.get(f"{BASE_URL}/api/products/{p['slug']}", timeout=15).json()["stock"]
        r = admin_session.request("DELETE", f"{BASE_URL}/api/admin/orders/{oid}",
                                  json={"reason": "teste unitário", "confirm": "EXCLUIR"}, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("ok") is True
        stock_after = requests.get(f"{BASE_URL}/api/products/{p['slug']}", timeout=15).json()["stock"]
        assert stock_after == stock_before_delete + 2, f"esperado +2, foi {stock_after - stock_before_delete}"

        # Idempotency: second delete -> already_deleted True, stock NOT changed
        r2 = admin_session.request("DELETE", f"{BASE_URL}/api/admin/orders/{oid}",
                                   json={"reason": "again", "confirm": "EXCLUIR"}, timeout=15)
        assert r2.status_code == 200
        assert r2.json().get("already_deleted") is True
        stock_after2 = requests.get(f"{BASE_URL}/api/products/{p['slug']}", timeout=15).json()["stock"]
        assert stock_after2 == stock_after, "stock should NOT be returned twice"

    def test_scopes_filter(self, admin_session, order_and_stock):
        oid = order_and_stock["order_id"]
        active = admin_session.get(f"{BASE_URL}/api/admin/orders?scope=active", timeout=15).json()
        deleted = admin_session.get(f"{BASE_URL}/api/admin/orders?scope=deleted", timeout=15).json()
        assert not any(o["id"] == oid for o in active)
        assert any(o["id"] == oid for o in deleted)

        # customer must not see deleted order in GET /api/orders
        s = order_and_stock["session"]
        my = s.get(f"{BASE_URL}/api/orders", timeout=15).json()
        assert not any(o["id"] == oid for o in my)


# ------------- MP block via direct DB manipulation -------------
class TestDeleteOrderMPBlock:
    def test_mp_approved_blocks_delete(self, admin_session):
        # place order then set payment_provider/status directly in DB
        s, _, _ = _new_customer()
        prods = requests.get(f"{BASE_URL}/api/products?limit=5", timeout=15).json()["items"]
        p = next(x for x in prods if x["stock"] >= 1)
        r = s.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": p["id"], "quantity": 1}],
            "shipping_method": "standard", "payment_method": "pix",
        }, timeout=30)
        assert r.status_code == 200
        oid = r.json()["id"]

        # Update DB via sqlalchemy directly using the app's engine
        import sys
        sys.path.insert(0, "/app/backend")
        # Load backend .env so DATABASE_URL is available in this process
        from dotenv import load_dotenv
        load_dotenv("/app/backend/.env")
        from app.db.session import SessionLocal
        from app.models import Order
        db = SessionLocal()
        try:
            o = db.get(Order, oid)
            o.payment_provider = "mercado_pago"
            o.payment_status = "approved"
            db.commit()
        finally:
            db.close()

        r2 = admin_session.request("DELETE", f"{BASE_URL}/api/admin/orders/{oid}",
                                   json={"reason": "tentativa bloqueada", "confirm": "EXCLUIR"}, timeout=15)
        assert r2.status_code == 409, r2.text
        assert "Mercado Pago" in r2.json()["detail"] or "confirmado" in r2.json()["detail"].lower() or "CONFIRMADO" in r2.json()["detail"]

        # Cleanup: revert so it doesn't leak
        db = SessionLocal()
        try:
            o = db.get(Order, oid)
            o.payment_provider = None
            o.payment_status = "paid_simulated"
            db.commit()
        finally:
            db.close()
