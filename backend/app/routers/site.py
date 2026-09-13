from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_db
from app.schemas import SiteConfigInput, SiteContentInput, SiteSettingsInput, SocialLinksInput
from app.services.site_service import (
    admin_config,
    admin_content,
    admin_social,
    delete_logo,
    get_settings,
    public_config,
    public_content,
    public_status,
    save_logo,
    update_config,
    update_content,
    update_settings,
    update_social,
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


# ---------- Conteúdo institucional (Sobre, Contato, Trocas, Frete) ----------
@router.get("/site-content")
def site_content(db: Session = Depends(get_db)):
    """Público: páginas ativas + redes sociais ativas."""
    return public_content(db)


@router.get("/admin/site-content")
def admin_get_site_content(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return admin_content(db)


@router.put("/admin/site-content")
def admin_update_site_content(
    payload: SiteContentInput,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_content(db, payload.model_dump(exclude_unset=True), admin.get("email"))


# ---------- Redes sociais ----------
@router.get("/admin/social-links")
def admin_get_social(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return admin_social(db)


@router.put("/admin/social-links")
def admin_update_social(
    payload: SocialLinksInput,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_social(db, payload.model_dump(exclude_unset=True), admin.get("email"))
