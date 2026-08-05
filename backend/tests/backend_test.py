"""
Brasil Minis - Comprehensive backend API tests.
Covers catalog, auth (register/login/me/logout), coupons, orders, favorites,
reviews, account, admin (RBAC), and banners.
"""
import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://vroom-preview.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@brasilminis.com"
ADMIN_PASSWORD = "Admin@2025"


# ---------------- Fixtures ----------------
@pytest.fixture(scope="session")
def anon():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def customer():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    email = f"TEST_customer_{uuid.uuid4().hex[:8]}@teste.com"
    r = s.post(f"{API}/auth/register", json={
        "name": "TEST Customer",
        "email": email,
        "password": "senha123",
        "newsletter": False,
    })
    assert r.status_code == 200, f"register failed {r.status_code} {r.text}"
    data = r.json()
    s.user = data
    s.email = email
    s.password = "senha123"
    return s


@pytest.fixture(scope="session")
def admin_sess():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"admin login failed {r.status_code} {r.text}"
    assert r.json().get("role") == "admin"
    return s


# ---------------- Health ----------------
def test_root_health(anon):
    r = anon.get(f"{API}/")
    assert r.status_code == 200
    assert "Brasil Minis" in r.json().get("message", "")


# ---------------- Catalog ----------------
class TestCatalog:
    def test_list_products_seeded(self, anon):
        r = anon.get(f"{API}/products")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "total" in data
        assert data["total"] >= 20, f"expected >=20 seeded products, got {data['total']}"
        assert len(data["items"]) > 0
        p = data["items"][0]
        assert "id" in p and "slug" in p and "price" in p
        assert "_id" not in p

    def test_filter_by_search(self, anon):
        r = anon.get(f"{API}/products", params={"search": "mochila"})
        assert r.status_code == 200
        items = r.json()["items"]
        assert all("mochila" in (p["name"] + p.get("description","")).lower() or "mochila" in p.get("category","").lower() for p in items) or len(items) >= 1

    def test_filter_sort_price_asc(self, anon):
        r = anon.get(f"{API}/products", params={"sort": "price_asc", "limit": 5})
        assert r.status_code == 200
        prices = [p["price"] for p in r.json()["items"]]
        assert prices == sorted(prices)

    def test_pagination(self, anon):
        r = anon.get(f"{API}/products", params={"limit": 5, "page": 2})
        assert r.status_code == 200
        assert r.json()["page"] == 2
        assert len(r.json()["items"]) <= 5

    def test_get_product_by_slug_and_related(self, anon):
        items = anon.get(f"{API}/products", params={"limit": 1}).json()["items"]
        slug = items[0]["slug"]
        r = anon.get(f"{API}/products/{slug}")
        assert r.status_code == 200
        assert r.json()["slug"] == slug
        rel = anon.get(f"{API}/products/{slug}/related")
        assert rel.status_code == 200
        assert isinstance(rel.json(), list)

    def test_product_not_found(self, anon):
        r = anon.get(f"{API}/products/does-not-exist-xyz")
        assert r.status_code == 404

    def test_categories_and_brands(self, anon):
        r = anon.get(f"{API}/categories")
        assert r.status_code == 200 and len(r.json()) > 0
        first = r.json()[0]
        assert "slug" in first
        r2 = anon.get(f"{API}/categories/{first['slug']}")
        assert r2.status_code == 200
        rb = anon.get(f"{API}/brands")
        assert rb.status_code == 200 and len(rb.json()) > 0

    def test_banners(self, anon):
        r = anon.get(f"{API}/banners")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------- Auth ----------------
class TestAuth:
    def test_register_login_me_logout_cycle(self, anon):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        email = f"TEST_cycle_{uuid.uuid4().hex[:8]}@teste.com"
        r = s.post(f"{API}/auth/register", json={
            "name": "Cycle User", "email": email, "password": "senha123", "newsletter": True,
        })
        assert r.status_code == 200
        assert r.json()["email"].lower() == email.lower()
        # httpOnly cookie set
        assert "access_token" in s.cookies.get_dict()

        me = s.get(f"{API}/auth/me")
        assert me.status_code == 200
        assert me.json()["email"].lower() == email.lower()

        # logout
        lo = s.post(f"{API}/auth/logout")
        assert lo.status_code == 200
        s.cookies.clear()
        me2 = s.get(f"{API}/auth/me")
        assert me2.status_code == 401

        # login again
        li = s.post(f"{API}/auth/login", json={"email": email, "password": "senha123"})
        assert li.status_code == 200

    def test_duplicate_register(self, anon, customer):
        r = anon.post(f"{API}/auth/register", json={
            "name": "Dup", "email": customer.email, "password": "senha123",
        })
        assert r.status_code == 400

    def test_login_bad_password(self, anon):
        r = anon.post(f"{API}/auth/login", json={
            "email": f"nouser_{uuid.uuid4().hex[:6]}@teste.com", "password": "wrong",
        })
        assert r.status_code == 401

    def test_me_requires_auth(self, anon):
        s = requests.Session()
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 401


