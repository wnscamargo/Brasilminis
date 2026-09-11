import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Order, Product
from app.schemas import CheckoutInput
from app.services.coupon_service import resolve_coupon
from app.services.payment_service import PAYMENT_STATUS_MOCK, build_mock_payment
from app.services.shipping_service import compute_shipping
from app.utils import to_dict

CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


def create_order(db: Session, user: dict, payload: CheckoutInput) -> dict:
    """Cria pedido com baixa de estoque ATÔMICA e CONGELA o custo (CMV) por item.

    Cálculos financeiros usam Decimal. Se o custo do produto for None, o item é
    marcado como 'sem custo' (não inventa CMV).
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="Carrinho vazio")

    try:
        order_items = []
        subtotal = Decimal("0.00")

        for item in payload.items:
            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .with_for_update()
                .first()
            )
            if not product or not product.is_active:
                raise HTTPException(status_code=400, detail="Produto indisponível no carrinho")
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=400, detail=f"Estoque insuficiente para {product.name}"
                )

            qty = item.quantity
            unit_price = _money(product.price)
            has_cost = product.cost_price is not None
            unit_cost = _money(product.cost_price) if has_cost else None

            line_revenue = _money(unit_price * qty)
            line_cogs = _money(unit_cost * qty) if has_cost else None
            line_gross_profit = _money(line_revenue - line_cogs) if has_cost else None

            subtotal += line_revenue
            order_items.append({
                "product_id": product.id,
                "name": product.name,
                "slug": product.slug,
                "image": (product.images or [""])[0] if product.images else "",
                "price": float(unit_price),
                "quantity": qty,
                "line_total": float(line_revenue),
                # Snapshots congelados no momento da venda
                "unit_price_snapshot": float(unit_price),
                "unit_cost_snapshot": (float(unit_cost) if has_cost else None),
                "line_revenue": float(line_revenue),
                "line_cogs": (float(line_cogs) if has_cost else None),
                "line_gross_profit": (float(line_gross_profit) if has_cost else None),
                "has_cost": has_cost,
            })

        subtotal = _money(subtotal)
        discount_f, coupon_code = resolve_coupon(db, payload.coupon, float(subtotal))
        discount = _money(discount_f)
        shipping = _money(compute_shipping(float(subtotal - discount), payload.shipping_method))
        total = _money(subtotal - discount + shipping)

        order = Order(
            id=str(uuid.uuid4()),
            order_number=f"BM{random.randint(100000, 999999)}",
            user_id=user["id"],
            user_name=user["name"],
            user_email=user["email"],
            items=order_items,
            subtotal=subtotal,
            discount=discount,
            coupon=coupon_code,
            shipping=shipping,
            shipping_method=payload.shipping_method,
            total=total,
            payment_method=payload.payment_method,
            payment_status=PAYMENT_STATUS_MOCK,  # MOCKED payment
            status="confirmado",
            address=payload.address.model_dump() if payload.address else None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(order)

        for item in payload.items:
            db.query(Product).filter(Product.id == item.product_id).update(
                {Product.stock: Product.stock - item.quantity}, synchronize_session=False
            )

        db.commit()
        db.refresh(order)
    except Exception:
        db.rollback()
        raise

    result = to_dict(order)
    result["payment"] = build_mock_payment(payload.payment_method)
    return result
