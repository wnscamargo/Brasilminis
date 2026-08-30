from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Brand, Category, Product
from app.utils import to_dict

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/categories")
def list_categories(group: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Category)
    if group:
        q = q.filter(Category.group == group)
    return [to_dict(c) for c in q.order_by(Category.name.asc()).all()]


@router.get("/categories/{slug}")
def get_category(slug: str, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return to_dict(cat)


@router.get("/brands")
def list_brands(db: Session = Depends(get_db)):
    return [to_dict(b) for b in db.query(Brand).order_by(Brand.name.asc()).all()]


@router.get("/brands/{slug}")
def get_brand(slug: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.slug == slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Marca não encontrada")
    return to_dict(brand)


@router.get("/products")
def list_products(
    category: Optional[str] = None,
    group: Optional[str] = None,
    brand: Optional[str] = None,
    badge: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    on_sale: Optional[bool] = None,
    sort: str = "recent",
    page: int = 1,
    limit: int = 24,
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.is_active.is_(True))
    if category:
        q = q.filter(Product.category == category)
    if group:
        q = q.filter(Product.group == group)
    if brand:
        q = q.filter(Product.brand == brand)
    if badge:
        q = q.filter(Product.badges.contains([badge]))
    if featured is not None:
        q = q.filter(Product.featured.is_(featured))
    if on_sale:
        q = q.filter(Product.compare_at_price.isnot(None), Product.compare_at_price > 0)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(
            Product.name.ilike(like),
            Product.description.ilike(like),
            Product.brand.ilike(like),
            Product.category.ilike(like),
        ))

    sort_map = {
        "recent": Product.created_at.desc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "name": Product.name.asc(),
        "rating": Product.rating.desc(),
    }
    order_by = sort_map.get(sort, Product.created_at.desc())

    total = q.count()
    items = q.order_by(order_by).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "page": page, "limit": limit, "items": [to_dict(p) for p in items]}


@router.get("/products/{slug}")
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        product = db.get(Product, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return to_dict(product)


@router.get("/products/{slug}/related")
def related_products(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        return []
    q = db.query(Product).filter(
        Product.is_active.is_(True),
        Product.id != product.id,
        or_(Product.category == product.category, Product.brand == product.brand),
    )
    return [to_dict(p) for p in q.limit(8).all()]
