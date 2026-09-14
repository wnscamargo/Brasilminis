from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_db
from app.services import superfrete_service as sf

router = APIRouter(prefix="/api", tags=["superfrete"])


@router.get("/superfrete/status")
def public_status(db: Session = Depends(get_db)):
    return sf.public_status(db)


@router.get("/admin/superfrete/config")
def admin_config(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.admin_config(db)


@router.put("/admin/superfrete/config")
def admin_update_config(payload: dict, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.update_config(db, payload, admin)


@router.post("/admin/superfrete/test")
def admin_test(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.test_connection(db, admin)


@router.post("/admin/superfrete/disconnect")
def admin_disconnect(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.disconnect(db, admin)
