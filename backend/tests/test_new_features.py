"""Backend regression for the new structural evolution:
- Hierarchical categories (parent_id, 2 levels)
- Product cost_price + main_category_id/subcategory_id
- Product cost history
- Order CMV snapshots (COGS frozen at sale)
- Analytics /admin/analytics with all periods
- Product images (URL + upload) with Pillow validation
- RBAC on all admin endpoints
- Public endpoints must NEVER expose cost_price
"""
import io
import os
import uuid

import pytest
import requests
from .test_helpers import preserve_auth_cookie, valid_cpf
from PIL import Image

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


# -------- Fixtures --------
@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    preserve_auth_cookie(s, r)
    return s


@pytest.fixture(scope="module")
def customer_session():
    email = f"TEST_{uuid.uuid4().hex[:8]}@example.com"
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Cliente CMV", "email": email, "password": "senha123", "cpf": valid_cpf(), "newsletter": False,
    }, timeout=30)
    assert r.status_code == 200, r.text
    preserve_auth_cookie(s, r)
    return s


def _png_bytes(w=64, h=64, color=(120, 90, 200, 255)):
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def _jpeg_bytes(w=64, h=64):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (200, 50, 50)).save(buf, format="JPEG")
    return buf.getvalue()


def _webp_bytes(w=64, h=64):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (50, 200, 100)).save(buf, format="WEBP")
    return buf.getvalue()


# =====================================================================
# Categories: hierarchy, tree, cycles / depth, move
# =====================================================================
class TestCategoriesHierarchy:
    def test_create_main_and_subcategory_and_tree(self, admin_session):
        main_name = f"TEST Main {uuid.uuid4().hex[:6]}"
        r = admin_session.post(f"{BASE_URL}/api/admin/categories",
                               json={"name": main_name, "is_active": True}, timeout=15)
        assert r.status_code == 200, r.text
        main = r.json()
        assert main["parent_id"] is None
        pytest.MAIN_CAT_ID = main["id"]

        sub_name = f"TEST Sub {uuid.uuid4().hex[:6]}"
        rs = admin_session.post(f"{BASE_URL}/api/admin/categories",
                                json={"name": sub_name, "parent_id": main["id"]}, timeout=15)
        assert rs.status_code == 200, rs.text
        sub = rs.json()
        assert sub["parent_id"] == main["id"]
        pytest.SUB_CAT_ID = sub["id"]

        # tree endpoint
        t = admin_session.get(f"{BASE_URL}/api/admin/categories/tree", timeout=15)
        assert t.status_code == 200
        tree = t.json()
        node = next((c for c in tree if c["id"] == main["id"]), None)
        assert node is not None
        assert "children" in node
        assert any(ch["id"] == sub["id"] for ch in node["children"])
        assert "product_count" in node

    def test_depth_limit(self, admin_session):
        # 3rd level must be rejected
        r = admin_session.post(f"{BASE_URL}/api/admin/categories", json={
            "name": f"TEST 3rd {uuid.uuid4().hex[:6]}", "parent_id": pytest.SUB_CAT_ID
        }, timeout=15)
        assert r.status_code == 400

    def test_cannot_convert_parent_with_children_into_sub(self, admin_session):
        # main category has children — try setting parent_id on it → 400
        main_name2 = f"TEST Main2 {uuid.uuid4().hex[:6]}"
        r = admin_session.post(f"{BASE_URL}/api/admin/categories",
                               json={"name": main_name2}, timeout=15)
        another_main_id = r.json()["id"]
        pytest.ANOTHER_MAIN_ID = another_main_id

        r = admin_session.put(f"{BASE_URL}/api/admin/categories/{pytest.MAIN_CAT_ID}",
                              json={"name": "x", "parent_id": another_main_id}, timeout=15)
        assert r.status_code == 400

    def test_move_subcategory(self, admin_session):
        r = admin_session.put(f"{BASE_URL}/api/admin/categories/{pytest.SUB_CAT_ID}", json={
            "name": "TEST Sub Moved", "parent_id": pytest.ANOTHER_MAIN_ID
        }, timeout=15)
        assert r.status_code == 200
        assert r.json()["parent_id"] == pytest.ANOTHER_MAIN_ID


