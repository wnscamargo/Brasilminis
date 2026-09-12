from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP

from app.dependencies import get_current_user, get_db
from app.models import Order, Product
from app.schemas import CheckoutInput, CouponPreviewInput, CouponValidateInput
from app.services import coupon_service
from app.services.coupon_service import validate_coupon
from app.services.order_service import create_order
from app.utils import to_dict

router = APIRouter(prefix="/api", tags=["orders"])


@router.post("/coupons/validate")
def validate(payload: CouponValidateInput, db: Session = Depends(get_db)):
    return validate_coupon(db, payload.code)


@router.post("/coupons/preview")
def preview(payload: CouponPreviewInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Calcula o desconto no servidor (nunca confiar no frontend)."""
    cents = Decimal("0.01")
    order_items = []
    subtotal = Decimal("0.00")
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product or not product.is_active:
            continue
        unit = Decimal(str(product.price)).quantize(cents, rounding=ROUND_HALF_UP)
        line = (unit * item.quantity).quantize(cents, rounding=ROUND_HALF_UP)
        subtotal += line
        order_items.append({"product_id": product.id, "quantity": item.quantity, "line_revenue": float(line)})
    subtotal = subtotal.quantize(cents, rounding=ROUND_HALF_UP)
    ev = coupon_service.evaluate(db, payload.code, user, order_items, float(subtotal))
    return {**ev, "subtotal": float(subtotal)}


@router.post("/orders")
def create(payload: CheckoutInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_order(db, user, payload)


@router.get("/orders")
def my_orders(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .filter(Order.user_id == user["id"], Order.deleted_at.is_(None))
        .order_by(Order.created_at.desc())
        .limit(200)
        .all()
    )
    return [to_dict(o) for o in orders]


@router.get("/orders/{order_id}")
def get_order(order_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user["id"], Order.deleted_at.is_(None)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return to_dict(order)
