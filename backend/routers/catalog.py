import re
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from db import db

router = APIRouter(prefix="/api", tags=["catalog"])


def _clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


@router.get("/categories")
async def list_categories(group: Optional[str] = None):
    q = {}
    if group:
        q["group"] = group
    cats = await db.categories.find(q, {"_id": 0}).sort("name", 1).to_list(500)
    return cats


@router.get("/categories/{slug}")
async def get_category(slug: str):
    cat = await db.categories.find_one({"slug": slug}, {"_id": 0})
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return cat


@router.get("/brands")
async def list_brands():
    brands = await db.brands.find({}, {"_id": 0}).sort("name", 1).to_list(500)
    return brands


@router.get("/brands/{slug}")
async def get_brand(slug: str):
    brand = await db.brands.find_one({"slug": slug}, {"_id": 0})
    if not brand:
        raise HTTPException(status_code=404, detail="Marca não encontrada")
    return brand


@router.get("/products")
async def list_products(
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
):
    q = {"is_active": True}
    if category:
        q["category"] = category
    if group:
        q["group"] = group
    if brand:
        q["brand"] = brand
    if badge:
        q["badges"] = badge
    if featured is not None:
        q["featured"] = featured
    if on_sale:
        q["compare_at_price"] = {"$ne": None, "$gt": 0}
    if search:
        rx = {"$regex": re.escape(search), "$options": "i"}
        q["$or"] = [{"name": rx}, {"description": rx}, {"brand": rx}, {"category": rx}]

    sort_map = {
        "recent": [("created_at", -1)],
        "price_asc": [("price", 1)],
        "price_desc": [("price", -1)],
        "name": [("name", 1)],
        "rating": [("rating", -1)],
    }
    sort_spec = sort_map.get(sort, [("created_at", -1)])

    skip = (page - 1) * limit
    total = await db.products.count_documents(q)
    items = await db.products.find(q, {"_id": 0}).sort(sort_spec).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "page": page, "limit": limit, "items": items}


@router.get("/products/{slug}")
async def get_product(slug: str):
    product = await db.products.find_one({"slug": slug}, {"_id": 0})
    if not product:
        product = await db.products.find_one({"id": slug}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


@router.get("/products/{slug}/related")
async def related_products(slug: str):
    product = await db.products.find_one({"slug": slug}, {"_id": 0})
    if not product:
        return []
    q = {
        "is_active": True,
        "id": {"$ne": product["id"]},
        "$or": [{"category": product.get("category")}, {"brand": product.get("brand")}],
    }
    items = await db.products.find(q, {"_id": 0}).limit(8).to_list(8)
    return items
