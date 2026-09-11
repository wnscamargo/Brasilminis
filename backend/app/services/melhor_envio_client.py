"""Cliente HTTP do Melhor Envio: OAuth, refresh com 1 retry, timeouts, logs sanitizados.

NUNCA loga Authorization, tokens, code ou PII. Erros são sanitizados para o cliente
final; detalhes ficam disponíveis apenas para diagnóstico admin.
"""
import logging
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt, encrypt
from app.models import MelhorEnvioToken

logger = logging.getLogger("melhor_envio")

TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class MelhorEnvioUnavailable(Exception):
    """Falha de rede/timeout/5xx — API indisponível (não derruba o Brasil Minis)."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _headers(access_token: str | None = None) -> dict:
    h = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": settings.MELHOR_ENVIO_USER_AGENT,
    }
    if access_token:
        h["Authorization"] = f"Bearer {access_token}"
    return h


def get_token_row(db: Session) -> MelhorEnvioToken | None:
    return db.get(MelhorEnvioToken, 1)


def save_token_data(db: Session, data: dict, account_email: str | None = None) -> MelhorEnvioToken:
    row = db.get(MelhorEnvioToken, 1)
    if not row:
        row = MelhorEnvioToken(id=1)
        db.add(row)
    row.access_token_enc = encrypt(data["access_token"])
    if data.get("refresh_token"):
        row.refresh_token_enc = encrypt(data["refresh_token"])
    row.expires_at = _iso(_now() + timedelta(seconds=int(data.get("expires_in", 2592000))))
    row.scope = data.get("scope") or row.scope
    row.token_type = data.get("token_type") or "Bearer"
    row.environment = settings.MELHOR_ENVIO_ENV
    row.last_error = None
    if account_email:
        row.account_email = account_email
    row.updated_at = _iso(_now())
    db.commit()
    db.refresh(row)
    return row


def exchange_code(db: Session, code: str) -> MelhorEnvioToken:
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.MELHOR_ENVIO_CLIENT_ID,
        "client_secret": settings.MELHOR_ENVIO_CLIENT_SECRET,
        "redirect_uri": settings.MELHOR_ENVIO_REDIRECT_URI,
        "code": code,
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.post(f"{settings.MELHOR_ENVIO_BASE_URL}/oauth/token", headers=_headers(), json=payload)
    except httpx.HTTPError as e:
        logger.warning("ME token exchange network error: %s", type(e).__name__)
        raise MelhorEnvioUnavailable()
    if r.is_error:
        logger.warning("ME token exchange failed: status=%s", r.status_code)
        raise HTTPException(status_code=400, detail="Falha ao conectar com o Melhor Envio. Verifique o aplicativo Sandbox e a redirect URI.")
    return save_token_data(db, r.json())


def _refresh(db: Session, row: MelhorEnvioToken) -> MelhorEnvioToken:
    refresh_token = decrypt(row.refresh_token_enc)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Conta Melhor Envio desconectada. Reconecte.")
    payload = {
        "grant_type": "refresh_token",
        "client_id": settings.MELHOR_ENVIO_CLIENT_ID,
        "client_secret": settings.MELHOR_ENVIO_CLIENT_SECRET,
        "refresh_token": refresh_token,
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.post(f"{settings.MELHOR_ENVIO_BASE_URL}/oauth/token", headers=_headers(), json=payload)
    except httpx.HTTPError:
        raise MelhorEnvioUnavailable()
    if r.is_error:
        row.last_error = f"refresh_failed:{r.status_code}"
        db.commit()
        raise HTTPException(status_code=401, detail="Sessão do Melhor Envio expirada. Reconecte a conta.")
    return save_token_data(db, r.json())


def _valid_access_token(db: Session) -> tuple[MelhorEnvioToken, str]:
    row = get_token_row(db)
    if not row or not row.access_token_enc:
        raise HTTPException(status_code=400, detail="Melhor Envio não conectado.")
    # Refresh proativo com margem de 60s.
    try:
        exp = datetime.fromisoformat(row.expires_at) if row.expires_at else _now()
    except Exception:
        exp = _now()
    if exp <= _now() + timedelta(seconds=60):
        row = _refresh(db, row)
    return row, decrypt(row.access_token_enc)


def api_request(db: Session, method: str, path: str, json: dict | None = None, params: dict | None = None):
    """Chamada autenticada à API v2 com no máximo 1 retry após refresh em 401."""
    row, access = _valid_access_token(db)
    url = f"{settings.MELHOR_ENVIO_BASE_URL}{path}"
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.request(method, url, headers=_headers(access), json=json, params=params)
            if r.status_code == 401:
                row = _refresh(db, row)
                access = decrypt(row.access_token_enc)
                r = c.request(method, url, headers=_headers(access), json=json, params=params)
    except httpx.HTTPError as e:
        logger.warning("ME api network error path=%s err=%s", path, type(e).__name__)
        raise MelhorEnvioUnavailable()
    if r.status_code >= 500:
        logger.warning("ME api 5xx path=%s status=%s", path, r.status_code)
        raise MelhorEnvioUnavailable()
    if r.is_error:
        logger.warning("ME api error path=%s status=%s", path, r.status_code)
        detail = "Não foi possível completar a operação no Melhor Envio."
        try:
            body = r.json()
            if isinstance(body, dict) and body.get("message"):
                detail = f"Melhor Envio: {body['message']}"
        except Exception:
            pass
        raise HTTPException(status_code=r.status_code, detail=detail)
    try:
        return r.json()
    except Exception:
        return {"raw": r.text}
