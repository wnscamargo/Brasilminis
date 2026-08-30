from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Banner
from app.utils import to_dict

router = APIRouter(prefix="/api", tags=["banners"])


@router.get("/banners")
def list_banners(db: Session = Depends(get_db)):
    banners = (
        db.query(Banner)
        .filter(Banner.active.is_(True))
        .order_by(Banner.position.asc())
        .limit(50)
        .all()
    )
    return [to_dict(b) for b in banners]
