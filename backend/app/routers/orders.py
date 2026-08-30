from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import Order
from app.schemas import CheckoutInput, CouponValidateInput
from app.services.coupon_service import validate_coupon
from app.services.order_service import create_order
from app.utils import to_dict

router = APIRouter(prefix="/api", tags=["orders"])


@router.post("/coupons/validate")
def validate(payload: CouponValidateInput, db: Session = Depends(get_db)):
    return validate_coupon(db, payload.code)


@router.post("/orders")
def create(payload: CheckoutInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_order(db, user, payload)


@router.get("/orders")
def my_orders(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .filter(Order.user_id == user["id"])
        .order_by(Order.created_at.desc())
        .limit(200)
        .all()
    )
    return [to_dict(o) for o in orders]


@router.get("/orders/{order_id}")
def get_order(order_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user["id"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return to_dict(order)
