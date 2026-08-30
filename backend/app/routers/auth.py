import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.dependencies import _public_user, get_current_user, get_db
from app.models import LoginAttempt, PasswordResetToken, User
from app.schemas import ForgotPasswordInput, LoginInput, RegisterInput, ResetPasswordInput

router = APIRouter(prefix="/api/auth", tags=["auth"])

MAX_ATTEMPTS = 5
LOCK_MINUTES = 15


def _client_ip(request: Request) -> str:
    # Atrás do ingress/proxy K8s, request.client.host é o IP do proxy (rotaciona).
    # Use o primeiro hop de X-Forwarded-For como IP real do cliente.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _set_auth_cookies(response: Response, user_id: str, email: str):
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    response.set_cookie("access_token", access, httponly=True, secure=True,
                        samesite="none", max_age=86400, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True,
                        samesite="none", max_age=604800, path="/")


@router.post("/register")
def register(payload: RegisterInput, response: Response, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado")
    user = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        role="customer",
        phone="",
        newsletter=payload.newsletter,
        addresses=[],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _set_auth_cookies(response, user.id, email)
    return _public_user(user)


@router.post("/login")
def login(payload: LoginInput, response: Response, request: Request, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    ip = _client_ip(request)
    identifier = f"{ip}:{email}"
    now = datetime.now(timezone.utc)

    attempt = db.get(LoginAttempt, identifier)
    if (
        attempt
        and (attempt.count or 0) >= MAX_ATTEMPTS
        and attempt.locked_until
        and datetime.fromisoformat(attempt.locked_until) > now
    ):
        raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em alguns minutos.")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        if attempt:
            # Se a janela de bloqueio expirou, zera o contador.
            if attempt.locked_until and datetime.fromisoformat(attempt.locked_until) <= now:
                attempt.count = 0
                attempt.locked_until = None
            attempt.count = (attempt.count or 0) + 1
            # Só trava quando atinge o limite (não renova o timer a cada tentativa).
            if attempt.count >= MAX_ATTEMPTS:
                attempt.locked_until = (now + timedelta(minutes=LOCK_MINUTES)).isoformat()
        else:
            attempt = LoginAttempt(identifier=identifier, count=1, locked_until=None)
            db.add(attempt)
        db.commit()
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

    if attempt:
        db.delete(attempt)
        db.commit()
    _set_auth_cookies(response, user.id, email)
    return _public_user(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logout efetuado"}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Sem token de atualização")
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        user = db.get(User, payload["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        access = create_access_token(user.id, user.email)
        response.set_cookie("access_token", access, httponly=True, secure=True,
                            samesite="none", max_age=86400, path="/")
        return {"message": "ok"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordInput, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user:
        token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            token=token,
            user_id=user.id,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            used=False,
        ))
        db.commit()
        print(f"[PASSWORD RESET] Link para {email}: /reset-password?token={token}")
    return {"message": "Se o e-mail existir, enviaremos instruções de recuperação."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordInput, db: Session = Depends(get_db)):
    record = db.get(PasswordResetToken, payload.token)
    if not record or record.used:
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado")
    if datetime.fromisoformat(record.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expirado")
    user = db.get(User, record.user_id)
    if user:
        user.password_hash = hash_password(payload.password)
    record.used = True
    db.commit()
    return {"message": "Senha redefinida com sucesso"}
