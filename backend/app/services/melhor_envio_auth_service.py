"""OAuth/config do Melhor Envio: URL de autorização, status, teste, desconexão, remetente."""
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import MelhorEnvioSender, MelhorEnvioToken
from app.services import melhor_envio_client as client
from app.services.melhor_envio_client import MelhorEnvioUnavailable
from app.utils import to_dict

SCOPES = "shipping-calculate cart-write cart-read shipping-checkout shipping-generate shipping-print shipping-tracking shipping-cancel"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_auth_url(db: Session) -> dict:
    if not settings.MELHOR_ENVIO_CONFIGURED:
        raise ValueError("Melhor Envio não configurado (client_id/secret/redirect).")
    state = secrets.token_urlsafe(32)
    row = db.get(MelhorEnvioToken, 1)
    if not row:
        row = MelhorEnvioToken(id=1, environment=settings.MELHOR_ENVIO_ENV)
        db.add(row)
    row.pending_state = state
    row.updated_at = _now_iso()
    db.commit()
    q = urlencode({
        "client_id": settings.MELHOR_ENVIO_CLIENT_ID,
        "redirect_uri": settings.MELHOR_ENVIO_REDIRECT_URI,
        "response_type": "code",
        "state": state,
        "scope": SCOPES,
    })
    return {"authorization_url": f"{settings.MELHOR_ENVIO_BASE_URL}/oauth/authorize?{q}", "state": state}


def exchange_code(db: Session, code: str):
    """Delega a troca de code por token ao cliente HTTP."""
    return client.exchange_code(db, code)


def validate_state(db: Session, state: str) -> bool:
    row = db.get(MelhorEnvioToken, 1)
    if not row or not row.pending_state or not state:
        return False
    ok = secrets.compare_digest(row.pending_state, state)
    if ok:
        row.pending_state = None
        db.commit()
    return ok


def _mask(token_enc) -> str | None:
    return "••••••" if token_enc else None


def status(db: Session) -> dict:
    row = db.get(MelhorEnvioToken, 1)
    if not settings.MELHOR_ENVIO_CONFIGURED:
        state = "not_configured"
    elif not row or not row.access_token_enc:
        state = "not_connected"
    elif row.last_error:
        state = "error"
    else:
        try:
            exp = datetime.fromisoformat(row.expires_at) if row.expires_at else None
        except Exception:
            exp = None
        state = "token_expired" if (exp and exp <= datetime.now(timezone.utc)) else "connected"
    return {
        "environment": settings.MELHOR_ENVIO_ENV,
        "configured": settings.MELHOR_ENVIO_CONFIGURED,
        "status": state,
        "account_email": row.account_email if row else None,
        "scope": row.scope if row else None,
        "expires_at": row.expires_at if row else None,
        "updated_at": row.updated_at if row else None,
        "access_token_masked": _mask(row.access_token_enc if row else None),
        "last_error": row.last_error if row else None,
    }


def test_connection(db: Session) -> dict:
    """Chama um endpoint autenticado leve (perfil do usuário ME)."""
    try:
        data = client.api_request(db, "GET", "/api/v2/me/user")
    except MelhorEnvioUnavailable:
        return {"ok": False, "reason": "unavailable", "message": "Melhor Envio indisponível no momento."}
    email = None
    if isinstance(data, dict):
        email = data.get("email")
    if email:
        row = db.get(MelhorEnvioToken, 1)
        if row:
            row.account_email = email
            db.commit()
    return {"ok": True, "account_email": email}


def disconnect(db: Session) -> dict:
    row = db.get(MelhorEnvioToken, 1)
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True, "status": "not_connected"}


def get_sender(db: Session) -> dict:
    row = db.get(MelhorEnvioSender, 1)
    if not row:
        row = MelhorEnvioSender(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return to_dict(row)


def update_sender(db: Session, data: dict) -> dict:
    row = db.get(MelhorEnvioSender, 1)
    if not row:
        row = MelhorEnvioSender(id=1)
        db.add(row)
    for k, v in data.items():
        if hasattr(row, k) and v is not None:
            setattr(row, k, v)
    row.updated_at = _now_iso()
    db.commit()
    db.refresh(row)
    return to_dict(row)


def sender_is_complete(db: Session) -> bool:
    s = db.get(MelhorEnvioSender, 1)
    if not s:
        return False
    required = ["name", "email", "document", "postal_code", "address", "number", "district", "city", "state_abbr"]
    return all((getattr(s, f) or "").strip() for f in required)
