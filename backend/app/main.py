import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.dependencies import get_db  # noqa: F401  (garante import do pacote)
from app import models  # noqa: F401  (registra os modelos no metadata)
from app.routers import account, admin, auth, banners, catalog, favorites, orders, reviews
from app.seed import seed_admin, seed_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brasilminis")

app = FastAPI(title="Brasil Minis API")

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(orders.router)
app.include_router(account.router)
app.include_router(banners.router)
app.include_router(admin.router)


@app.get("/api/")
def root():
    return {"message": "Brasil Minis API online"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


origins = settings.CORS_ORIGINS or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    # Preview/dev: cria tabelas automaticamente. Produção (VPS): use Alembic.
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_admin(db)
        seed_data(db)
        logger.info("Startup concluído: admin e seed verificados.")
    finally:
        db.close()
