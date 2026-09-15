"""Higiene de testes (estrutural e SEGURA): remove apenas as categorias/produtos
que FORAM CRIADOS DURANTE ESTA sessão de teste.

Motivação: vários testes criam categorias via API do Admin (nomes com sufixo
aleatório). Sem limpeza elas se acumulam no banco e poluem o header público.

SEGURANÇA (produção): NÃO faz purge cego. Tira um "snapshot" dos IDs existentes
ANTES da sessão e, no teardown, remove somente os IDs que surgiram DURANTE a
sessão e que não pertencem ao conjunto canônico do seed. Dados pré-existentes
(inclusive categorias criadas pelo Admin) NUNCA são tocados. Não deve ser usado
como rotina de limpeza de produção.
"""
import pytest


def _snapshot_ids():
    try:
        from app.db.session import SessionLocal
        from app.models import Category
        db = SessionLocal()
        try:
            return {row[0] for row in db.query(Category.id).all()}
        finally:
            db.close()
    except Exception:
        return None


@pytest.fixture(scope="session", autouse=True)
def _purge_only_session_created_categories():
    baseline = _snapshot_ids()  # IDs que já existiam antes dos testes
    yield
    if baseline is None:
        return
    try:
        from app.db.session import SessionLocal
        from app.models import Category, Product
        from app.seed import GROUP_ORDER, CATEGORIES, slugify
        canonical = set(GROUP_ORDER) | {slugify(name) for (name, _g, _d) in CATEGORIES}
        db = SessionLocal()
        try:
            # remove SOMENTE o que nasceu nesta sessão e não é canônico
            created = [c for c in db.query(Category).all()
                       if c.id not in baseline and c.slug not in canonical]
            ids = {c.id for c in created}
            if not ids:
                return
            for p in db.query(Product).all():
                if p.main_category_id in ids or p.subcategory_id in ids:
                    db.delete(p)
            for c in [c for c in created if c.parent_id is not None]:
                db.delete(c)
            db.commit()
            for c in [c for c in created if c.parent_id is None]:
                db.delete(c)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass
