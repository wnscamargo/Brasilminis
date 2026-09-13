"""Catálogo: Home dinâmica, contagem ativa, badges CRUD, produtos por categoria."""
import os, uuid, requests, pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
A = ("admin@brasilminis.com", "Admin@2025")


@pytest.fixture(scope="module")
def adm():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"email": A[0], "password": A[1]}, timeout=30)
    assert r.status_code == 200
    return s


def _mkcat(adm, name, parent_id=None, show_on_home=False, active=True):
    r = adm.post(f"{BASE}/api/admin/categories", json={"name": name, "parent_id": parent_id, "is_active": active, "show_on_home": show_on_home}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


class TestHomeCategories:
    def test_created_home_category_appears(self, adm):
        c = _mkcat(adm, f"HomeCat {uuid.uuid4().hex[:5]}", show_on_home=True)
        hc = requests.get(f"{BASE}/api/home-categories", timeout=30).json()
        assert any(x["id"] == c["id"] for x in hc)

    def test_not_on_home_hidden(self, adm):
        c = _mkcat(adm, f"NoHome {uuid.uuid4().hex[:5]}", show_on_home=False)
        hc = requests.get(f"{BASE}/api/home-categories", timeout=30).json()
        assert not any(x["id"] == c["id"] for x in hc)

    def test_inactive_hidden(self, adm):
        c = _mkcat(adm, f"Inactive {uuid.uuid4().hex[:5]}", show_on_home=True, active=False)
        hc = requests.get(f"{BASE}/api/home-categories", timeout=30).json()
        assert not any(x["id"] == c["id"] for x in hc)

    def test_rename_reflects(self, adm):
        c = _mkcat(adm, f"Old {uuid.uuid4().hex[:5]}", show_on_home=True)
        newname = f"New {uuid.uuid4().hex[:5]}"
        adm.put(f"{BASE}/api/admin/categories/{c['id']}", json={"name": newname}, timeout=30)
        hc = requests.get(f"{BASE}/api/home-categories", timeout=30).json()
        assert any(x["id"] == c["id"] and x["name"] == newname for x in hc)

    def test_empty_category_count_zero(self, adm):
        c = _mkcat(adm, f"Empty {uuid.uuid4().hex[:5]}", show_on_home=True)
        hc = requests.get(f"{BASE}/api/home-categories", timeout=30).json()
        node = next(x for x in hc if x["id"] == c["id"])
        assert node["product_count"] == 0


class TestActiveCount:
    def test_count_only_active(self, adm):
        main = _mkcat(adm, f"CntMain {uuid.uuid4().hex[:5]}", show_on_home=True)
        sub = _mkcat(adm, f"CntSub {uuid.uuid4().hex[:5]}", parent_id=main["id"])
        # 2 products: 1 active, 1 inactive
        for active in (True, False):
            adm.post(f"{BASE}/api/admin/products", json={
                "name": f"P {uuid.uuid4().hex[:5]}", "price": 10, "stock": 5,
                "main_category_id": main["id"], "subcategory_id": sub["id"],
                "is_active": active, "images": [], "badges": [], "specs": {},
            }, timeout=30)
        tree = requests.get(f"{BASE}/api/categories?tree=true", timeout=30).json()
        node = next(x for x in tree if x["id"] == main["id"])
        subnode = next(s for s in node["children"] if s["id"] == sub["id"])
        assert subnode["product_count"] == 1
        assert node["product_count"] == 1


class TestBadges:
    def test_crud_and_delete_block(self, adm):
        text = f"BADGE{uuid.uuid4().hex[:5].upper()}"
        r = adm.post(f"{BASE}/api/admin/badges", json={"text": text, "bg_color": "#000", "text_color": "#fff"}, timeout=30)
        assert r.status_code == 200
        bid = r.json()["id"]
        # edit
        assert adm.put(f"{BASE}/api/admin/badges/{bid}", json={"text": text, "bg_color": "#111", "text_color": "#fff", "active": False}, timeout=30).status_code == 200
        assert any(b["id"] == bid for b in requests.get(f"{BASE}/api/badges", timeout=30).json()) is False  # inactive not public
        # reactivate + associate to a product
        adm.put(f"{BASE}/api/admin/badges/{bid}", json={"text": text, "bg_color": "#111", "text_color": "#fff", "active": True}, timeout=30)
        pr = adm.post(f"{BASE}/api/admin/products", json={"name": f"BP {uuid.uuid4().hex[:5]}", "price": 5, "stock": 1, "badges": [text], "images": [], "specs": {}}, timeout=30)
        assert pr.status_code == 200
        # delete blocked while in use
        assert adm.delete(f"{BASE}/api/admin/badges/{bid}", timeout=30).status_code == 400

    def test_rbac(self):
        s = requests.Session()
        assert s.get(f"{BASE}/api/admin/badges", timeout=30).status_code == 401


class TestCatalogProducts:
    def test_filter_by_subcategory(self, adm):
        main = _mkcat(adm, f"FMain {uuid.uuid4().hex[:5]}")
        sub1 = _mkcat(adm, f"FSub1 {uuid.uuid4().hex[:5]}", parent_id=main["id"])
        sub2 = _mkcat(adm, f"FSub2 {uuid.uuid4().hex[:5]}", parent_id=main["id"])
        p1 = adm.post(f"{BASE}/api/admin/products", json={"name": f"S1 {uuid.uuid4().hex[:5]}", "price": 10, "stock": 3, "main_category_id": main["id"], "subcategory_id": sub1["id"], "images": [], "badges": [], "specs": {}}, timeout=30).json()
        adm.post(f"{BASE}/api/admin/products", json={"name": f"S2 {uuid.uuid4().hex[:5]}", "price": 10, "stock": 3, "main_category_id": main["id"], "subcategory_id": sub2["id"], "images": [], "badges": [], "specs": {}}, timeout=30)
        d = adm.get(f"{BASE}/api/admin/catalog/products?category={sub1['slug']}", timeout=30).json()
        ids = [x["id"] for x in d["items"]]
        assert p1["id"] in ids
        assert d["total"] == 1  # only sub1's product
