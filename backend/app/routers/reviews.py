import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Product, Review
from app.schemas import ReviewInput
from app.utils import to_dict

router = APIRouter(prefix="/api", tags=["reviews"])


@router.get("/products/{product_id}/reviews")
def list_reviews(product_id: str, db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .limit(200)
        .all()
    )
    return [to_dict(r) for r in reviews]


@router.post("/products/{product_id}/reviews")
def add_review(product_id: str, payload: ReviewInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    review = Review(
        id=str(uuid.uuid4()),
        product_id=product_id,
        user_id=user["id"],
        user_name=user["name"],
        rating=payload.rating,
        comment=payload.comment,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(review)
    db.flush()

    all_ratings = [r.rating for r in db.query(Review.rating).filter(Review.product_id == product_id).all()]
    count = len(all_ratings)
    avg = round(sum(all_ratings) / count, 1) if count else 0
    product.rating = avg
    product.reviews_count = count
    db.commit()
    return to_dict(review)
