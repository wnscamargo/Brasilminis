from fastapi import APIRouter, Depends

from db import db
from deps import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
async def list_favorites(user: dict = Depends(get_current_user)):
    favs = await db.favorites.find({"user_id": user["id"]}).to_list(1000)
    ids = [f["product_id"] for f in favs]
    if not ids:
        return []
    products = await db.products.find({"id": {"$in": ids}}, {"_id": 0}).to_list(1000)
    return products


@router.post("/{product_id}")
async def add_favorite(product_id: str, user: dict = Depends(get_current_user)):
    await db.favorites.update_one(
        {"user_id": user["id"], "product_id": product_id},
        {"$set": {"user_id": user["id"], "product_id": product_id}},
        upsert=True,
    )
    return {"message": "Adicionado aos favoritos"}


@router.delete("/{product_id}")
async def remove_favorite(product_id: str, user: dict = Depends(get_current_user)):
    await db.favorites.delete_one({"user_id": user["id"], "product_id": product_id})
    return {"message": "Removido dos favoritos"}
