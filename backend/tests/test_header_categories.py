"""Contrato de dados do header dinâmico (categorias públicas).

Valida a árvore que alimenta o menu público: somente raízes no topo, filhos
aninhados, inativos excluídos, sem subcategoria duplicada no nível principal,
ordenação por sort_order do Admin. Fonte da verdade = Admin/backend (dinâmico).
"""
import os
import uuid

import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
A = ("admin@brasilminis.com", "Admin@2025")


def _adm():
    s = requests.Session()
    assert s.post(f"{BASE}/api/auth/login", json={"email": A[0], "password": A[1]}, timeout=30).status_code == 200
    return s


def _tree():
    return requests.get(f"{BASE}/api/categories?tree=true", timeout=30).json()


class TestHeaderTree:
    def test_only_roots_at_top_level(self):
        # A árvore pública já vem aninhada: itens de topo não têm parent_id.
        for node in _tree():
            assert node.get("parent_id") in (None, "", node.get("parent_id") if False else None)

    def test_children_nested_not_duplicated_at_top(self):
        tree = _tree()
        top_ids = {n["id"] for n in tree}
        child_ids = set()
        for n in tree:
            for c in n.get("children", []):
                child_ids.add(c["id"])
        # nenhum filho aparece também no nível principal
        assert top_ids.isdisjoint(child_ids)

    def test_inactive_excluded(self):
        adm = _adm()
        c = adm.post(f"{BASE}/api/admin/categories",
                     json={"name": f"HDR Inactive {uuid.uuid4().hex[:6]}", "is_active": False}, timeout=30).json()
        try:
            ids = {n["id"] for n in _tree()}
            assert c["id"] not in ids
        finally:
            adm.delete(f"{BASE}/api/admin/categories/{c['id']}", timeout=30)

    def test_root_with_children_has_dropdown_shape(self):
        # Ao menos uma raiz canônica possui filhos (permite dropdown no header).
        tree = _tree()
        assert any(len(n.get("children", [])) > 0 for n in tree)

    def test_ordering_follows_sort_order(self):
        tree = _tree()
        orders = [n.get("sort_order", 0) for n in tree]
        assert orders == sorted(orders)

    def test_created_root_appears_and_cleanup(self):
        adm = _adm()
        name = f"HDR Root {uuid.uuid4().hex[:6]}"
        c = adm.post(f"{BASE}/api/admin/categories", json={"name": name, "is_active": True}, timeout=30).json()
        try:
            assert any(n["id"] == c["id"] for n in _tree())   # dinâmico: vem do Admin
        finally:
            r = adm.delete(f"{BASE}/api/admin/categories/{c['id']}", timeout=30)
            assert r.status_code in (200, 204)
            assert not any(n["id"] == c["id"] for n in _tree())  # some após exclusão