# ---------------- Coupons ----------------
class TestCoupons:
    @pytest.mark.parametrize("code", ["BRASIL10", "MINIS20", "FRETEGRATIS"])
    def test_valid_coupons(self, anon, code):
        r = anon.post(f"{API}/coupons/validate", json={"code": code})
        assert r.status_code == 200, r.text
        assert r.json()["code"] == code

    def test_invalid_coupon(self, anon):
        r = anon.post(f"{API}/coupons/validate", json={"code": "INVALIDXYZ"})
        assert r.status_code == 400


# ---------------- Orders ----------------
class TestOrders:
    def _pick_products(self, anon, n=2):
        r = anon.get(f"{API}/products", params={"limit": 10})
        items = [p for p in r.json()["items"] if p.get("stock", 0) > 0][:n]
        return items

    def test_create_order_requires_auth(self, anon):
        r = anon.post(f"{API}/orders", json={"items": [{"product_id": "x", "quantity": 1}]})
        assert r.status_code == 401

    def test_create_order_with_coupon_and_shipping(self, anon, customer):
        prods = self._pick_products(anon, 1)
        assert prods
        p = prods[0]
        qty = 1
        r = customer.post(f"{API}/orders", json={
            "items": [{"product_id": p["id"], "quantity": qty}],
            "payment_method": "pix",
            "coupon": "BRASIL10" if p["price"] * qty >= 100 else None,
            "address": {
                "label": "Casa", "recipient": "TEST Customer", "street": "Rua A",
                "number": "10", "district": "Centro", "city": "SP", "state": "SP", "zip": "01000-000",
            },
        })
        assert r.status_code == 200, r.text
        order = r.json()
        assert order["order_number"].startswith("BM")
        subtotal = order["subtotal"]
        expected_shipping = 0.0 if (subtotal - order["discount"]) >= 300 else 29.9
        assert order["shipping"] == expected_shipping
        assert order["payment_status"] == "paid_simulated"
        assert order["payment"]["provider"] == "mock"

        # Verify GET /orders and by-id
        my = customer.get(f"{API}/orders")
        assert my.status_code == 200
        assert any(o["id"] == order["id"] for o in my.json())
        one = customer.get(f"{API}/orders/{order['id']}")
        assert one.status_code == 200
        assert one.json()["order_number"] == order["order_number"]

    def test_empty_cart(self, customer):
        r = customer.post(f"{API}/orders", json={"items": []})
        assert r.status_code == 400


# ---------------- Favorites ----------------
class TestFavorites:
    def test_favorites_flow(self, anon, customer):
        p = anon.get(f"{API}/products", params={"limit": 1}).json()["items"][0]
        pid = p["id"]
        add = customer.post(f"{API}/favorites/{pid}")
        assert add.status_code == 200
        lst = customer.get(f"{API}/favorites")
        assert lst.status_code == 200
        assert any(x["id"] == pid for x in lst.json())
        rm = customer.delete(f"{API}/favorites/{pid}")
        assert rm.status_code == 200
        lst2 = customer.get(f"{API}/favorites")
        assert not any(x["id"] == pid for x in lst2.json())

    def test_favorites_requires_auth(self, anon):
        r = anon.get(f"{API}/favorites")
        assert r.status_code == 401


# ---------------- Reviews ----------------
class TestReviews:
    def test_add_review_updates_rating(self, anon, customer):
        p = anon.get(f"{API}/products", params={"limit": 1}).json()["items"][0]
        pid = p["id"]
        r = customer.post(f"{API}/products/{pid}/reviews", json={"rating": 5, "comment": "Excelente"})
        assert r.status_code == 200, r.text
        # refetch product
        fresh = anon.get(f"{API}/products/{p['slug']}").json()
        assert fresh["reviews_count"] >= 1
        assert fresh["rating"] > 0


