"""Exclusão protegida (soft delete) e restauração de clientes.

- Nunca apaga fisicamente pedidos/pagamentos/envios/cupons — apenas marca o cliente.
- Idempotente: excluir 2x não duplica efeitos nem auditoria de exclusão.
- Anonimização LGPD opcional: apaga PII (nome/e-mail/CPF/telefone/endereços) e libera
  e-mail/CPF para reuso; o histórico operacional permanece via snapshots do pedido.
- CPF nunca é exposto por completo em logs/auditoria.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Order, User
from app.services import audit_service


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cpf_tail(cpf: str | None) -> str | None:
    """Traço de auditoria SEM expor o CPF (apenas 2 últimos dígitos, mascarado)."""
    if not cpf:
        return None
    return f"***.***.***-{cpf[-2:]}"


def _public_customer(db: Session, u: User) -> dict:
    orders_count = db.query(func.count(Order.id)).filter(Order.user_id == u.id).scalar() or 0
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "phone": u.phone or "",
        "cpf": u.cpf or "",
        "newsletter": bool(u.newsletter),
        "orders_count": orders_count,
        "created_at": u.created_at,
        "deleted_at": u.deleted_at,
        "deleted_by": u.deleted_by,
        "delete_reason": u.delete_reason,
        "anonymized_at": u.anonymized_at,
    }


def list_customers(db: Session, scope: str = "active") -> list:
    q = db.query(User).filter(User.role == "customer")
    if scope == "active":
        q = q.filter(User.deleted_at.is_(None))
    elif scope == "deleted":
        q = q.filter(User.deleted_at.isnot(None))
    # scope == "all" -> sem filtro
    return [_public_customer(db, u) for u in q.order_by(User.created_at.desc()).all()]


def delete_customer(db: Session, user_id: str, admin: dict, reason: str, confirm: str, anonymize: bool = False) -> dict:
    if (confirm or "").strip() != "EXCLUIR":
        raise HTTPException(status_code=400, detail='Confirmação inválida. Digite exatamente "EXCLUIR".')
    if not (reason or "").strip():
        raise HTTPException(status_code=400, detail="Informe o motivo da exclusão.")

    u = db.get(User, user_id)
    if not u or u.role != "customer":
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    audit_service.log(db, "CUSTOMER_DELETE_REQUESTED", admin, None, {
        "customer_id": u.id, "email": u.email, "cpf_tail": _cpf_tail(u.cpf), "reason": reason.strip(),
    })

    # Idempotência: já excluído -> não repete efeitos/auditoria de exclusão
    if u.deleted_at:
        db.commit()
        return {"ok": True, "already_deleted": True, "customer": _public_customer(db, u)}

    orders_count = db.query(func.count(Order.id)).filter(Order.user_id == u.id).scalar() or 0

    u.deleted_at = _now()
    u.deleted_by = admin.get("email")
    u.delete_reason = reason.strip()

    if anonymize:
        u.name = "Cliente removido"
        u.email = f"deleted+{u.id}@anonimizado.local"
        u.cpf = None
        u.phone = ""
        u.addresses = []
        u.newsletter = False
        u.anonymized_at = _now()

    audit_service.log(db, "CUSTOMER_DELETED", admin, None, {
        "customer_id": u.id,
        "reason": reason.strip(),
        "anonymized": bool(anonymize),
        "orders_preserved": orders_count,
    })
    db.commit()
    db.refresh(u)
    return {"ok": True, "customer": _public_customer(db, u), "orders_preserved": orders_count}


def restore_customer(db: Session, user_id: str, admin: dict) -> dict:
    u = db.get(User, user_id)
    if not u or u.role != "customer":
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    if not u.deleted_at:
        # Idempotência: já ativo
        return {"ok": True, "already_active": True, "customer": _public_customer(db, u)}

    # Conflito de e-mail/CPF com outro cliente ATIVO antes de restaurar (sem alterar dados)
    conflict_email = db.query(User).filter(
        func.lower(User.email) == (u.email or "").lower(), User.id != u.id, User.deleted_at.is_(None)
    ).first()
    if conflict_email:
        raise HTTPException(status_code=409, detail="Não é possível restaurar: o e-mail já está em uso por outro cliente ativo.")
    if u.cpf:
        conflict_cpf = db.query(User).filter(
            User.cpf == u.cpf, User.id != u.id, User.deleted_at.is_(None)
        ).first()
        if conflict_cpf:
            raise HTTPException(status_code=409, detail="Não é possível restaurar: o CPF já está em uso por outro cliente ativo.")

    u.deleted_at = None
    u.deleted_by = None
    u.delete_reason = None
    audit_service.log(db, "CUSTOMER_RESTORED", admin, None, {
        "customer_id": u.id, "email": u.email, "was_anonymized": bool(u.anonymized_at),
    })
    db.commit()
    db.refresh(u)
    return {"ok": True, "customer": _public_customer(db, u)}
