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


# ---------- Identidade visual global ----------
import io
import os
import uuid

from fastapi import HTTPException

ALLOWED_LOGO = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
MAX_LOGO_BYTES = 3 * 1024 * 1024
MAX_LOGO_DIM = 5000


def public_config(db: Session) -> dict:
    """Somente a identidade visual PÚBLICA (logo + tamanho)."""
    s = get_settings(db)
    return {
        "logo_url": s.logo_url or None,
        "logo_width": s.logo_width or 200,
        "store_name": (s.branding or {}).get("store_name"),
    }


def admin_config(db: Session) -> dict:
    s = get_settings(db)
    return {
        "logo_url": s.logo_url or None,
        "logo_width": s.logo_width or 200,
        "branding": s.branding or {},
        "updated_at": s.updated_at,
        "updated_by": s.updated_by,
    }


def update_config(db: Session, logo_width: int, branding: dict | None, updated_by: str | None) -> dict:
    s = get_settings(db)
    s.logo_width = max(60, min(500, int(logo_width or 200)))
    if branding is not None:
        merged = dict(s.branding or {})
        merged.update(branding)
        s.branding = merged
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return admin_config(db)


def _branding_dir() -> str:
    from app.core.config import settings
    d = os.path.join(settings.UPLOADS_DIR, "branding")
    os.makedirs(d, exist_ok=True)
    return d


def _remove_if_custom(logo_url: str | None):
    if logo_url and logo_url.startswith("/api/uploads/branding/"):
        name = os.path.basename(logo_url)
        path = os.path.join(_branding_dir(), name)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass


def save_logo(db: Session, content_type: str, content: bytes, updated_by: str | None) -> dict:
    from PIL import Image

    ext = ALLOWED_LOGO.get(content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="Formato inválido. Use PNG, JPEG ou WEBP.")
    if len(content) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máx. 3MB).")
    try:
        Image.open(io.BytesIO(content)).verify()
        w, h = Image.open(io.BytesIO(content)).size
    except Exception:
        raise HTTPException(status_code=400, detail="Imagem inválida ou corrompida.")
    if w > MAX_LOGO_DIM or h > MAX_LOGO_DIM or w < 1 or h < 1:
        raise HTTPException(status_code=400, detail="Dimensões da imagem fora do permitido.")

    name = f"logo-{uuid.uuid4().hex}.{ext}"  # nome próprio (sem confiar no original)
    with open(os.path.join(_branding_dir(), name), "wb") as f:
        f.write(content)

    s = get_settings(db)
    _remove_if_custom(s.logo_url)
    s.logo_url = f"/api/uploads/branding/{name}"
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return public_config(db)


def delete_logo(db: Session, updated_by: str | None) -> dict:
    s = get_settings(db)
    _remove_if_custom(s.logo_url)
    s.logo_url = None  # volta ao fallback (logo padrão)
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return public_config(db)
