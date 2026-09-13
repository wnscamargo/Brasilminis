import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AdminAuditLog


def log(db: Session, event: str, admin: dict | None = None, order_id: str | None = None, detail: dict | None = None, commit: bool = False) -> None:
    """Registra um evento administrativo (sem segredos)."""
    db.add(AdminAuditLog(
        id=str(uuid.uuid4()),
        event=event,
        order_id=order_id,
        admin_id=(admin or {}).get("id"),
        admin_email=(admin or {}).get("email"),
        detail=detail or {},
        created_at=datetime.now(timezone.utc).isoformat(),
    ))
    if commit:
        db.commit()
