import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from db import db, client
from security import hash_password, verify_password
from seed import seed_data

from routers import auth, catalog, reviews, favorites, orders, account, banners, admin

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
async def root():
    return {"message": "Brasil Minis API online"}


origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@brasilminis.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "name": "Administrador",
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "phone": "",
            "newsletter": False,
            "addresses": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Admin seeded: %s", admin_email)
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email},
                                  {"$set": {"password_hash": hash_password(admin_password)}})


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.password_reset_tokens.create_index("token")
    await db.login_attempts.create_index("identifier")
    await db.products.create_index("slug")
    await db.products.create_index("id")
    await db.categories.create_index("slug")
    await db.brands.create_index("slug")
    await seed_admin()
    await seed_data()


@app.on_event("shutdown")
async def shutdown():
    client.close()
