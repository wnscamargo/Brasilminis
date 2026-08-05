import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from db import db
from deps import get_current_admin
from models import ProductInput, CategoryInput, BrandInput, BannerInput, OrderStatusInput
from utils import slugify

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------- Dashboard ----------------
@router.get("/stats")
async def stats(admin: dict = Depends(get_current_admin)):
    total_products = await db.products.count_documents({})
    total_orders = await db.orders.count_documents({})
    total_customers = await db.users.count_documents({"role": "customer"})
    orders = await db.orders.find({}, {"_id": 0, "total": 1, "status": 1, "created_at": 1, "items": 1}).to_list(5000)
    revenue = round(sum(o.get("total", 0) for o in orders), 2)
    low_stock = await db.products.count_documents({"stock": {"$lte": 5}})

    # revenue by day (last 7 entries)
    by_day = {}
    for o in orders:
        day = (o.get("created_at") or "")[:10]
        by_day[day] = round(by_day.get(day, 0) + o.get("total", 0), 2)
    revenue_series = [{"date": k, "revenue": v} for k, v in sorted(by_day.items())][-7:]

    recent_orders = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "revenue": revenue,
        "low_stock": low_stock,
        "revenue_series": revenue_series,
        "recent_orders": recent_orders,
    }


# ---------------- Products ----------------
@router.get("/products")
async def admin_list_products(admin: dict = Depends(get_current_admin)):
    return await db.products.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)


@router.post("/products")
async def create_product(payload: ProductInput, admin: dict = Depends(get_current_admin)):
    data = payload.model_dump()
    data["id"] = str(uuid.uuid4())
    data["slug"] = data.get("slug") or slugify(data["name"])
    if await db.products.find_one({"slug": data["slug"]}):
        data["slug"] = f"{data['slug']}-{data['id'][:6]}"
    data["rating"] = 0
    data["reviews_count"] = 0
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.products.insert_one(data)
    data.pop("_id", None)
    return data


@router.put("/products/{product_id}")
async def update_product(product_id: str, payload: ProductInput, admin: dict = Depends(get_current_admin)):
    existing = await db.products.find_one({"id": product_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    data = payload.model_dump()
    data["slug"] = data.get("slug") or existing.get("slug") or slugify(data["name"])
    await db.products.update_one({"id": product_id}, {"$set": data})
    fresh = await db.products.find_one({"id": product_id}, {"_id": 0})
    return fresh


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, admin: dict = Depends(get_current_admin)):
    await db.products.delete_one({"id": product_id})
    return {"message": "Produto removido"}


# ---------------- Categories ----------------
@router.post("/categories")
async def create_category(payload: CategoryInput, admin: dict = Depends(get_current_admin)):
    data = payload.model_dump()
    data["id"] = str(uuid.uuid4())
    data["slug"] = data.get("slug") or slugify(data["name"])
    if await db.categories.find_one({"slug": data["slug"]}):
        raise HTTPException(status_code=400, detail="Categoria já existe")
    await db.categories.insert_one(data)
    data.pop("_id", None)
    return data


@router.put("/categories/{category_id}")
async def update_category(category_id: str, payload: CategoryInput, admin: dict = Depends(get_current_admin)):
    data = payload.model_dump()
    data["slug"] = data.get("slug") or slugify(data["name"])
    await db.categories.update_one({"id": category_id}, {"$set": data})
    return await db.categories.find_one({"id": category_id}, {"_id": 0})


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, admin: dict = Depends(get_current_admin)):
    await db.categories.delete_one({"id": category_id})
    return {"message": "Categoria removida"}


# ---------------- Brands ----------------
@router.post("/brands")
async def create_brand(payload: BrandInput, admin: dict = Depends(get_current_admin)):
    data = payload.model_dump()
    data["id"] = str(uuid.uuid4())
    data["slug"] = data.get("slug") or slugify(data["name"])
    if await db.brands.find_one({"slug": data["slug"]}):
        raise HTTPException(status_code=400, detail="Marca já existe")
    await db.brands.insert_one(data)
    data.pop("_id", None)
    return data


@router.put("/brands/{brand_id}")
async def update_brand(brand_id: str, payload: BrandInput, admin: dict = Depends(get_current_admin)):
    data = payload.model_dump()
    data["slug"] = data.get("slug") or slugify(data["name"])
    await db.brands.update_one({"id": brand_id}, {"$set": data})
    return await db.brands.find_one({"id": brand_id}, {"_id": 0})


@router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: str, admin: dict = Depends(get_current_admin)):
    await db.brands.delete_one({"id": brand_id})
    return {"message": "Marca removida"}


# ---------------- Orders ----------------
@router.get("/orders")
async def admin_list_orders(admin: dict = Depends(get_current_admin)):
    return await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)


@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, payload: OrderStatusInput, admin: dict = Depends(get_current_admin)):
    await db.orders.update_one({"id": order_id}, {"$set": {"status": payload.status}})
    return await db.orders.find_one({"id": order_id}, {"_id": 0})


# ---------------- Customers ----------------
@router.get("/customers")
async def admin_list_customers(admin: dict = Depends(get_current_admin)):
    users = await db.users.find({"role": "customer"}).sort("created_at", -1).to_list(2000)
    result = []
    for u in users:
        orders_count = await db.orders.count_documents({"user_id": str(u["_id"])})
        result.append({
            "id": str(u["_id"]),
            "name": u.get("name"),
            "email": u.get("email"),
            "phone": u.get("phone", ""),
            "newsletter": u.get("newsletter", False),
            "orders_count": orders_count,
            "created_at": u.get("created_at"),
        })
    return result


# ---------------- Banners ----------------
@router.get("/banners")
async def admin_list_banners(admin: dict = Depends(get_current_admin)):
    return await db.banners.find({}, {"_id": 0}).sort("position", 1).to_list(50)


@router.post("/banners")
async def create_banner(payload: BannerInput, admin: dict = Depends(get_current_admin)):
    data = payload.model_dump()
    data["id"] = str(uuid.uuid4())
    await db.banners.insert_one(data)
    data.pop("_id", None)
    return data


@router.put("/banners/{banner_id}")
async def update_banner(banner_id: str, payload: BannerInput, admin: dict = Depends(get_current_admin)):
    await db.banners.update_one({"id": banner_id}, {"$set": payload.model_dump()})
    return await db.banners.find_one({"id": banner_id}, {"_id": 0})


@router.delete("/banners/{banner_id}")
async def delete_banner(banner_id: str, admin: dict = Depends(get_current_admin)):
    await db.banners.delete_one({"id": banner_id})
    return {"message": "Banner removido"}