# ---------------- Account ----------------
class TestAccount:
    def test_update_profile(self, customer):
        r = customer.put(f"{API}/account/profile", json={"name": "TEST Updated", "phone": "11999"})
        assert r.status_code == 200
        assert r.json()["name"] == "TEST Updated"
        assert r.json()["phone"] == "11999"

    def test_change_password_and_revert(self, customer):
        r = customer.put(f"{API}/account/password", json={
            "current_password": customer.password, "new_password": "novasenha123",
        })
        assert r.status_code == 200
        # revert
        r2 = customer.put(f"{API}/account/password", json={
            "current_password": "novasenha123", "new_password": customer.password,
        })
        assert r2.status_code == 200

    def test_addresses_crud(self, customer):
        payload = {
            "label": "Casa", "recipient": "TEST", "street": "R", "number": "1",
            "district": "D", "city": "C", "state": "SP", "zip": "01000-000", "is_default": True,
        }
        add = customer.post(f"{API}/account/addresses", json=payload)
        assert add.status_code == 200
        addrs = add.json()
        assert len(addrs) >= 1
        aid = addrs[-1]["id"]
        lst = customer.get(f"{API}/account/addresses")
        assert lst.status_code == 200
        rm = customer.delete(f"{API}/account/addresses/{aid}")
        assert rm.status_code == 200
        assert not any(a["id"] == aid for a in rm.json())


# ---------------- Admin RBAC + CRUD ----------------
class TestAdmin:
    def test_customer_forbidden(self, customer):
        r = customer.get(f"{API}/admin/stats")
        assert r.status_code == 403

    def test_stats(self, admin_sess):
        r = admin_sess.get(f"{API}/admin/stats")
        assert r.status_code == 200
        d = r.json()
        for k in ["total_products", "total_orders", "total_customers", "revenue", "low_stock", "revenue_series", "recent_orders"]:
            assert k in d

    def test_admin_lists(self, admin_sess):
        for path in ["/admin/products", "/admin/orders", "/admin/customers", "/admin/banners"]:
            r = admin_sess.get(f"{API}{path}")
            assert r.status_code == 200, f"{path} -> {r.status_code}"

    def test_product_crud(self, admin_sess):
        payload = {
            "name": f"TEST Product {uuid.uuid4().hex[:6]}",
            "description": "Test", "price": 199.9, "category": "carros",
            "group": "miniaturas", "brand": "", "images": ["https://x/y.jpg"],
            "stock": 10, "badges": [], "specs": {}, "featured": False, "is_active": True,
        }
        r = admin_sess.post(f"{API}/admin/products", json=payload)
        assert r.status_code == 200, r.text
        prod = r.json()
        pid = prod["id"]
        # update
        payload["price"] = 149.9
        payload["name"] = prod["name"]
        u = admin_sess.put(f"{API}/admin/products/{pid}", json=payload)
        assert u.status_code == 200 and u.json()["price"] == 149.9
        # delete
        d = admin_sess.delete(f"{API}/admin/products/{pid}")
        assert d.status_code == 200

    def test_category_and_brand_and_banner_lifecycle(self, admin_sess):
        cat = admin_sess.post(f"{API}/admin/categories", json={
            "name": f"TEST Cat {uuid.uuid4().hex[:5]}", "group": "miniaturas",
        })
        assert cat.status_code == 200
        cid = cat.json()["id"]
        admin_sess.delete(f"{API}/admin/categories/{cid}")

        br = admin_sess.post(f"{API}/admin/brands", json={
            "name": f"TEST Brand {uuid.uuid4().hex[:5]}",
        })
        assert br.status_code == 200
        bid = br.json()["id"]
        admin_sess.delete(f"{API}/admin/brands/{bid}")

        bn = admin_sess.post(f"{API}/admin/banners", json={
            "title": "TEST Banner", "image": "https://x/y.jpg", "position": 99, "active": True,
        })
        assert bn.status_code == 200
        bnid = bn.json()["id"]
        d = admin_sess.delete(f"{API}/admin/banners/{bnid}")
        assert d.status_code == 200

    def test_update_order_status(self, admin_sess):
        orders = admin_sess.get(f"{API}/admin/orders").json()
        if not orders:
            pytest.skip("no orders yet")
        oid = orders[0]["id"]
        r = admin_sess.put(f"{API}/admin/orders/{oid}/status", json={"status": "enviado"})
        assert r.status_code == 200
        assert r.json()["status"] == "enviado"
