import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_db
from app.models import (
    Banner,
    Brand,
    Category,
    Order,
    Product,
    ProductCostHistory,
    User,
)
from app.schemas import (
    BannerInput,
    BrandInput,
    CategoryInput,
    CategoryReorderInput,
    ImageReorderInput,
    OrderStatusInput,
    ProductImageUrlInput,
    ProductInput,
)
from app.services import analytics_service, category_service
from app.services import product_image_service as img_service
from app.utils import slugify, to_dict

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _resolve_category_fields(db: Session, data: dict):
    """Deriva category/group (slugs, compat) a partir de main_category_id/subcategory_id."""
    sub_id = data.get("subcategory_id")
    main_id = data.get("main_category_id")
    if sub_id:
        sub = db.get(Category, sub_id)
        if not sub:
            raise HTTPException(status_code=400, detail="Subcategoria inválida")
        data["subcategory_id"] = sub.id
        data["category"] = sub.slug
        parent = db.get(Category, sub.parent_id) if sub.parent_id else None
        data["main_category_id"] = parent.id if parent else main_id
        data["group"] = parent.slug if parent else (sub.group or data.get("group") or "")
    elif main_id:
        main = db.get(Category, main_id)
        if not main:
            raise HTTPException(status_code=400, detail="Categoria inválida")
        data["main_category_id"] = main.id
        data["subcategory_id"] = None
        data["group"] = main.slug
        if not data.get("category"):
            data["category"] = ""
    return data


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


@router.get("/analytics")
def analytics(
    period: str = "30d",
    start: str | None = None,
    end: str | None = None,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return analytics_service.compute(db, period, start, end)


# ---------------- Products ----------------
@router.get("/products")
def admin_list_products(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return [to_dict(p) for p in db.query(Product).order_by(Product.created_at.desc()).all()]


@router.post("/products")
def create_product(payload: ProductInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    data = payload.model_dump()
    _resolve_category_fields(db, data)
    pid = str(uuid.uuid4())
    slug = data.get("slug") or slugify(data["name"])
    if db.query(Product).filter(Product.slug == slug).first():
        slug = f"{slug}-{pid[:6]}"
    initial_images = data.pop("images", []) or []
    cost = data.get("cost_price")
    product = Product(
        id=pid, slug=slug, rating=0, reviews_count=0,
        created_at=datetime.now(timezone.utc).isoformat(),
        images=[],
        **{k: v for k, v in data.items() if k not in ("slug", "images")},
    )
    db.add(product)
    db.flush()
    # Imagens iniciais (URLs) -> product_images + cache denormalizado
    img_service.seed_images_from_urls(db, pid, initial_images)
    db.flush()
    img_service.sync_product_images(db, pid)
    # Histórico de custo inicial (se informado)
    if cost is not None:
        db.add(ProductCostHistory(
            id=str(uuid.uuid4()), product_id=pid, old_cost=None, new_cost=cost,
            changed_by=admin.get("email"), changed_at=datetime.now(timezone.utc).isoformat(),
        ))
    db.commit()
    db.refresh(product)
    return to_dict(product)


@router.put("/products/{product_id}")
def update_product(product_id: str, payload: ProductInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    data = payload.model_dump()
    _resolve_category_fields(db, data)
    data["slug"] = data.get("slug") or product.slug or slugify(data["name"])
    data.pop("images", None)  # imagens são gerenciadas pelos endpoints dedicados

    old_cost = product.cost_price
    new_cost = data.get("cost_price")
    for k, v in data.items():
        setattr(product, k, v)

    # Histórico de custo em qualquer alteração manual do custo
    def _norm(c):
        return None if c is None else round(float(c), 2)
    if _norm(old_cost) != _norm(new_cost):
        db.add(ProductCostHistory(
            id=str(uuid.uuid4()), product_id=product_id,
            old_cost=old_cost, new_cost=new_cost,
            changed_by=admin.get("email"), changed_at=datetime.now(timezone.utc).isoformat(),
        ))
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


@router.get("/products/{product_id}/cost-history")
def product_cost_history(product_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = (
        db.query(ProductCostHistory)
        .filter(ProductCostHistory.product_id == product_id)
        .order_by(ProductCostHistory.changed_at.desc())
        .all()
    )
    return [to_dict(r) for r in rows]


# ---------------- Product images ----------------
@router.get("/products/{product_id}/images")
def list_product_images(product_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return img_service.list_images(db, product_id)


@router.post("/products/{product_id}/images")
def add_product_image_url(product_id: str, payload: ProductImageUrlInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return img_service.add_url_image(db, product_id, payload.url, payload.is_primary)


@router.post("/products/{product_id}/images/upload")
async def upload_product_image(product_id: str, file: UploadFile = File(...), admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    content = await file.read()
    return img_service.upload_image(db, product_id, file.content_type, content)


@router.put("/products/{product_id}/images/reorder")
def reorder_product_images(product_id: str, payload: ImageReorderInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return img_service.reorder_images(db, product_id, payload.ids)


@router.put("/products/{product_id}/images/{image_id}/primary")
def make_primary_image(product_id: str, image_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return img_service.set_primary(db, product_id, image_id)


@router.delete("/products/{product_id}/images/{image_id}")
def delete_product_image(product_id: str, image_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return img_service.delete_image(db, product_id, image_id)


# ---------------- Categories (hierárquicas) ----------------
@router.get("/categories/tree")
def categories_tree(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return category_service.build_tree(db, only_active=False)


@router.post("/categories")
def create_category(payload: CategoryInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return category_service.create_category(db, payload.model_dump())


@router.put("/categories/reorder")
def reorder_categories(payload: CategoryReorderInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return category_service.reorder(db, payload.ids)


@router.put("/categories/{category_id}")
def update_category(category_id: str, payload: CategoryInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return category_service.update_category(db, category_id, payload.model_dump(exclude_unset=True))


@router.delete("/categories/{category_id}")
def delete_category(category_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return category_service.delete_category(db, category_id)


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
