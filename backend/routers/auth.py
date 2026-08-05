import os
import secrets
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from fastapi import APIRouter, Response, Request, HTTPException, Depends

from db import db
from deps import get_current_user
from models import RegisterInput, LoginInput, ForgotPasswordInput, ResetPasswordInput
from security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

MAX_ATTEMPTS = 5
LOCK_MINUTES = 15


def _set_auth_cookies(response: Response, user_id: str, email: str):
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    response.set_cookie("access_token", access, httponly=True, secure=True,
                        samesite="none", max_age=86400, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True,
                        samesite="none", max_age=604800, path="/")


def _public_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]) if "_id" in user else user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role", "customer"),
        "phone": user.get("phone", ""),
        "newsletter": user.get("newsletter", False),
    }


@router.post("/register")
async def register(payload: RegisterInput, response: Response):
    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado")
    doc = {
        "name": payload.name,
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": "customer",
        "phone": "",
        "newsletter": payload.newsletter,
        "addresses": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    res = await db.users.insert_one(doc)
    _set_auth_cookies(response, str(res.inserted_id), email)
    doc["_id"] = res.inserted_id
    return _public_user(doc)


@router.post("/login")
async def login(payload: LoginInput, response: Response, request: Request):
    email = payload.email.lower().strip()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"

    attempt = await db.login_attempts.find_one({"identifier": identifier})
    if attempt and attempt.get("count", 0) >= MAX_ATTEMPTS:
        locked_until = attempt.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em alguns minutos.")

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        now = datetime.now(timezone.utc)
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"locked_until": (now + timedelta(minutes=LOCK_MINUTES)).isoformat()}},
            upsert=True,
        )
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

    await db.login_attempts.delete_one({"identifier": identifier})
    _set_auth_cookies(response, str(user["_id"]), email)
    return _public_user(user)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logout efetuado"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return _public_user(user)


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Sem token de atualização")
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        access = create_access_token(str(user["_id"]), user["email"])
        response.set_cookie("access_token", access, httponly=True, secure=True,
                            samesite="none", max_age=86400, path="/")
        return {"message": "ok"}
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordInput):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if user:
        token = secrets.token_urlsafe(32)
        await db.password_reset_tokens.insert_one({
            "token": token,
            "user_id": str(user["_id"]),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "used": False,
        })
        print(f"[PASSWORD RESET] Link para {email}: /reset-password?token={token}")
    return {"message": "Se o e-mail existir, enviaremos instruções de recuperação."}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordInput):
    record = await db.password_reset_tokens.find_one({"token": payload.token})
    if not record or record.get("used"):
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado")
    if datetime.fromisoformat(record["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expirado")
    await db.users.update_one(
        {"_id": ObjectId(record["user_id"])},
        {"$set": {"password_hash": hash_password(payload.password)}},
    )
    await db.password_reset_tokens.update_one({"token": payload.token}, {"$set": {"used": True}})
    return {"message": "Senha redefinida com sucesso"}
