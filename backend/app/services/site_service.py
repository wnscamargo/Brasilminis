from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import SiteSettings
from app.utils import to_dict


def get_settings(db: Session) -> SiteSettings:
    """Retorna a linha única de configuração (cria com defaults se não existir)."""
    s = db.get(SiteSettings, 1)
    if s is None:
        s = SiteSettings(id=1, maintenance_enabled=False)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def public_status(db: Session) -> dict:
    """Somente informações PÚBLICAS (nada administrativo/sensível)."""
    s = get_settings(db)
    return {
        "maintenance_enabled": bool(s.maintenance_enabled),
        "title": s.maintenance_title or "",
        "subtitle": s.maintenance_subtitle or "",
        "message": s.maintenance_message or "",
        "launch_date": s.launch_date,
        "show_countdown": bool(s.show_countdown),
        "whatsapp_url": s.whatsapp_url if s.show_whatsapp else None,
        "instagram_url": s.instagram_url if s.show_instagram else None,
        "show_whatsapp": bool(s.show_whatsapp and s.whatsapp_url),
        "show_instagram": bool(s.show_instagram and s.instagram_url),
    }


def update_settings(db: Session, data: dict, updated_by: str | None) -> dict:
    s = get_settings(db)
    for key, value in data.items():
        setattr(s, key, value)
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return to_dict(s)
