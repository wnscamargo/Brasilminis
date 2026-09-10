from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_db
from app.schemas import SiteSettingsInput
from app.services.site_service import get_settings, public_status, update_settings
from app.utils import to_dict

router = APIRouter(prefix="/api", tags=["site"])


@router.get("/site-status")
def site_status(db: Session = Depends(get_db)):
    """Endpoint público leve (consumido no boot do frontend)."""
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
