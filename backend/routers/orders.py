import uuid
import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from db import db
from deps import get_current_user
from models import CheckoutInput, CouponValidateInput

router = APIRouter(prefix="/api", tags=["orders"])

FREE_SHIPPING_THRESHOLD = 300.0
STANDARD_SHIPPING = 29.9


async def _resolve_coupon(code: str, subtotal: float):
    if not code:
        return 0.0, None
    coupon = await db.coupons.find_one({"code": code.upper(), "active": True})
    if not coupon:
        raise HTTPException(status_code=400, detail="Cupom inválido")
    if subtotal < coupon.get("min_order", 0):
        raise HTTPException(status_code=400, detail=f"Pedido mínimo de R$ {coupon.get('min_order', 0):.2f} para este cupom")
    if coupon["type"] == "percent":
        discount = round(subtotal * coupon["value"] / 100, 2)
    else:
        discount = float(coupon["value"])
    return min(discount, subtotal), coupon["code"]


@router.post("/coupons/validate")
async def validate_coupon(payload: CouponValidateInput):
    coupon = await db.coupons.find_one({"code": payload.code.upper(), "active": True}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=400, detail="Cupom inválido ou expirado")
    return coupon


@router.post("/orders")
async def create_order(payload: CheckoutInput, user: dict = Depends(get_current_user)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Carrinho vazio")

    order_items = []
    subtotal = 0.0
    for item in payload.items:
        product = await db.products.find_one({"id": item.product_id})
        if not product or not product.get("is_active", True):
            raise HTTPException(status_code=400, detail="Produto indisponível no carrinho")
        if product.get("stock", 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente para {product['name']}")
        line_total = round(product["price"] * item.quantity, 2)
        subtotal += line_total
        order_items.append({
            "product_id": product["id"],
            "name": product["name"],
            "slug": product.get("slug"),
            "image": (product.get("images") or [""])[0],
            "price": product["price"],
            "quantity": item.quantity,
            "line_total": line_total,
        })

    subtotal = round(subtotal, 2)
    discount, coupon_code = await _resolve_coupon(payload.coupon, subtotal)
    shipping = 0.0 if (subtotal - discount) >= FREE_SHIPPING_THRESHOLD else STANDARD_SHIPPING
    total = round(subtotal - discount + shipping, 2)

    order = {
        "id": str(uuid.uuid4()),
        "order_number": f"BM{random.randint(100000, 999999)}",
        "user_id": user["id"],
        "user_name": user["name"],
        "user_email": user["email"],
        "items": order_items,
        "subtotal": subtotal,
        "discount": discount,
        "coupon": coupon_code,
        "shipping": shipping,
        "shipping_method": payload.shipping_method,
        "total": total,
        "payment_method": payload.payment_method,
        "payment_status": "paid_simulated",  # MOCKED payment for MVP
        "status": "confirmado",
        "address": payload.address.model_dump() if payload.address else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.orders.insert_one(order)
    order.pop("_id", None)

    # decrement stock
    for item in payload.items:
        await db.products.update_one({"id": item.product_id}, {"$inc": {"stock": -item.quantity}})

    # mock payment payload (ready for Mercado Pago future integration)
    order["payment"] = {
        "provider": "mock",
        "method": payload.payment_method,
        "pix_qr": "00020126BR.GOV.BCB.PIX-SIMULATED" if payload.payment_method == "pix" else None,
        "status": "approved",
    }
    return order


@router.get("/orders")
async def my_orders(user: dict = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return orders


@router.get("/orders/{order_id}")
async def get_order(order_id: str, user: dict = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id, "user_id": user["id"]}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order
