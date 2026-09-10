from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_db
from app.schemas import SiteConfigInput, SiteSettingsInput
from app.services.site_service import (
    admin_config,
    delete_logo,
    get_settings,
    public_config,
    public_status,
    save_logo,
    update_config,
    update_settings,
)
from app.utils import to_dict

router = APIRouter(prefix="/api", tags=["site"])


# ---------- Modo em construção ----------
@router.get("/site-status")
def site_status(db: Session = Depends(get_db)):
    return public_status(db)


@router.get("/admin/site-settings")
def admin_get_site_settings(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return to_dict(get_settings(db))


@router.put("/admin/site-settings")
def admin_update_site_settings(
    payload: SiteSettingsInput,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_settings(db, payload.model_dump(), admin.get("email"))


# ---------- Identidade visual global ----------
@router.get("/site-config")
def site_config(db: Session = Depends(get_db)):
    """Público e leve (logo + tamanho). Consumido uma vez no boot."""
    return public_config(db)


@router.get("/admin/site-config")
def admin_get_site_config(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return admin_config(db)


@router.put("/admin/site-config")
def admin_update_site_config(
    payload: SiteConfigInput,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_config(db, payload.logo_width, payload.branding, admin.get("email"))


@router.post("/admin/site-config/logo")
async def admin_upload_logo(
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    content = await file.read()
    return save_logo(db, file.content_type, content, admin.get("email"))


@router.delete("/admin/site-config/logo")
def admin_delete_logo(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return delete_logo(db, admin.get("email"))
