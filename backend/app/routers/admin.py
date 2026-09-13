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
    BadgeInput,
    BannerInput,
    BrandInput,
    CategoryInput,
    CategoryReorderInput,
    CouponGenerateInput,
    CouponInput,
    CustomerDeleteInput,
    DashboardResetInput,
    ImageReorderInput,
    OrderDeleteInput,
    OrderStatusInput,
    ProductImageUrlInput,
    ProductInput,
    ProfileInput,
)
from app.services import analytics_service, category_service
from app.services import badge_service
from app.services import coupon_service
from app.services import customer_admin_service
from app.services import dashboard_service
from app.services import order_admin_service
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
    baseline = dashboard_service.get_baseline(db)
    total_products = db.query(func.count(Product.id)).scalar() or 0
    low_stock = db.query(func.count(Product.id)).filter(Product.stock <= 5).scalar() or 0

    # KPIs acumulados respeitam o marco de zeragem (eventos posteriores ao baseline)
    orders_q = db.query(Order)
    customers_q = db.query(func.count(User.id)).filter(User.role == "customer")
    if baseline:
        orders_q = orders_q.filter(Order.created_at >= baseline)
        customers_q = customers_q.filter(User.created_at >= baseline)

    orders = orders_q.all()
    total_orders = len(orders)
    total_customers = customers_q.scalar() or 0
    revenue = round(sum((o.total or 0) for o in orders), 2)

    by_day: dict = {}
    for o in orders:
        day = (o.created_at or "")[:10]
        by_day[day] = round(by_day.get(day, 0) + (o.total or 0), 2)
    revenue_series = [{"date": k, "revenue": v} for k, v in sorted(by_day.items())][-7:]

    recent_q = db.query(Order)
    if baseline:
        recent_q = recent_q.filter(Order.created_at >= baseline)
    recent = recent_q.order_by(Order.created_at.desc()).limit(5).all()

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "revenue": revenue,
        "low_stock": low_stock,
        "revenue_series": revenue_series,
        "recent_orders": [to_dict(o) for o in recent],
        "dashboard_baseline": baseline,
    }


@router.get("/analytics")
def analytics(
    period: str = "30d",
    start: str | None = None,
    end: str | None = None,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    baseline = dashboard_service.get_baseline(db)
    return analytics_service.compute(db, period, start, end, baseline=baseline)


# ---------------- Controle dos indicadores (zeragem do Dashboard) ----------------
@router.get("/dashboard/baseline")
def dashboard_baseline(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {"baseline": dashboard_service.get_baseline(db), "history": dashboard_service.list_resets(db)}


@router.post("/dashboard/reset")
def dashboard_reset(payload: DashboardResetInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return dashboard_service.reset(db, admin, payload.reason, payload.confirm)


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


# ---------------- Badges (catálogo administrável) ----------------
@router.get("/badges")
def admin_list_badges(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return badge_service.list_badges(db)


@router.post("/badges")
def admin_create_badge(payload: BadgeInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return badge_service.create_badge(db, payload.model_dump())


@router.put("/badges/{badge_id}")
def admin_update_badge(badge_id: str, payload: BadgeInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return badge_service.update_badge(db, badge_id, payload.model_dump())


@router.delete("/badges/{badge_id}")
def admin_delete_badge(badge_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return badge_service.delete_badge(db, badge_id)


# ---------------- Produtos por categoria/subcategoria (Ver produtos) ----------------
@router.get("/catalog/products")
def admin_products_by_category(
    category: str | None = None,   # slug de categoria/subcategoria
    search: str | None = None,
    active: str | None = None,     # "true" | "false" | None(todos)
    stock: str | None = None,      # "in" | "out" | None
    sort: str = "recent",
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    from sqlalchemy import or_
    from app.routers.catalog import _category_filter
    q = db.query(Product)
    if category:
        q = q.filter(_category_filter(db, category))
    if active == "true":
        q = q.filter(Product.is_active.is_(True))
    elif active == "false":
        q = q.filter(Product.is_active.is_(False))
    if stock == "in":
        q = q.filter(Product.stock > 0)
    elif stock == "out":
        q = q.filter(Product.stock <= 0)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.slug.ilike(like)))
    sort_map = {
        "recent": Product.created_at.desc(),
        "name": Product.name.asc(),
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "stock_asc": Product.stock.asc(),
        "stock_desc": Product.stock.desc(),
    }
    order_by = sort_map.get(sort, Product.created_at.desc())
    total = q.count()
    items = q.order_by(order_by).offset((page - 1) * limit).limit(limit).all()
    return {"total": total, "page": page, "limit": limit, "items": [to_dict(p) for p in items]}


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
def admin_list_orders(scope: str = "active", admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return order_admin_service.list_orders(db, scope)


@router.put("/orders/{order_id}/status")
def update_order_status(order_id: str, payload: OrderStatusInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return to_dict(order)


@router.delete("/orders/{order_id}")
def delete_order(order_id: str, payload: OrderDeleteInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return order_admin_service.delete_order(db, order_id, admin, payload.reason, payload.confirm)


# ---------------- Cupons de desconto ----------------
@router.get("/coupons")
def admin_list_coupons(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return coupon_service.list_coupons(db)


@router.post("/coupons/generate-code")
def admin_generate_coupon_code(payload: CouponGenerateInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {"code": coupon_service.generate_code(db, payload.prefix, payload.length)}


@router.post("/coupons")
def admin_create_coupon(payload: CouponInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return coupon_service.create_coupon(db, payload.model_dump())


@router.put("/coupons/{code}")
def admin_update_coupon(code: str, payload: CouponInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return coupon_service.update_coupon(db, code, payload.model_dump())


@router.delete("/coupons/{code}")
def admin_delete_coupon(code: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return coupon_service.delete_coupon(db, code)


# ---------------- Customers ----------------
@router.get("/customers")
def admin_list_customers(scope: str = "active", admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return customer_admin_service.list_customers(db, scope)


@router.delete("/customers/{user_id}")
def admin_delete_customer(user_id: str, payload: CustomerDeleteInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return customer_admin_service.delete_customer(db, user_id, admin, payload.reason, payload.confirm, payload.anonymize)


@router.post("/customers/{user_id}/restore")
def admin_restore_customer(user_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return customer_admin_service.restore_customer(db, user_id, admin)


@router.put("/customers/{user_id}")
def admin_update_customer(user_id: str, payload: ProfileInput, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    from app.core.cpf import is_valid_cpf, normalize_cpf
    u = db.get(User, user_id)
    if not u or u.role != "customer":
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "cpf" in data:
        cpf = normalize_cpf(data.pop("cpf"))
        if cpf:
            if not is_valid_cpf(cpf):
                raise HTTPException(status_code=400, detail="CPF inválido. Verifique os números digitados.")
            dup = db.query(User).filter(User.cpf == cpf, User.id != u.id).first()
            if dup:
                raise HTTPException(status_code=400, detail="Este CPF já está cadastrado.")
            u.cpf = cpf
    for k, v in data.items():
        setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "name": u.name, "email": u.email, "phone": u.phone or "", "cpf": u.cpf or "", "newsletter": bool(u.newsletter)}


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
