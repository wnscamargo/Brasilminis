from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Favorite, Product
from app.utils import to_dict

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
def list_favorites(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    favs = db.query(Favorite).filter(Favorite.user_id == user["id"]).all()
    ids = [f.product_id for f in favs]
    if not ids:
        return []
    products = db.query(Product).filter(Product.id.in_(ids)).all()
    return [to_dict(p) for p in products]


@router.post("/{product_id}")
def add_favorite(product_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.get(Favorite, {"user_id": user["id"], "product_id": product_id})
    if not existing:
        db.add(Favorite(user_id=user["id"], product_id=product_id))
        db.commit()
    return {"message": "Adicionado aos favoritos"}


@router.delete("/{product_id}")
def remove_favorite(product_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.get(Favorite, {"user_id": user["id"], "product_id": product_id})
    if existing:
        db.delete(existing)
        db.commit()
    return {"message": "Removido dos favoritos"}
