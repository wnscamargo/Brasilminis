import random
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Coupon, CouponRedemption, Order, Product
from app.utils import to_dict

CENTS = Decimal("0.01")


def _money(v) -> float:
    return float(Decimal(str(v)).quantize(CENTS, rounding=ROUND_HALF_UP))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(db: Session, code: str) -> Coupon | None:
    if not code:
        return None
    return db.query(Coupon).filter(Coupon.code == code.strip().upper()).first()


# ---------------- Validação ----------------
def _check_validity(db: Session, coupon: Coupon, user: dict | None, subtotal: float) -> None:
    if not coupon.active:
        raise HTTPException(status_code=400, detail="Cupom inativo.")
    now = datetime.now(timezone.utc)
    if coupon.starts_at:
        try:
            if now < datetime.fromisoformat(coupon.starts_at):
                raise HTTPException(status_code=400, detail="Cupom ainda não está disponível.")
        except ValueError:
            pass
    if coupon.expires_at:
        try:
            if now > datetime.fromisoformat(coupon.expires_at):
                raise HTTPException(status_code=400, detail="Cupom expirado.")
        except ValueError:
            pass
    if coupon.usage_limit is not None and (coupon.used_count or 0) >= coupon.usage_limit:
        raise HTTPException(status_code=400, detail="Limite de uso do cupom esgotado.")
    if subtotal < float(coupon.min_order or 0):
        raise HTTPException(status_code=400, detail=f"Pedido mínimo de R$ {float(coupon.min_order):.2f} para este cupom.")
    if user:
        if coupon.first_purchase_only:
            prior = db.query(Order).filter(Order.user_id == user["id"], Order.deleted_at.is_(None)).count()
            if prior > 0:
                raise HTTPException(status_code=400, detail="Cupom válido apenas na primeira compra.")
        if coupon.per_user_limit is not None:
            used = db.query(CouponRedemption).filter(
                CouponRedemption.coupon_code == coupon.code, CouponRedemption.user_id == user["id"]
            ).count()
            if used >= coupon.per_user_limit:
                raise HTTPException(status_code=400, detail="Você já utilizou este cupom o número máximo de vezes.")


def _eligible_base(db: Session, coupon: Coupon, order_items: list) -> float:
    """Soma o valor dos itens elegíveis conforme o escopo do cupom."""
    scope = coupon.scope_type or "all"
    if scope == "all":
        return _money(sum(i.get("line_revenue", i.get("line_total", 0)) for i in order_items))
    if scope == "products":
        ids = set(coupon.scope_product_ids or [])
        return _money(sum((i.get("line_revenue", i.get("line_total", 0))) for i in order_items if i["product_id"] in ids))
    if scope == "categories":
        cat_ids = set(coupon.scope_category_ids or [])
        if not cat_ids:
            return 0.0
        prod_ids = [i["product_id"] for i in order_items]
        prods = {p.id: p for p in db.query(Product).filter(Product.id.in_(prod_ids)).all()}
        base = 0.0
        for i in order_items:
            p = prods.get(i["product_id"])
            if p and (p.main_category_id in cat_ids or p.subcategory_id in cat_ids):
                base += i.get("line_revenue", i.get("line_total", 0))
        return _money(base)
    return 0.0


def _compute_discount(coupon: Coupon, eligible_base: float) -> float:
    if eligible_base <= 0:
        return 0.0
    if coupon.type == "percent":
        discount = eligible_base * float(coupon.value) / 100.0
    else:
        discount = float(coupon.value)
    if coupon.max_discount is not None:
        discount = min(discount, float(coupon.max_discount))
    discount = min(discount, eligible_base)
    return _money(discount)


def evaluate(db: Session, code: str, user: dict | None, order_items: list, subtotal: float) -> dict:
    """Valida e calcula o desconto. Fonte da verdade (nunca confiar no frontend)."""
    coupon = _get(db, code)
    if not coupon:
        raise HTTPException(status_code=400, detail="Cupom inválido.")
    _check_validity(db, coupon, user, subtotal)
    base = _eligible_base(db, coupon, order_items)
    if base <= 0:
        raise HTTPException(status_code=400, detail="Cupom não aplicável aos itens do carrinho.")
    discount = _compute_discount(coupon, base)
    return {
        "code": coupon.code,
        "type": coupon.type,
        "value": float(coupon.value),
        "discount": discount,
        "free_shipping": bool(coupon.free_shipping),
        "allow_stacking": bool(coupon.allow_stacking),
        "description": coupon.description or "",
    }


def resolve_coupon(db: Session, code: str, user: dict | None, order_items: list, subtotal: float):
    """Usado na criação do pedido. Retorna (discount, free_shipping, snapshot, code)."""
    if not code:
        return 0.0, False, None, None
    ev = evaluate(db, code, user, order_items, subtotal)
    snapshot = {
        "code": ev["code"], "type": ev["type"], "value": ev["value"],
        "discount": ev["discount"], "free_shipping": ev["free_shipping"],
    }
    return ev["discount"], ev["free_shipping"], snapshot, ev["code"]


