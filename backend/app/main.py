import logging
import os
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.dependencies import get_db  # noqa: F401  (garante import do pacote)
from app import models  # noqa: F401  (registra os modelos no metadata)
from app.routers import account, admin, auth, banners, catalog, favorites, melhor_envio, orders, payments, reviews, site
from app.seed import seed_admin, seed_data
from app.services import melhor_envio_auth_service as auth_service

BACKEND_DIR = Path(__file__).resolve().parents[1]

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
app.include_router(site.router)
app.include_router(admin.router)
app.include_router(melhor_envio.router)
app.include_router(payments.router)

# Uploads persistentes (identidade visual, imagens de produto) servidos sob /api/uploads.
os.makedirs(os.path.join(settings.UPLOADS_DIR, "branding"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOADS_DIR, "products"), exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")


@app.get("/api/")
def root():
    return {"message": "Brasil Minis API online"}


@app.get("/api/health")
def health(response: Response):
    """Health operacional (sem dados sensíveis).

    200 = app + banco + migrations OK. 503 = dependência crítica indisponível.
    """
    database = "down"
    migration = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            database = "ok"
            current = MigrationContext.configure(conn).get_current_revision()
        cfg = Config()
        cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        head = ScriptDirectory.from_config(cfg).get_current_head()
        migration = "current" if current == head else "out_of_date"
    except Exception:
        # Não expõe stack trace nem detalhes internos.
        pass

    healthy = database == "ok" and migration == "current"
    if not healthy:
        response.status_code = 503

    # Melhor Envio é OPCIONAL: nunca transforma em 503.
    me_state = "not_configured"
    if settings.MELHOR_ENVIO_CONFIGURED:
        try:
            db = SessionLocal()
            try:
                st = auth_service.status(db).get("status")
                me_state = "connected" if st == "connected" else (
                    "unavailable" if st in ("error", "token_expired") else "not_configured"
                )
            finally:
                db.close()
        except Exception:
            me_state = "unavailable"

    return {
        "status": "ok" if healthy else "degraded",
        "database": database,
        "migration": migration,
        "melhor_envio": me_state,
        "mercado_pago": _mp_state(),
    }


def _mp_state() -> str:
    try:
        db = SessionLocal()
        try:
            from app.services import mercado_pago_service as mp
            st = mp.status(db).get("status")
            if st == "connected":
                return "connected"
            if st in ("not_configured",):
                return "not_configured"
            if st in ("error",):
                return "unavailable"
            return "configured"
        finally:
            db.close()
    except Exception:
        return "not_configured"


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
    import time
    from sqlalchemy import inspect as sa_inspect

    # Aguarda o banco ficar disponível (em preview o Postgres pode subir logo após).
    for _ in range(20):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception:
            time.sleep(2)
    else:
        # Sobe em modo degradado: /api/health retornará 503 até o banco voltar.
        logger.error("Banco indisponível no startup — app em modo degradado (health 503).")
        return

    # Fallback opcional (NUNCA usar em produção multi-worker). Migrations = Alembic.
    if settings.AUTO_CREATE_TABLES:
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

    # Aguarda as migrations serem aplicadas (deploy.sh na VPS / pg-bootstrap no preview).
    for _ in range(20):
        try:
            if sa_inspect(engine).has_table("users"):
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        logger.error("Tabelas ausentes (migrations não aplicadas) — modo degradado.")
        return

    try:
        db = SessionLocal()
        try:
            seed_admin(db)
            seed_data(db)
            logger.info("Startup concluído: seed verificado.")
        finally:
            db.close()
    except Exception as exc:
        logger.error("Falha no seed: %s", type(exc).__name__)
