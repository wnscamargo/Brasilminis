"""Catálogo administrável de badges (estilos). Associação ao produto via Product.badges (JSONB)."""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Badge, Product
from app.utils import to_dict


def _now():
    return datetime.now(timezone.utc).isoformat()


def list_badges(db: Session, only_active: bool = False) -> list:
    q = db.query(Badge)
    if only_active:
        q = q.filter(Badge.active.is_(True))
    rows = q.order_by(Badge.sort_order.asc(), Badge.priority.desc(), Badge.text.asc()).all()
    return [to_dict(b) for b in rows]


def _usage_count(db: Session, text: str) -> int:
    return db.query(Product).filter(Product.badges.contains([text])).count()


def create_badge(db: Session, data: dict) -> dict:
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Informe o texto do badge.")
    if db.query(Badge).filter(Badge.text == text).first():
        raise HTTPException(status_code=400, detail="Já existe um badge com esse texto.")
    b = Badge(
        id=str(uuid.uuid4()), text=text,
        bg_color=data.get("bg_color") or "#FFC107",
        text_color=data.get("text_color") or "#111111",
        icon=data.get("icon") or "",
        priority=data.get("priority") or 0,
        sort_order=data.get("sort_order") or 0,
        active=data.get("active", True),
        created_at=_now(), updated_at=_now(),
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return to_dict(b)


def update_badge(db: Session, badge_id: str, data: dict) -> dict:
    b = db.get(Badge, badge_id)
    if not b:
        raise HTTPException(status_code=404, detail="Badge não encontrado.")
    new_text = (data.get("text") or "").strip()
    if new_text and new_text != b.text:
        if db.query(Badge).filter(Badge.text == new_text, Badge.id != b.id).first():
            raise HTTPException(status_code=400, detail="Já existe um badge com esse texto.")
        # Propaga o novo texto para os produtos que já usam o texto antigo (mantém associação)
        for p in db.query(Product).filter(Product.badges.contains([b.text])).all():
            p.badges = [new_text if x == b.text else x for x in (p.badges or [])]
        b.text = new_text
    for k in ("bg_color", "text_color", "icon", "priority", "sort_order", "active"):
        if k in data and data[k] is not None:
            setattr(b, k, data[k])
    b.updated_at = _now()
    db.commit()
    db.refresh(b)
    return to_dict(b)


def delete_badge(db: Session, badge_id: str) -> dict:
    b = db.get(Badge, badge_id)
    if not b:
        return {"message": "Badge removido"}
    used = _usage_count(db, b.text)
    if used > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Badge em uso por {used} produto(s). Desative-o ou remova a associação antes de excluir.",
        )
    db.delete(b)
    db.commit()
    return {"message": "Badge removido"}
