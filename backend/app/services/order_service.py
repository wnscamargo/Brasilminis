import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import MelhorEnvioSender, MelhorEnvioShipment, Order, Product
from app.schemas import CheckoutInput
from app.services.coupon_service import resolve_coupon
from app.services.payment_service import PAYMENT_STATUS_MOCK, build_mock_payment
from app.services.shipping_service import compute_shipping
from app.utils import to_dict

CENTS = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


def _resolve_shipping(db: Session, payload: CheckoutInput, amount_after_discount: Decimal, order_items: list):
    """Resolve o frete. Se houver cotação Melhor Envio selecionada, congela o snapshot.

    Retorna (customer_price, quoted_price, snapshot, meta). Preserva frete grátis:
    mesmo grátis para o cliente, o custo real cotado é registrado.
    """
    if payload.quote_id and payload.shipping_service_id:
        from app.services.melhor_envio_quote_service import get_valid_quote

        q = get_valid_quote(db, payload.quote_id)
        option = next((o for o in (q.results or []) if o.get("service_id") == payload.shipping_service_id), None)
        if not option:
            raise HTTPException(status_code=400, detail="Serviço de frete inválido para esta cotação.")
        quoted = _money(option["price"])
        free = amount_after_discount >= Decimal(str(settings.FREE_SHIPPING_THRESHOLD))
        customer = Decimal("0.00") if free else quoted
        sender = db.get(MelhorEnvioSender, 1)
        origin = "".join(c for c in (sender.postal_code if sender else "") if c.isdigit())
        products = [{"name": i["name"], "quantity": i["quantity"], "unitary_value": i["price"]} for i in order_items]
        snapshot = {
            "quote_id": q.id,
            "service_id": option["service_id"],
            "option": option,
            "volumes": q.volumes,
            "products": products,
            "origin_postal_code": origin,
            "destination_postal_code": q.destination_postal_code,
            "free_shipping_applied": bool(free),
        }
        meta = {
            "provider": "melhor_envio",
            "service_id": option.get("service_id"),
            "service_name": option.get("name"),
            "company_id": option.get("company_id"),
            "company_name": option.get("company_name"),
            "delivery_min": option.get("delivery_min"),
            "delivery_max": option.get("delivery_max"),
            "destination_postal_code": q.destination_postal_code,
        }
        return customer, quoted, snapshot, meta

    # Fallback: regra de frete simples existente
    customer = _money(compute_shipping(float(amount_after_discount), payload.shipping_method))
    return customer, None, None, {"provider": "standard"}


def _build_recipient(payload: CheckoutInput, user: dict) -> dict | None:
    addr = payload.address
    if not addr:
        return None
    return {
        "name": addr.recipient or user["name"],
        "document": payload.recipient_document,
        "email": user["email"],
        "phone": payload.recipient_phone or user.get("phone") or "",
        "street": addr.street,
        "number": addr.number,
        "complement": addr.complement or "",
        "district": addr.district,
        "city": addr.city,
        "uf": addr.state,
        "state": addr.state,
        "zip": addr.zip,
        "cep": addr.zip,
    }


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
        amount_after_discount = subtotal - discount
        shipping, shipping_quoted, quote_snapshot, ship_meta = _resolve_shipping(
            db, payload, amount_after_discount, order_items
        )
        total = _money(amount_after_discount + shipping)
        recipient_snapshot = _build_recipient(payload, user)

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
            shipping_provider=ship_meta.get("provider"),
            shipping_service_id=ship_meta.get("service_id"),
            shipping_service_name=ship_meta.get("service_name"),
            shipping_company_id=ship_meta.get("company_id"),
            shipping_company_name=ship_meta.get("company_name"),
            shipping_price_customer=shipping,
            shipping_price_quoted=shipping_quoted,
            shipping_delivery_min=ship_meta.get("delivery_min"),
            shipping_delivery_max=ship_meta.get("delivery_max"),
            shipping_destination_postal_code=ship_meta.get("destination_postal_code"),
            shipping_quote_snapshot=quote_snapshot,
            recipient_snapshot=recipient_snapshot,
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

        # Cria o registro de envio (Melhor Envio) quando houve cotação selecionada
        if ship_meta.get("provider") == "melhor_envio":
            db.add(MelhorEnvioShipment(
                id=str(uuid.uuid4()),
                order_id=order.id,
                internal_status="pending",
                service_id=ship_meta.get("service_id"),
                service_name=ship_meta.get("service_name"),
                company_name=ship_meta.get("company_name"),
                price=shipping_quoted,
                timeline=[],
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ))

        db.commit()
        db.refresh(order)
    except Exception:
        db.rollback()
        raise

    result = to_dict(order)
    result["payment"] = build_mock_payment(payload.payment_method)
    return result
