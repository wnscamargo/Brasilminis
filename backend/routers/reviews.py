from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from db import db
from deps import get_current_user
from models import ReviewInput

router = APIRouter(prefix="/api", tags=["reviews"])


@router.get("/products/{product_id}/reviews")
async def list_reviews(product_id: str):
    reviews = await db.reviews.find({"product_id": product_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return reviews


@router.post("/products/{product_id}/reviews")
async def add_review(product_id: str, payload: ReviewInput, user: dict = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    import uuid
    review = {
        "id": str(uuid.uuid4()),
        "product_id": product_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "rating": payload.rating,
        "comment": payload.comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.reviews.insert_one(review)
    review.pop("_id", None)

    # recompute aggregate rating
    all_reviews = await db.reviews.find({"product_id": product_id}).to_list(1000)
    count = len(all_reviews)
    avg = round(sum(r["rating"] for r in all_reviews) / count, 1) if count else 0
    await db.products.update_one({"id": product_id}, {"$set": {"rating": avg, "reviews_count": count}})
    return review
