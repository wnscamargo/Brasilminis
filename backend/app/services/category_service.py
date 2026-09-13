import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Category, Product
from app.utils import slugify, to_dict

MAX_DEPTH = 2  # Categoria -> Subcategoria (arquitetura preparada para mais níveis)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _serialize(c: Category) -> dict:
    return to_dict(c)


def build_tree(db: Session, only_active: bool = False) -> list:
    """Retorna a árvore de categorias (2 níveis) com contagem de produtos ATIVOS."""
    q = db.query(Category)
    if only_active:
        q = q.filter(Category.is_active.is_(True))
    cats = q.order_by(Category.sort_order.asc(), Category.name.asc()).all()

    # Produtos ATIVOS (id + vínculos) para contagem sem duplicação.
    rows = db.query(
        Product.id, Product.main_category_id, Product.subcategory_id, Product.group, Product.category
    ).filter(Product.is_active.is_(True)).all()

    by_id = {c.id: c for c in cats}
    roots = []
    children_map: dict = {}
    for c in cats:
        if c.parent_id and c.parent_id in by_id:
            children_map.setdefault(c.parent_id, []).append(c)
        elif c.parent_id is None:
            roots.append(c)

    def _sub_ids(cat: Category) -> set:
        s = set()
        for pid, main_id, sub_id, grp, cat_slug in rows:
            if sub_id == cat.id or (cat_slug and cat_slug == cat.slug):
                s.add(pid)
        return s

    def _root_ids(cat: Category, child_slugs: set, child_ids: set) -> set:
        s = set()
        for pid, main_id, sub_id, grp, cat_slug in rows:
            if (
                main_id == cat.id
                or (grp and grp == cat.slug)
                or (cat_slug and cat_slug == cat.slug)
                or (sub_id in child_ids)
                or (cat_slug and cat_slug in child_slugs)
            ):
                s.add(pid)
        return s

    def node(c: Category, children: list, count: int) -> dict:
        d = _serialize(c)
        d["product_count"] = count
        d["children"] = children
        return d

    tree = []
    for root in roots:
        kids_cats = sorted(children_map.get(root.id, []), key=lambda x: (x.sort_order, x.name))
        kids = [node(child, [], len(_sub_ids(child))) for child in kids_cats]
        child_ids = {c.id for c in kids_cats}
        child_slugs = {c.slug for c in kids_cats}
        tree.append(node(root, kids, len(_root_ids(root, child_slugs, child_ids))))
    return tree


def _unique_slug(db: Session, name: str, provided: str | None, ignore_id: str | None = None) -> str:
    slug = provided or slugify(name)
    q = db.query(Category).filter(Category.slug == slug)
    if ignore_id:
        q = q.filter(Category.id != ignore_id)
    if q.first():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    return slug


def _validate_parent(db: Session, parent_id: str | None, self_id: str | None = None):
    if parent_id is None:
        return None
    if parent_id == self_id:
        raise HTTPException(status_code=400, detail="Uma categoria não pode ser pai de si mesma.")
    parent = db.get(Category, parent_id)
    if not parent:
        raise HTTPException(status_code=400, detail="Categoria pai não encontrada.")
    # Impede exceder a profundidade (parent não pode ser uma subcategoria => 2 níveis).
    if parent.parent_id is not None:
        raise HTTPException(status_code=400, detail="Só é permitido 2 níveis (categoria → subcategoria).")
    # Impede que uma categoria que já possui filhos vire subcategoria (evita ciclos/estrutura inválida).
    if self_id:
        has_children = db.query(Category).filter(Category.parent_id == self_id).first()
        if has_children:
            raise HTTPException(
                status_code=400,
                detail="Esta categoria possui subcategorias e não pode virar subcategoria.",
            )
    return parent


def create_category(db: Session, data: dict) -> dict:
    parent_id = data.get("parent_id")
    _validate_parent(db, parent_id)
    slug = _unique_slug(db, data["name"], data.get("slug"))
    parent = db.get(Category, parent_id) if parent_id else None
    group = data.get("group") or (parent.group if parent else slug)
    cat = Category(
        id=str(uuid.uuid4()),
        name=data["name"],
        slug=slug,
        parent_id=parent_id,
        group=group,
        is_active=data.get("is_active", True),
        sort_order=data.get("sort_order", 0),
        image=data.get("image", ""),
        icon=data.get("icon", ""),
        show_on_home=bool(data.get("show_on_home", False)),
        featured=bool(data.get("featured", False)),
        description=data.get("description", ""),
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return _serialize(cat)


def update_category(db: Session, category_id: str, data: dict) -> dict:
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    new_parent = data.get("parent_id", cat.parent_id)
    if new_parent != cat.parent_id:
        _validate_parent(db, new_parent, self_id=cat.id)
        cat.parent_id = new_parent
        parent = db.get(Category, new_parent) if new_parent else None
        cat.group = parent.group if parent else cat.slug

    if data.get("name"):
        cat.name = data["name"]
    if "is_active" in data and data["is_active"] is not None:
        cat.is_active = data["is_active"]
    if "sort_order" in data and data["sort_order"] is not None:
        cat.sort_order = data["sort_order"]
    if "image" in data and data["image"] is not None:
        cat.image = data["image"]
    if "icon" in data and data["icon"] is not None:
        cat.icon = data["icon"]
    if "show_on_home" in data and data["show_on_home"] is not None:
        cat.show_on_home = bool(data["show_on_home"])
    if "featured" in data and data["featured"] is not None:
        cat.featured = bool(data["featured"])
    if "description" in data and data["description"] is not None:
        cat.description = data["description"]
    if data.get("group"):
        cat.group = data["group"]
    cat.updated_at = _now()
    db.commit()
    db.refresh(cat)
    return _serialize(cat)


def delete_category(db: Session, category_id: str) -> dict:
    cat = db.get(Category, category_id)
    if not cat:
        return {"message": "Categoria removida"}
    if db.query(Category).filter(Category.parent_id == cat.id).first():
        raise HTTPException(
            status_code=400,
            detail="Remova ou mova as subcategorias antes de excluir esta categoria.",
        )
    db.delete(cat)
    db.commit()
    return {"message": "Categoria removida"}


def reorder(db: Session, ids: list) -> dict:
    for index, cid in enumerate(ids):
        cat = db.get(Category, cid)
        if cat:
            cat.sort_order = index
            cat.updated_at = _now()
    db.commit()
    return {"message": "Ordenação atualizada"}
