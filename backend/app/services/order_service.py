import random
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Order, Product
from app.schemas import CheckoutInput
from app.services.coupon_service import resolve_coupon
from app.services.payment_service import PAYMENT_STATUS_MOCK, build_mock_payment
from app.services.shipping_service import compute_shipping
from app.utils import to_dict


def create_order(db: Session, user: dict, payload: CheckoutInput) -> dict:
    """Cria pedido com baixa de estoque ATÔMICA (transação + SELECT ... FOR UPDATE).

    Impede venda acima do estoque (também garantido por CHECK stock >= 0 no banco).
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="Carrinho vazio")

    try:
        order_items = []
        subtotal = 0.0

        # Bloqueia as linhas dos produtos para evitar condição de corrida.
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
            line_total = round(product.price * item.quantity, 2)
            subtotal += line_total
            order_items.append(
                {
                    "product_id": product.id,
                    "name": product.name,
                    "slug": product.slug,
                    "image": (product.images or [""])[0] if product.images else "",
                    "price": product.price,
                    "quantity": item.quantity,
                    "line_total": line_total,
                }
            )

        subtotal = round(subtotal, 2)
        discount, coupon_code = resolve_coupon(db, payload.coupon, subtotal)
        shipping = compute_shipping(subtotal - discount, payload.shipping_method)
        total = round(subtotal - discount + shipping, 2)

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

        # Baixa de estoque atômica (mesma transação).
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
