from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Coupon
from app.utils import to_dict


def resolve_coupon(db: Session, code: str, subtotal: float):
    """Valida o cupom para o subtotal e retorna (desconto, codigo)."""
    if not code:
        return 0.0, None
    coupon = db.query(Coupon).filter(Coupon.code == code.upper(), Coupon.active.is_(True)).first()
    if not coupon:
        raise HTTPException(status_code=400, detail="Cupom inválido")
    if subtotal < (coupon.min_order or 0):
        raise HTTPException(
            status_code=400,
            detail=f"Pedido mínimo de R$ {coupon.min_order:.2f} para este cupom",
        )
    if coupon.type == "percent":
        discount = round(subtotal * coupon.value / 100, 2)
    else:
        discount = float(coupon.value)
    return min(discount, subtotal), coupon.code


def validate_coupon(db: Session, code: str) -> dict:
    coupon = db.query(Coupon).filter(Coupon.code == code.upper(), Coupon.active.is_(True)).first()
    if not coupon:
        raise HTTPException(status_code=400, detail="Cupom inválido ou expirado")
    return to_dict(coupon)
