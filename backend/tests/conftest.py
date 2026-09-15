"""Higiene de testes (estrutural): remove categorias/produtos de teste vazados.

Vários testes criam categorias via API do Admin (nomes com sufixo aleatório).
Sem limpeza, elas se acumulam no banco do preview e poluem o header público.
Este teardown de sessão remove tudo que NÃO faz parte do conjunto canônico do
seed (GROUP_ORDER + subcategorias do seed). Regra estrutural, não por nome.
"""
import pytest


@pytest.fixture(scope="session", autouse=True)
def _purge_leaked_test_categories():
    yield
    try:
        from app.db.session import SessionLocal
        from app.models import Category, Product
        from app.seed import GROUP_ORDER, CATEGORIES, slugify
        canonical = set(GROUP_ORDER) | {slugify(name) for (name, _g, _d) in CATEGORIES}
        db = SessionLocal()
        try:
            remove = [c for c in db.query(Category).all() if c.slug not in canonical]
            remove_ids = {c.id for c in remove}
            if remove_ids:
                for p in db.query(Product).all():
                    if p.main_category_id in remove_ids or p.subcategory_id in remove_ids:
                        db.delete(p)
                for c in [c for c in remove if c.parent_id is not None]:
                    db.delete(c)
                db.commit()
                for c in [c for c in remove if c.parent_id is None]:
                    db.delete(c)
                db.commit()
        finally:
            db.close()
    except Exception:
        pass
