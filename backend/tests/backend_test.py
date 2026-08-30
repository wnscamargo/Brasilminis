"""Brasil Minis backend regression suite (PostgreSQL rewrite).

Runs against the public preview URL to cover cookie-based auth (SameSite=none, Secure).
"""
import os
import time
import uuid
import concurrent.futures

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://vroom-preview.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@brasilminis.com"
ADMIN_PASSWORD = "Admin@2025"


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    body = r.json()
    assert body["role"] == "admin"
    return s


@pytest.fixture(scope="session")
def customer_creds():
    email = f"TEST_{uuid.uuid4().hex[:8]}@example.com"
    password = "senha123"
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Cliente Teste", "email": email, "password": password, "newsletter": False
    }, timeout=30)
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
    return {"email": email, "password": password, "id": r.json()["id"], "session": s}


@pytest.fixture()
def customer_session(customer_creds):
    return customer_creds["session"]


# ---------- Health / Root ----------
class TestHealth:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_root(self):
        r = requests.get(f"{BASE_URL}/api/", timeout=15)
        assert r.status_code == 200
        assert "online" in r.json()["message"].lower()


# ---------- Catalog ----------
class TestCatalog:
    def test_list_products(self):
        r = requests.get(f"{BASE_URL}/api/products?limit=5", timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ("total", "page", "limit", "items"):
            assert k in d
        assert d["limit"] == 5
        assert len(d["items"]) <= 5
        assert d["total"] >= 1

    def test_filters(self):
        r = requests.get(f"{BASE_URL}/api/products?featured=true", timeout=15)
        assert r.status_code == 200
        for it in r.json()["items"]:
            assert it["featured"] is True

    def test_search(self):
        r = requests.get(f"{BASE_URL}/api/products?search=mini", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json()["items"], list)

    def test_sort_price_asc(self):
        r = requests.get(f"{BASE_URL}/api/products?sort=price_asc&limit=10", timeout=15)
        assert r.status_code == 200
        prices = [i["price"] for i in r.json()["items"]]
        assert prices == sorted(prices)

    def test_product_by_slug_and_related(self):
        base = requests.get(f"{BASE_URL}/api/products?limit=1", timeout=15).json()["items"][0]
        slug = base["slug"]
        r = requests.get(f"{BASE_URL}/api/products/{slug}", timeout=15)
        assert r.status_code == 200
        assert r.json()["slug"] == slug
        r2 = requests.get(f"{BASE_URL}/api/products/{slug}/related", timeout=15)
        assert r2.status_code == 200
        assert isinstance(r2.json(), list)

    def test_product_not_found(self):
        r = requests.get(f"{BASE_URL}/api/products/nope-nope-{uuid.uuid4().hex[:6]}", timeout=15)
        assert r.status_code == 404

    def test_categories_and_brands(self):
        rc = requests.get(f"{BASE_URL}/api/categories", timeout=15)
        assert rc.status_code == 200 and isinstance(rc.json(), list)
        rb = requests.get(f"{BASE_URL}/api/brands", timeout=15)
        assert rb.status_code == 200 and isinstance(rb.json(), list)

    def test_banners(self):
        r = requests.get(f"{BASE_URL}/api/banners", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------- Auth ----------
class TestAuth:
    def test_admin_login_sets_cookies(self, admin_session):
        cookies = admin_session.cookies.get_dict()
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    def test_me_with_cookie(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN_EMAIL
        assert r.json()["role"] == "admin"

    def test_me_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 401

    def test_refresh(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/auth/refresh", timeout=15)
        assert r.status_code == 200

    def test_logout(self):
        s = requests.Session()
        s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        r = s.post(f"{BASE_URL}/api/auth/logout", timeout=15)
        assert r.status_code == 200

    def test_forgot_password_generic(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": "nonexistent@example.com"}, timeout=15)
        assert r.status_code == 200
        assert "instru" in r.json()["message"].lower() or "existir" in r.json()["message"].lower()

    def test_reset_password_invalid_token(self):
        r = requests.post(f"{BASE_URL}/api/auth/reset-password",
                          json={"token": "invalid-token-xyz", "password": "novasenha123"}, timeout=15)
        assert r.status_code == 400

    def test_bearer_auth_on_me(self):
        # login and use access token as Bearer
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        token = r.cookies.get("access_token")
        assert token
        rr = requests.get(f"{BASE_URL}/api/auth/me",
                          headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert rr.status_code == 200

    def test_brute_force_lockout(self):
        # Use a fresh email to avoid clobbering other tests
        bad_email = f"TEST_bf_{uuid.uuid4().hex[:6]}@example.com"
        last_status = None
        for _ in range(6):
            r = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": bad_email, "password": "wrongwrong"}, timeout=15)
            last_status = r.status_code
        # After MAX_ATTEMPTS wrong tries, next call should be 429
        assert last_status in (401, 429)
        r2 = requests.post(f"{BASE_URL}/api/auth/login",
                           json={"email": bad_email, "password": "wrongwrong"}, timeout=15)
        assert r2.status_code == 429, f"Expected 429 after brute force, got {r2.status_code}"


# ---------- RBAC ----------
class TestRBAC:
    def test_admin_stats_anonymous(self):
        r = requests.get(f"{BASE_URL}/api/admin/stats", timeout=15)
        assert r.status_code == 401

    def test_admin_stats_customer_forbidden(self, customer_session):
        r = customer_session.get(f"{BASE_URL}/api/admin/stats", timeout=15)
        assert r.status_code == 403

    def test_admin_stats_ok(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/stats", timeout=15)
        assert r.status_code == 200
        for k in ("total_products", "total_orders", "total_customers",
                  "revenue", "low_stock", "revenue_series", "recent_orders"):
            assert k in r.json()


# ---------- Coupons ----------
class TestCoupons:
    @pytest.mark.parametrize("code", ["BRASIL10", "MINIS20", "FRETEGRATIS"])
    def test_valid_coupons(self, code):
        r = requests.post(f"{BASE_URL}/api/coupons/validate", json={"code": code}, timeout=15)
        assert r.status_code == 200, f"{code} -> {r.status_code} {r.text}"
        assert r.json()["code"].upper() == code

    def test_invalid_coupon(self):
        r = requests.post(f"{BASE_URL}/api/coupons/validate", json={"code": "BOGUSCODE"}, timeout=15)
        assert r.status_code == 400


# ---------- Orders + Atomic Stock ----------
class TestOrders:
    def _pick_product(self, min_stock=3):
        items = requests.get(f"{BASE_URL}/api/products?limit=50", timeout=15).json()["items"]
        for p in items:
            if p["stock"] >= min_stock:
                return p
        pytest.skip("No product with sufficient stock")

    def test_create_order_and_stock_decrement(self, customer_session):
        product = self._pick_product(min_stock=3)
        pid = product["id"]
        stock_before = product["stock"]
        payload = {
            "items": [{"product_id": pid, "quantity": 2}],
            "shipping_method": "standard",
            "payment_method": "pix",
        }
        r = customer_session.post(f"{BASE_URL}/api/orders", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "confirmado"
        assert body["payment_status"] == "paid_simulated"
        assert "payment" in body
        # Verify stock decrement
        after = requests.get(f"{BASE_URL}/api/products/{product['slug']}", timeout=15).json()
        assert after["stock"] == stock_before - 2, f"Expected {stock_before - 2}, got {after['stock']}"

    def test_oversell_rejected(self, customer_session):
        product = self._pick_product(min_stock=1)
        stock_before = product["stock"]
        payload = {
            "items": [{"product_id": product["id"], "quantity": stock_before + 100}],
            "shipping_method": "standard",
            "payment_method": "pix",
        }
        r = customer_session.post(f"{BASE_URL}/api/orders", json=payload, timeout=30)
        assert r.status_code == 400
        assert "estoque" in r.json()["detail"].lower()
        after = requests.get(f"{BASE_URL}/api/products/{product['slug']}", timeout=15).json()
        assert after["stock"] == stock_before, "Stock changed after failed oversell"

    def test_concurrent_no_negative_stock(self, customer_session):
        product = self._pick_product(min_stock=2)
        pid = product["id"]
        slug = product["slug"]
        stock_before = product["stock"]

        # Try to order (stock_before) items in parallel across N sessions
        # Only 1 should succeed if we buy full stock each; here we buy 1 each in N>>stock threads
        N = stock_before + 5

        def _place():
            s = requests.Session()
            s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
            # admin can also order
            return s.post(f"{BASE_URL}/api/orders", json={
                "items": [{"product_id": pid, "quantity": 1}],
                "shipping_method": "standard", "payment_method": "pix",
            }, timeout=30).status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(N, 10)) as ex:
            statuses = list(ex.map(lambda _: _place(), range(N)))
        successes = sum(1 for s in statuses if s == 200)
        # Not more successes than initial stock
        assert successes <= stock_before, f"successes={successes} stock_before={stock_before}"
        after = requests.get(f"{BASE_URL}/api/products/{slug}", timeout=15).json()
        assert after["stock"] >= 0, f"Negative stock! {after['stock']}"
        assert after["stock"] == stock_before - successes

    def test_order_with_coupon_and_shipping(self, customer_session):
        # Build cart that surpasses R$300 to trigger FRETEGRATIS/free shipping via total
        items = requests.get(f"{BASE_URL}/api/products?limit=50", timeout=15).json()["items"]
        # Pick a high-priced item with stock
        item = next((p for p in items if p["price"] >= 150 and p["stock"] >= 3), None)
        if not item:
            pytest.skip("no suitable product")
        payload = {
            "items": [{"product_id": item["id"], "quantity": 3}],
            "shipping_method": "standard",
            "payment_method": "pix",
            "coupon": "BRASIL10",
        }
        r = customer_session.post(f"{BASE_URL}/api/orders", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["coupon"] == "BRASIL10"
        assert body["discount"] > 0
        # subtotal - discount >= 300 -> free shipping
        if body["subtotal"] - body["discount"] >= 300:
            assert body["shipping"] == 0.0
        else:
            assert body["shipping"] == 29.9

    def test_empty_cart_rejected(self, customer_session):
        r = customer_session.post(f"{BASE_URL}/api/orders", json={"items": []}, timeout=15)
        assert r.status_code in (400, 422)

    def test_my_orders(self, customer_session):
        r = customer_session.get(f"{BASE_URL}/api/orders", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------- Account ----------
class TestAccount:
    def test_update_profile(self, customer_session):
        r = customer_session.put(f"{BASE_URL}/api/account/profile",
                                 json={"name": "Nome Atualizado", "phone": "11999999999"},
                                 timeout=15)
        assert r.status_code == 200
        assert r.json()["name"] == "Nome Atualizado"

    def test_wrong_current_password(self, customer_session):
        r = customer_session.put(f"{BASE_URL}/api/account/password",
                                 json={"current_password": "wrongpwd", "new_password": "novasenha1"},
                                 timeout=15)
        assert r.status_code == 400

    def test_address_flow(self, customer_session):
        # Start clean
        addrs = customer_session.get(f"{BASE_URL}/api/account/addresses", timeout=15).json()
        for a in addrs:
            customer_session.delete(f"{BASE_URL}/api/account/addresses/{a['id']}", timeout=15)

        payload = {
            "label": "Casa", "recipient": "Fulano", "street": "Rua X", "number": "10",
            "district": "Centro", "city": "SP", "state": "SP", "zip": "01000-000",
        }
        r = customer_session.post(f"{BASE_URL}/api/account/addresses", json=payload, timeout=15)
        assert r.status_code == 200
        addrs = r.json()
        assert len(addrs) == 1
        assert addrs[0]["is_default"] is True  # first becomes default

        # Delete
        aid = addrs[0]["id"]
        r2 = customer_session.delete(f"{BASE_URL}/api/account/addresses/{aid}", timeout=15)
        assert r2.status_code == 200
        assert r2.json() == []


# ---------- Favorites ----------
class TestFavorites:
    def test_favorites_idempotent(self, customer_session):
        pid = requests.get(f"{BASE_URL}/api/products?limit=1", timeout=15).json()["items"][0]["id"]
        r1 = customer_session.post(f"{BASE_URL}/api/favorites/{pid}", timeout=15)
        r2 = customer_session.post(f"{BASE_URL}/api/favorites/{pid}", timeout=15)
        assert r1.status_code == 200 and r2.status_code == 200
        favs = customer_session.get(f"{BASE_URL}/api/favorites", timeout=15).json()
        assert any(p["id"] == pid for p in favs)
        # delete twice idempotent
        d1 = customer_session.delete(f"{BASE_URL}/api/favorites/{pid}", timeout=15)
        d2 = customer_session.delete(f"{BASE_URL}/api/favorites/{pid}", timeout=15)
        assert d1.status_code == 200 and d2.status_code == 200


# ---------- Reviews ----------
class TestReviews:
    def test_review_recomputes_rating(self, customer_session):
        pid = requests.get(f"{BASE_URL}/api/products?limit=1", timeout=15).json()["items"][0]["id"]
        r = customer_session.post(f"{BASE_URL}/api/products/{pid}/reviews",
                                  json={"rating": 5, "comment": "TEST review"}, timeout=15)
        assert r.status_code == 200
        # Fetch product
        prod = None
        for p in requests.get(f"{BASE_URL}/api/products?limit=50", timeout=15).json()["items"]:
            if p["id"] == pid:
                prod = p
                break
        assert prod is not None
        assert prod["reviews_count"] >= 1
        assert prod["rating"] >= 1

    def test_review_requires_auth(self):
        pid = requests.get(f"{BASE_URL}/api/products?limit=1", timeout=15).json()["items"][0]["id"]
        r = requests.post(f"{BASE_URL}/api/products/{pid}/reviews",
                          json={"rating": 5, "comment": "x"}, timeout=15)
        assert r.status_code == 401


# ---------- Admin CRUD ----------
class TestAdminCRUD:
    def test_product_crud(self, admin_session):
        name = f"TEST Produto {uuid.uuid4().hex[:6]}"
        create = admin_session.post(f"{BASE_URL}/api/admin/products", json={
            "name": name, "description": "d", "price": 9.9,
            "category": "mochilas", "images": [], "stock": 5, "badges": [], "specs": {},
        }, timeout=15)
        assert create.status_code == 200, create.text
        pid = create.json()["id"]
        assert create.json()["slug"]  # slug auto-generated

        upd = admin_session.put(f"{BASE_URL}/api/admin/products/{pid}", json={
            "name": name + " v2", "description": "d", "price": 19.9,
            "category": "mochilas", "images": [], "stock": 8, "badges": [], "specs": {},
        }, timeout=15)
        assert upd.status_code == 200
        assert upd.json()["price"] == 19.9

        dele = admin_session.delete(f"{BASE_URL}/api/admin/products/{pid}", timeout=15)
        assert dele.status_code == 200

    def test_admin_orders_and_customers(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/orders", timeout=15)
        assert r.status_code == 200 and isinstance(r.json(), list)
        r2 = admin_session.get(f"{BASE_URL}/api/admin/customers", timeout=15)
        assert r2.status_code == 200 and isinstance(r2.json(), list)
        if r2.json():
            assert "orders_count" in r2.json()[0]

    def test_banner_crud(self, admin_session):
        create = admin_session.post(f"{BASE_URL}/api/admin/banners", json={
            "title": "TEST Banner", "image": "https://x/y.jpg", "position": 99, "active": True,
        }, timeout=15)
        assert create.status_code == 200
        bid = create.json()["id"]
        dele = admin_session.delete(f"{BASE_URL}/api/admin/banners/{bid}", timeout=15)
        assert dele.status_code == 200