# =====================================================================
# RBAC: customer must be forbidden on all admin structural endpoints
# =====================================================================
class TestRBACForNewEndpoints:
    @pytest.mark.parametrize("method,path", [
        ("get", "/api/admin/categories/tree"),
        ("post", "/api/admin/categories"),
        ("get", "/api/admin/analytics"),
        ("get", "/api/admin/products"),
    ])
    def test_customer_forbidden(self, customer_session, method, path):
        fn = getattr(customer_session, method)
        kwargs = {"timeout": 15}
        if method == "post":
            kwargs["json"] = {"name": "x"}
        r = fn(f"{BASE_URL}{path}", **kwargs)
        assert r.status_code == 403, f"{method} {path} -> {r.status_code}"


# =====================================================================
# Products with cost / main+sub category derivation
# =====================================================================
@pytest.fixture(scope="module")
def cost_product(admin_session):
    # Create using an existing main+sub pair.
    tree = admin_session.get(f"{BASE_URL}/api/admin/categories/tree", timeout=15).json()
    main = next((c for c in tree if c.get("children")), None)
    assert main, "Expected at least one main category with children in seed"
    sub = main["children"][0]

    name = f"TEST Cost Prod {uuid.uuid4().hex[:6]}"
    r = admin_session.post(f"{BASE_URL}/api/admin/products", json={
        "name": name, "description": "cmv", "price": 100.0, "cost_price": 40.0,
        "main_category_id": main["id"], "subcategory_id": sub["id"],
        "stock": 50, "images": [], "badges": [], "specs": {},
    }, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cost_price"] == 40.0
    assert body["main_category_id"] == main["id"]
    assert body["subcategory_id"] == sub["id"]
    assert body["category"] == sub["slug"]
    assert body["group"] == main["slug"]
    return body


class TestProductWithCost:
    def test_reject_negative_cost(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/admin/products", json={
            "name": f"TEST neg {uuid.uuid4().hex[:6]}", "description": "", "price": 10,
            "cost_price": -1, "stock": 1, "images": [], "badges": [], "specs": {},
        }, timeout=15)
        assert r.status_code == 422

    def test_cost_hidden_public_list(self, cost_product):
        r = requests.get(f"{BASE_URL}/api/products?search=TEST+Cost&limit=50", timeout=15)
        assert r.status_code == 200
        items = r.json()["items"]
        for it in items:
            assert "cost_price" not in it, f"cost_price leaked in {it.get('name')}"

    def test_cost_hidden_public_detail(self, cost_product):
        r = requests.get(f"{BASE_URL}/api/products/{cost_product['slug']}", timeout=15)
        assert r.status_code == 200
        assert "cost_price" not in r.json()

    def test_cost_hidden_public_related(self, cost_product):
        r = requests.get(f"{BASE_URL}/api/products/{cost_product['slug']}/related", timeout=15)
        assert r.status_code == 200
        for it in r.json():
            assert "cost_price" not in it

    def test_cost_history_on_update(self, admin_session, cost_product):
        pid = cost_product["id"]
        # bump cost 40 -> 50
        r = admin_session.put(f"{BASE_URL}/api/admin/products/{pid}", json={
            **{k: cost_product[k] for k in ("name", "description", "price", "stock")},
            "cost_price": 50.0,
            "main_category_id": cost_product["main_category_id"],
            "subcategory_id": cost_product["subcategory_id"],
            "images": [], "badges": [], "specs": {},
        }, timeout=15)
        assert r.status_code == 200
        assert r.json()["cost_price"] == 50.0
        h = admin_session.get(f"{BASE_URL}/api/admin/products/{pid}/cost-history", timeout=15)
        assert h.status_code == 200
        hist = h.json()
        # Should contain at least the initial (None->40) and the (40->50) rows.
        assert len(hist) >= 2
        latest = hist[0]
        assert float(latest["new_cost"]) == 50.0
        assert float(latest["old_cost"]) == 40.0
        # Restore back to 40 for CMV test
        admin_session.put(f"{BASE_URL}/api/admin/products/{pid}", json={
            **{k: cost_product[k] for k in ("name", "description", "price", "stock")},
            "cost_price": 40.0,
            "main_category_id": cost_product["main_category_id"],
            "subcategory_id": cost_product["subcategory_id"],
            "images": [], "badges": [], "specs": {},
        }, timeout=15)


