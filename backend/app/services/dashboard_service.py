"""Zeragem administrativa (baseline) do Dashboard.

NÃO apaga pedidos/pagamentos/produtos/estoque/histórico. Apenas grava um marco
(dashboard_reset_at). Os indicadores acumulados passam a considerar somente eventos
posteriores ao marco. Relatórios que selecionam explicitamente períodos anteriores
(custom) continuam acessíveis.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import DashboardReset
from app.services import audit_service


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_baseline(db: Session) -> str | None:
    """Marco atual (ISO) ou None se nunca houve zeragem."""
    row = db.query(DashboardReset).order_by(DashboardReset.created_at.desc()).first()
    return row.reset_at if row else None


def list_resets(db: Session) -> list:
    rows = db.query(DashboardReset).order_by(DashboardReset.created_at.desc()).all()
    return [{
        "id": r.id,
        "reset_at": r.reset_at,
        "previous_reset_at": r.previous_reset_at,
        "admin_email": r.admin_email,
        "reason": r.reason,
        "created_at": r.created_at,
    } for r in rows]


def reset(db: Session, admin: dict, reason: str, confirm: str) -> dict:
    if (confirm or "").strip() != "ZERAR DASHBOARD":
        raise HTTPException(status_code=400, detail='Confirmação inválida. Digite exatamente "ZERAR DASHBOARD".')
    if not (reason or "").strip():
        raise HTTPException(status_code=400, detail="Informe o motivo da zeragem.")

    previous = get_baseline(db)
    new_marker = _now()

    audit_service.log(db, "DASHBOARD_RESET_REQUESTED", admin, None, {
        "reason": reason.strip(), "previous_baseline": previous,
    })

    import uuid
    row = DashboardReset(
        id=str(uuid.uuid4()),
        reset_at=new_marker,
        previous_reset_at=previous,
        admin_id=admin.get("id"),
        admin_email=admin.get("email"),
        reason=reason.strip(),
        created_at=new_marker,
    )
    db.add(row)

    audit_service.log(db, "DASHBOARD_RESET_COMPLETED", admin, None, {
        "reason": reason.strip(), "previous_baseline": previous, "new_baseline": new_marker,
    })
    db.commit()
    return {"ok": True, "baseline": new_marker, "previous_baseline": previous}
