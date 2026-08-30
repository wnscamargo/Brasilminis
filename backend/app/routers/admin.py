import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_db
from app.models import Banner, Brand, Category, Order, Product, User
from app.schemas import BannerInput, BrandInput, CategoryInput, OrderStatusInput, ProductInput
from app.utils import slugify, to_dict

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------- Dashboard ----------------
@router.get("/stats")
def stats(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_customers = db.query(func.count(User.id)).filter(User.role == "customer").scalar() or 0
    low_stock = db.query(func.count(Product.id)).filter(Product.stock <= 5).scalar() or 0

    orders = db.query(Order).all()
    revenue = round(sum((o.total or 0) for o in orders), 2)

    by_day: dict = {}
    for o in orders:
        day = (o.created_at or "")[:10]
        by_day[day] = round(by_day.get(day, 0) + (o.total or 0), 2)
    revenue_series = [{"date": k, "revenue": v} for k, v in sorted(by_day.items())][-7:]

    recent = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "revenue": revenue,
        "low_stock": low_stock,
        "revenue_series": revenue_series,
        "recent_orders": [to_dict(o) for o in recent],
    }


# ---------------- Products ----------------
@router.get("/products")
def admin_list_products(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return [to_dict(p) for p in db.query(Product).order_by(Product.created_at.desc()).all()]


@router.post("/products")
def create_product(payload: ProductInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    data = payload.model_dump()
    pid = str(uuid.uuid4())
    slug = data.get("slug") or slugify(data["name"])
    if db.query(Product).filter(Product.slug == slug).first():
        slug = f"{slug}-{pid[:6]}"
    product = Product(
        id=pid, slug=slug, rating=0, reviews_count=0,
        created_at=datetime.now(timezone.utc).isoformat(),
        **{k: v for k, v in data.items() if k != "slug"},
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return to_dict(product)


@router.put("/products/{product_id}")
def update_product(product_id: str, payload: ProductInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    data = payload.model_dump()
    data["slug"] = data.get("slug") or product.slug or slugify(data["name"])
    for k, v in data.items():
        setattr(product, k, v)
    db.commit()
    db.refresh(product)
    return to_dict(product)


@router.delete("/products/{product_id}")
def delete_product(product_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product:
        db.delete(product)
        db.commit()
    return {"message": "Produto removido"}


# ---------------- Categories ----------------
@router.post("/categories")
def create_category(payload: CategoryInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    data = payload.model_dump()
    slug = data.get("slug") or slugify(data["name"])
    if db.query(Category).filter(Category.slug == slug).first():
        raise HTTPException(status_code=400, detail="Categoria já existe")
    cat = Category(id=str(uuid.uuid4()), **{**data, "slug": slug})
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return to_dict(cat)


@router.put("/categories/{category_id}")
def update_category(category_id: str, payload: CategoryInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    data = payload.model_dump()
    data["slug"] = data.get("slug") or slugify(data["name"])
    for k, v in data.items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return to_dict(cat)


@router.delete("/categories/{category_id}")
def delete_category(category_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    cat = db.get(Category, category_id)
    if cat:
        db.delete(cat)
        db.commit()
    return {"message": "Categoria removida"}


# ---------------- Brands ----------------
@router.post("/brands")
def create_brand(payload: BrandInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    data = payload.model_dump()
    slug = data.get("slug") or slugify(data["name"])
    if db.query(Brand).filter(Brand.slug == slug).first():
        raise HTTPException(status_code=400, detail="Marca já existe")
    brand = Brand(id=str(uuid.uuid4()), **{**data, "slug": slug})
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return to_dict(brand)


@router.put("/brands/{brand_id}")
def update_brand(brand_id: str, payload: BrandInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Marca não encontrada")
    data = payload.model_dump()
    data["slug"] = data.get("slug") or slugify(data["name"])
    for k, v in data.items():
        setattr(brand, k, v)
    db.commit()
    db.refresh(brand)
    return to_dict(brand)


@router.delete("/brands/{brand_id}")
def delete_brand(brand_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    brand = db.get(Brand, brand_id)
    if brand:
        db.delete(brand)
        db.commit()
    return {"message": "Marca removida"}


# ---------------- Orders ----------------
@router.get("/orders")
def admin_list_orders(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return [to_dict(o) for o in db.query(Order).order_by(Order.created_at.desc()).all()]


@router.put("/orders/{order_id}/status")
def update_order_status(order_id: str, payload: OrderStatusInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return to_dict(order)


# ---------------- Customers ----------------
@router.get("/customers")
def admin_list_customers(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role == "customer").order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        orders_count = db.query(func.count(Order.id)).filter(Order.user_id == u.id).scalar() or 0
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone or "",
            "newsletter": bool(u.newsletter),
            "orders_count": orders_count,
            "created_at": u.created_at,
        })
    return result


# ---------------- Banners ----------------
@router.get("/banners")
def admin_list_banners(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return [to_dict(b) for b in db.query(Banner).order_by(Banner.position.asc()).all()]


@router.post("/banners")
def create_banner(payload: BannerInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    banner = Banner(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return to_dict(banner)


@router.put("/banners/{banner_id}")
def update_banner(banner_id: str, payload: BannerInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    banner = db.get(Banner, banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado")
    for k, v in payload.model_dump().items():
        setattr(banner, k, v)
    db.commit()
    db.refresh(banner)
    return to_dict(banner)


@router.delete("/banners/{banner_id}")
def delete_banner(banner_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    banner = db.get(Banner, banner_id)
    if banner:
        db.delete(banner)
        db.commit()
    return {"message": "Banner removido"}