# =====================================================================
# CMV snapshot in orders (critical) + cost-less product
# =====================================================================
@pytest.fixture(scope="module")
def no_cost_product(admin_session):
    r = admin_session.post(f"{BASE_URL}/api/admin/products", json={
        "name": f"TEST NoCost {uuid.uuid4().hex[:6]}", "description": "", "price": 30.0,
        "cost_price": None, "stock": 20, "images": [], "badges": [], "specs": {},
    }, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


class TestOrderCMVSnapshot:
    def test_order_freezes_cost_with_cost(self, admin_session, customer_session, cost_product):
        pid = cost_product["id"]
        r = customer_session.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": pid, "quantity": 3}],
            "shipping_method": "standard", "payment_method": "pix",
        }, timeout=30)
        assert r.status_code == 200, r.text
        order = r.json()
        pytest.CMV_ORDER_ID = order["id"]
        it = next(i for i in order["items"] if i["product_id"] == pid)
        assert it["unit_cost_snapshot"] == 40.0
        assert it["line_revenue"] == 300.0
        assert it["line_cogs"] == 120.0
        assert it["line_gross_profit"] == 180.0
        assert it["has_cost"] is True

    def test_changing_cost_does_not_alter_old_order(self, admin_session, customer_session, cost_product):
        pid = cost_product["id"]
        # Bump cost to 60
        upd = admin_session.put(f"{BASE_URL}/api/admin/products/{pid}", json={
            "name": cost_product["name"], "description": "", "price": 100.0,
            "cost_price": 60.0,
            "main_category_id": cost_product["main_category_id"],
            "subcategory_id": cost_product["subcategory_id"],
            "stock": 50, "images": [], "badges": [], "specs": {},
        }, timeout=15)
        assert upd.status_code == 200
        # Fetch the OLD order → snapshots must be intact
        orders = customer_session.get(f"{BASE_URL}/api/orders", timeout=15).json()
        old = next(o for o in orders if o["id"] == pytest.CMV_ORDER_ID)
        it = next(i for i in old["items"] if i["product_id"] == pid)
        assert it["unit_cost_snapshot"] == 40.0
        assert it["line_cogs"] == 120.0

    def test_order_no_cost_product(self, customer_session, no_cost_product):
        r = customer_session.post(f"{BASE_URL}/api/orders", json={
            "items": [{"product_id": no_cost_product["id"], "quantity": 2}],
            "shipping_method": "standard", "payment_method": "pix",
        }, timeout=30)
        assert r.status_code == 200, r.text
        it = r.json()["items"][0]
        assert it["unit_cost_snapshot"] is None
        assert it["line_cogs"] is None
        assert it["has_cost"] is False


