from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import MelhorEnvioShipment, Order, Product
from app.services import audit_service
from app.utils import to_dict

# Estados logísticos que impedem exclusão (operação comprometida no Melhor Envio)
COMMITTED_SHIPMENT = {"in_cart", "purchased", "generated", "posted", "delivered"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_orders(db: Session, scope: str = "active") -> list:
    q = db.query(Order)
    if scope == "active":
        q = q.filter(Order.deleted_at.is_(None))
    elif scope == "deleted":
        q = q.filter(Order.deleted_at.isnot(None))
    # scope == "all" -> sem filtro
    return [to_dict(o) for o in q.order_by(Order.created_at.desc()).all()]


def delete_order(db: Session, order_id: str, admin: dict, reason: str, confirm: str) -> dict:
    """Soft delete protegido, idempotente, com devolução de estoque exatamente 1x."""
    if (confirm or "").strip() != "EXCLUIR":
        raise HTTPException(status_code=400, detail='Confirmação inválida. Digite exatamente "EXCLUIR".')
    if not (reason or "").strip():
        raise HTTPException(status_code=400, detail="Informe o motivo da exclusão.")

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    audit_service.log(db, "ORDER_DELETE_REQUESTED", admin, order.id, {"reason": reason})

    # Idempotência: já excluído -> não repete estoque/auditoria de exclusão
    if order.deleted_at:
        db.commit()
        return {"ok": True, "already_deleted": True, "order": to_dict(order)}

    prev = {
        "status": order.status,
        "payment_status": order.payment_status,
        "payment_provider": order.payment_provider,
    }

    # Proteção Mercado Pago: pagamento real confirmado não pode ser excluído
    if order.payment_provider == "mercado_pago" and order.payment_status == "approved":
        audit_service.log(db, "ORDER_DELETE_BLOCKED", admin, order.id, {"reason": reason, "cause": "mp_paid", **prev}, commit=True)
        raise HTTPException(status_code=409, detail="Pedido com pagamento CONFIRMADO no Mercado Pago. Trate o cancelamento/estorno financeiro antes de excluir.")

    # Proteção Melhor Envio: envio comprometido
    sh = db.query(MelhorEnvioShipment).filter(MelhorEnvioShipment.order_id == order.id).first()
    if sh and (sh.internal_status in COMMITTED_SHIPMENT):
        audit_service.log(db, "ORDER_DELETE_BLOCKED", admin, order.id, {"reason": reason, "cause": "me_shipment", "shipment_status": sh.internal_status, **prev}, commit=True)
        raise HTTPException(status_code=409, detail=f"Há operação logística ativa no Melhor Envio (status: {sh.internal_status}). Trate o envio antes de excluir.")

    # Soft delete
    order.deleted_at = _now()
    order.deleted_by = admin.get("email")
    order.delete_reason = reason.strip()

    # Devolução de estoque exatamente 1x
    returned = []
    if not order.stock_returned:
        for it in (order.items or []):
            pid = it.get("product_id")
            qty = it.get("quantity") or 0
            if pid and qty:
                db.query(Product).filter(Product.id == pid).update(
                    {Product.stock: Product.stock + qty}, synchronize_session=False
                )
                returned.append({"product_id": pid, "quantity": qty})
        order.stock_returned = True

    audit_service.log(db, "ORDER_DELETED", admin, order.id, {
        "reason": reason.strip(), "prev": prev, "stock_returned": returned,
    })
    db.commit()
    db.refresh(order)
    return {"ok": True, "order": to_dict(order), "stock_returned": returned}
