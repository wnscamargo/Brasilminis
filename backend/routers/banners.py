from fastapi import APIRouter

from db import db

router = APIRouter(prefix="/api", tags=["banners"])


@router.get("/banners")
async def list_banners():
    banners = await db.banners.find({"active": True}, {"_id": 0}).sort("position", 1).to_list(50)
    return banners