# =====================================================================
# Analytics dashboard
# =====================================================================
class TestAnalytics:
    EXPECTED_KEYS = {
        "revenue_gross", "discounts", "shipping_charged", "net_revenue",
        "cogs", "gross_profit", "gross_margin_pct", "avg_ticket",
        "orders_count", "products_sold",
        "items_without_cost_qty", "products_without_cost_catalog",
        "top_products_revenue", "top_products_profit",
        "top_categories_revenue", "top_subcategories_revenue",
        "low_margin_products", "best_sellers", "series",
    }

    @pytest.mark.parametrize("period", ["today", "7d", "30d", "this_month", "last_month"])
    def test_periods_return_all_keys(self, admin_session, period):
        r = admin_session.get(f"{BASE_URL}/api/admin/analytics?period={period}", timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        missing = self.EXPECTED_KEYS - set(body.keys())
        assert not missing, f"Missing keys for period={period}: {missing}"

    def test_custom_period(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/analytics",
                              params={"period": "custom", "start": "2025-01-01", "end": "2030-01-01"},
                              timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert "period" in body and body["period"]["key"] == "custom"

    def test_cmv_reflected_after_orders(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/analytics?period=30d", timeout=20)
        assert r.status_code == 200
        body = r.json()
        # After the CMV tests we should have orders with cost and orders without cost.
        assert body["orders_count"] >= 2
        assert body["cogs"] > 0
        assert body["items_without_cost_qty"] >= 2  # from no-cost order (qty=2)


# =====================================================================
# Product images: URL, upload (jpeg/png/webp), invalid rejection, primary/reorder/delete
# =====================================================================
@pytest.fixture(scope="module")
def image_product(admin_session):
    r = admin_session.post(f"{BASE_URL}/api/admin/products", json={
        "name": f"TEST Img Prod {uuid.uuid4().hex[:6]}", "description": "", "price": 15.0,
        "cost_price": 5.0, "stock": 10, "images": [], "badges": [], "specs": {},
    }, timeout=15)
    assert r.status_code == 200
    return r.json()


class TestProductImages:
    def test_add_url_image_becomes_primary(self, admin_session, image_product):
        pid = image_product["id"]
        r = admin_session.post(f"{BASE_URL}/api/admin/products/{pid}/images", json={
            "url": "https://example.com/one.jpg", "is_primary": False,
        }, timeout=15)
        assert r.status_code == 200
        assert r.json()["is_primary"] is True  # first becomes primary

    def test_upload_png(self, admin_session, image_product):
        pid = image_product["id"]
        r = admin_session.post(f"{BASE_URL}/api/admin/products/{pid}/images/upload",
                               files={"file": ("a.png", _png_bytes(), "image/png")}, timeout=30)
        assert r.status_code == 200, r.text
        url = r.json()["url"]
        assert url.startswith("/api/uploads/products/")
        # Publicly accessible
        pub = requests.get(f"{BASE_URL}{url}", timeout=15)
        assert pub.status_code == 200
        pytest.UPLOADED_IMG_ID = r.json()["id"]

    def test_upload_jpeg(self, admin_session, image_product):
        pid = image_product["id"]
        r = admin_session.post(f"{BASE_URL}/api/admin/products/{pid}/images/upload",
                               files={"file": ("b.jpg", _jpeg_bytes(), "image/jpeg")}, timeout=30)
        assert r.status_code == 200, r.text

    def test_upload_webp(self, admin_session, image_product):
        pid = image_product["id"]
        r = admin_session.post(f"{BASE_URL}/api/admin/products/{pid}/images/upload",
                               files={"file": ("c.webp", _webp_bytes(), "image/webp")}, timeout=30)
        assert r.status_code == 200, r.text

    def test_reject_non_image_bytes(self, admin_session, image_product):
        pid = image_product["id"]
        r = admin_session.post(f"{BASE_URL}/api/admin/products/{pid}/images/upload",
                               files={"file": ("x.png", b"not really an image", "image/png")}, timeout=15)
        assert r.status_code == 400

    def test_reject_oversized(self, admin_session, image_product):
        pid = image_product["id"]
        # 8.1 MB
        big = b"\x00" * (8 * 1024 * 1024 + 1024)
        r = admin_session.post(f"{BASE_URL}/api/admin/products/{pid}/images/upload",
                               files={"file": ("big.png", big, "image/png")}, timeout=30)
        assert r.status_code == 400

    def test_set_primary_and_delete_and_product_intact(self, admin_session, image_product):
        pid = image_product["id"]
        imgs = admin_session.get(f"{BASE_URL}/api/admin/products/{pid}/images", timeout=15).json()
        assert len(imgs) >= 3
        # Set primary to a different image
        target = next(i for i in imgs if not i["is_primary"])
        r = admin_session.put(f"{BASE_URL}/api/admin/products/{pid}/images/{target['id']}/primary",
                              timeout=15)
        assert r.status_code == 200
        new_primary = next(i for i in r.json() if i["is_primary"])
        assert new_primary["id"] == target["id"]

        # Reorder
        ids = [i["id"] for i in r.json()][::-1]
        rr = admin_session.put(f"{BASE_URL}/api/admin/products/{pid}/images/reorder",
                               json={"ids": ids}, timeout=15)
        assert rr.status_code == 200

        # Delete one image
        del_id = ids[-1]
        d = admin_session.delete(f"{BASE_URL}/api/admin/products/{pid}/images/{del_id}",
                                 timeout=15)
        assert d.status_code == 200
        # Product still accessible + images synced
        slug = image_product["slug"]
        prod = requests.get(f"{BASE_URL}/api/products/{slug}", timeout=15).json()
        assert isinstance(prod["images"], list)
        assert len(prod["images"]) >= 1