def record_redemption(db: Session, code: str, user_id: str | None, order_id: str | None) -> None:
    """Registra o uso (incrementa contador + insere redemption). Chamar 1x por pedido."""
    coupon = _get(db, code)
    if not coupon:
        return
    coupon.used_count = (coupon.used_count or 0) + 1
    db.add(CouponRedemption(id=str(uuid.uuid4()), coupon_code=coupon.code, user_id=user_id, order_id=order_id, created_at=_now_iso()))


def validate_coupon(db: Session, code: str) -> dict:
    """Endpoint público leve: existência/ativo/datas (sem itens/usuário)."""
    coupon = _get(db, code)
    if not coupon or not coupon.active:
        raise HTTPException(status_code=400, detail="Cupom inválido ou expirado.")
    now = datetime.now(timezone.utc)
    if coupon.expires_at:
        try:
            if now > datetime.fromisoformat(coupon.expires_at):
                raise HTTPException(status_code=400, detail="Cupom expirado.")
        except ValueError:
            pass
    return {
        "code": coupon.code, "type": coupon.type, "value": float(coupon.value),
        "min_order": float(coupon.min_order or 0), "free_shipping": bool(coupon.free_shipping),
        "description": coupon.description or "",
    }


# ---------------- Admin CRUD ----------------
def _serialize(db: Session, c: Coupon) -> dict:
    return {
        "code": c.code, "type": c.type, "value": float(c.value),
        "min_order": float(c.min_order or 0),
        "max_discount": (float(c.max_discount) if c.max_discount is not None else None),
        "active": bool(c.active), "description": c.description or "",
        "starts_at": c.starts_at, "expires_at": c.expires_at,
        "usage_limit": c.usage_limit, "per_user_limit": c.per_user_limit,
        "used_count": c.used_count or 0,
        "first_purchase_only": bool(c.first_purchase_only),
        "free_shipping": bool(c.free_shipping), "allow_stacking": bool(c.allow_stacking),
        "scope_type": c.scope_type or "all",
        "scope_category_ids": c.scope_category_ids or [],
        "scope_product_ids": c.scope_product_ids or [],
        "created_at": c.created_at, "updated_at": c.updated_at,
    }


def list_coupons(db: Session) -> list:
    rows = db.query(Coupon).order_by(Coupon.created_at.desc().nullslast()).all()
    return [_serialize(db, c) for c in rows]


def generate_code(db: Session, prefix: str = "BM", length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = (prefix or "").upper() + "".join(random.choices(alphabet, k=max(4, min(length, 16))))
        if not _get(db, code):
            return code
    raise HTTPException(status_code=500, detail="Não foi possível gerar um código único.")


def _apply(db: Session, c: Coupon, data: dict) -> None:
    c.type = data.get("type", c.type)
    if c.type not in ("percent", "fixed"):
        raise HTTPException(status_code=400, detail="Tipo inválido (percent | fixed).")
    c.value = data.get("value", c.value)
    c.min_order = data.get("min_order", c.min_order) or 0
    c.max_discount = data.get("max_discount", c.max_discount)
    c.active = data.get("active", c.active)
    c.description = data.get("description", c.description) or ""
    c.starts_at = data.get("starts_at", c.starts_at) or None
    c.expires_at = data.get("expires_at", c.expires_at) or None
    c.usage_limit = data.get("usage_limit", c.usage_limit)
    c.per_user_limit = data.get("per_user_limit", c.per_user_limit)
    c.first_purchase_only = bool(data.get("first_purchase_only", c.first_purchase_only))
    c.free_shipping = bool(data.get("free_shipping", c.free_shipping))
    c.allow_stacking = bool(data.get("allow_stacking", c.allow_stacking))
    scope = data.get("scope_type", c.scope_type) or "all"
    if scope not in ("all", "categories", "products"):
        raise HTTPException(status_code=400, detail="Escopo inválido.")
    c.scope_type = scope
    c.scope_category_ids = data.get("scope_category_ids", c.scope_category_ids) or []
    c.scope_product_ids = data.get("scope_product_ids", c.scope_product_ids) or []
    c.updated_at = _now_iso()


def create_coupon(db: Session, data: dict) -> dict:
    code = (data.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Código obrigatório.")
    if _get(db, code):
        raise HTTPException(status_code=400, detail="Já existe um cupom com este código.")
    c = Coupon(code=code, value=0, type="percent", used_count=0, created_at=_now_iso())
    _apply(db, c, data)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _serialize(db, c)


def update_coupon(db: Session, code: str, data: dict) -> dict:
    c = _get(db, code)
    if not c:
        raise HTTPException(status_code=404, detail="Cupom não encontrado.")
    _apply(db, c, data)
    db.commit()
    db.refresh(c)
    return _serialize(db, c)


def delete_coupon(db: Session, code: str) -> dict:
    c = _get(db, code)
    if c:
        db.delete(c)
        db.commit()
    return {"message": "Cupom removido"}
