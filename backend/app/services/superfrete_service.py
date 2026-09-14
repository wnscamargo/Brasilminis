"""Service SuperFrete: config segura, teste de conexão, cotação e snapshot.

- Token cifrado (Fernet, reutilizando infra do Melhor Envio).
- Token NUNCA retornado ao frontend (apenas máscara).
- Peso/dimensões vêm SEMPRE do PostgreSQL (fallback = padrão configurado).
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.crypto import encrypt, decrypt
from app.models import Product, SuperfreteSettings
from app.services import superfrete_client as client
from app.services import audit_service

MASK = "••••••••"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(db: Session) -> SuperfreteSettings:
    s = db.get(SuperfreteSettings, 1)
    if s is None:
        s = SuperfreteSettings(id=1, environment="sandbox", enabled_services=["1", "2", "17"])
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _token(s: SuperfreteSettings) -> str | None:
    return decrypt(s.token_enc) if s.token_enc else None


def _user_agent(s: SuperfreteSettings) -> str:
    email = (s.sender_email or "").strip() or "contato@brasilminis.com.br"
    name = (s.sender_name or "Brasil Minis").strip() or "Brasil Minis"
    return f"{name}/1.0 ({email})"


def _mask(s: SuperfreteSettings) -> str:
    tok = _token(s)
    return (MASK + tok[-4:]) if tok and len(tok) >= 4 else (MASK if tok else "")


def public_status(db: Session) -> dict:
    """Status logístico público (sem segredos)."""
    s = _get(db)
    return {"provider": "superfrete", "is_enabled": bool(s.is_enabled and s.token_enc), "environment": s.environment}


def admin_status(db: Session) -> dict:
    s = _get(db)
    return {
        "status": s.status or "not_configured",
        "environment": s.environment,
        "is_enabled": bool(s.is_enabled),
        "token_masked": _mask(s),
        "has_token": bool(s.token_enc),
        "last_test_at": s.last_test_at,
        "last_error": s.last_error,
    }


def admin_config(db: Session) -> dict:
    s = _get(db)
    return {
        "environment": s.environment,
        "is_enabled": bool(s.is_enabled),
        "status": s.status,
        "token_masked": _mask(s),
        "has_token": bool(s.token_enc),
        "sender_name": s.sender_name or "",
        "sender_document": s.sender_document or "",
        "sender_phone": s.sender_phone or "",
        "sender_email": s.sender_email or "",
        "sender_postal_code": s.sender_postal_code or "",
        "sender_address": s.sender_address or "",
        "sender_number": s.sender_number or "",
        "sender_complement": s.sender_complement or "",
        "sender_district": s.sender_district or "",
        "sender_city": s.sender_city or "",
        "sender_state": s.sender_state or "",
        "default_width": float(s.default_width) if s.default_width is not None else None,
        "default_height": float(s.default_height) if s.default_height is not None else None,
        "default_length": float(s.default_length) if s.default_length is not None else None,
        "default_weight": float(s.default_weight) if s.default_weight is not None else None,
        "enabled_services": s.enabled_services or ["1", "2", "17"],
        "last_test_at": s.last_test_at,
        "last_error": s.last_error,
    }


_PLAIN = ("environment", "sender_name", "sender_document", "sender_phone", "sender_email",
          "sender_postal_code", "sender_address", "sender_number", "sender_complement",
          "sender_district", "sender_city", "sender_state")
_NUM = ("default_width", "default_height", "default_length", "default_weight")


def update_config(db: Session, data: dict, admin: dict) -> dict:
    s = _get(db)
    for k in _PLAIN:
        if data.get(k) is not None:
            setattr(s, k, str(data[k]))
    if data.get("environment") not in (None, "sandbox", "production"):
        raise HTTPException(status_code=400, detail="Ambiente inválido.")
    for k in _NUM:
        if data.get(k) is not None:
            setattr(s, k, data[k])
    if data.get("enabled_services") is not None:
        s.enabled_services = [str(x) for x in data["enabled_services"]]
    if data.get("is_enabled") is not None:
        s.is_enabled = bool(data["is_enabled"])
    # Token: só atualiza se vier valor NOVO (não a máscara)
    token = data.get("token")
    if token and MASK not in token:
        s.token_enc = encrypt(token.strip())
        if s.status == "not_configured":
            s.status = "connected" if False else "not_configured"
    s.updated_at = _now()
    audit_service.log(db, "SUPERFRETE_CONFIG_UPDATED", admin, None,
                      {"environment": s.environment, "is_enabled": bool(s.is_enabled)})
    db.commit()
    db.refresh(s)
    return admin_config(db)


def test_connection(db: Session, admin: dict) -> dict:
    s = _get(db)
    tok = _token(s)
    audit_service.log(db, "SUPERFRETE_CONNECTION_TESTED", admin, None, {"environment": s.environment})
    if not tok:
        s.status = "not_configured"
        s.last_error = "Token não configurado."
        s.last_test_at = _now()
        db.commit()
        raise HTTPException(status_code=400, detail="Configure o token da SuperFrete antes de testar.")
    try:
        client.request(s.environment, tok, "GET", "/api/v0/user", user_agent=_user_agent(s))
        s.status = "connected"
        s.last_error = None
        audit_service.log(db, "SUPERFRETE_CONNECTED", admin, None, {"environment": s.environment})
    except client.SuperfreteUnavailable as e:
        s.status = "unavailable"
        s.last_error = str(e)
    except client.SuperfreteError as e:
        s.status = "error"
        s.last_error = f"HTTP {e.status}: {e.body}"
    s.last_test_at = _now()
    db.commit()
    db.refresh(s)
    return admin_status(db)


def disconnect(db: Session, admin: dict) -> dict:
    s = _get(db)
    s.is_enabled = False
    s.status = "not_configured"
    s.updated_at = _now()
    audit_service.log(db, "SUPERFRETE_DISCONNECTED", admin, None, {"environment": s.environment})
    db.commit()
    return admin_status(db)


# ---------- Cotação ----------
def _clean_cep(cep: str) -> str:
    digits = "".join(ch for ch in (cep or "") if ch.isdigit())
    if len(digits) != 8:
        raise HTTPException(status_code=400, detail="CEP inválido. Informe um CEP com 8 dígitos.")
    return digits


def _package(db: Session, s: SuperfreteSettings, items: list) -> tuple[dict, list, float]:
    """Empacotamento determinístico a partir do PostgreSQL. Fallback = padrão configurado."""
    tot_w, max_h, max_wd, tot_len, insurance, snap = 0.0, 0.0, 0.0, 0.0, 0.0, []
    for it in items:
        p = db.get(Product, it.get("product_id"))
        qty = int(it.get("quantity", 1) or 1)
        if not p or not p.is_active or qty < 1:
            raise HTTPException(status_code=400, detail="Produto indisponível no carrinho.")
        w = float(p.weight_kg) if p.weight_kg else (float(s.default_weight) if s.default_weight else 0)
        h = float(p.height_cm) if p.height_cm else (float(s.default_height) if s.default_height else 0)
        wd = float(p.width_cm) if p.width_cm else (float(s.default_width) if s.default_width else 0)
        ln = float(p.length_cm) if p.length_cm else (float(s.default_length) if s.default_length else 0)
        if min(w, h, wd, ln) <= 0:
            raise HTTPException(status_code=422, detail=f"Dados de frete incompletos para '{p.name}'. Cadastre peso e dimensões (ou defina padrões na SuperFrete).")
        tot_w += w * qty
        tot_len += ln * qty
        max_h = max(max_h, h)
        max_wd = max(max_wd, wd)
        insurance += float(p.price) * qty
        snap.append({"product_id": p.id, "name": p.name, "quantity": qty, "unitary_value": round(float(p.price), 2)})
    pkg = {"weight": round(tot_w, 3), "height": round(max_h, 2), "width": round(max_wd, 2), "length": round(tot_len, 2)}
    return pkg, snap, round(insurance, 2)


def _normalize(raw) -> list:
    out = []
    for svc in (raw or []):
        if not isinstance(svc, dict) or svc.get("error") or svc.get("has_error"):
            continue
        price = svc.get("price")
        if price is None:
            continue
        company = svc.get("company") or {}
        out.append({
            "provider": "superfrete",
            "service_id": str(svc.get("id") or svc.get("service_id") or ""),
            "service_code": str(svc.get("id") or svc.get("service_id") or ""),
            "service_name": svc.get("name"),
            "name": svc.get("name"),
            "carrier": company.get("name") or svc.get("company_name"),
            "company_name": company.get("name") or svc.get("company_name"),
            "company_id": company.get("id"),
            "price": round(float(price), 2),
            "delivery_min": svc.get("delivery_min"),
            "delivery_max": svc.get("delivery_max"),
            "delivery_time": svc.get("delivery_time") or svc.get("delivery"),
            "estimated_days": svc.get("delivery_max") or svc.get("delivery"),
        })
    out.sort(key=lambda o: o["price"])
    return out


def quote(db: Session, postal_code: str, items: list, user_id: str | None = None) -> dict:
    import uuid
    from datetime import timedelta
    from app.models import ShippingQuote

    s = _get(db)
    tok = _token(s)
    if not (s.is_enabled and tok):
        raise client.SuperfreteUnavailable("SuperFrete não habilitada.")
    if not (s.sender_postal_code or "").strip():
        raise HTTPException(status_code=400, detail="Remetente SuperFrete não configurado (CEP de origem).")
    dest = _clean_cep(postal_code)
    origin = _clean_cep(s.sender_postal_code)
    pkg, snap, insurance = _package(db, s, items)
    services = ",".join(s.enabled_services or ["1", "2", "17"])
    payload = {
        "from": {"postal_code": origin},
        "to": {"postal_code": dest},
        "services": services,
        "options": {"own_hand": False, "receipt": False, "insurance_value": insurance, "use_insurance_value": insurance > 0},
        "package": pkg,
    }
    raw = client.request(s.environment, tok, "POST", "/api/v0/calculator", user_agent=_user_agent(s), json=payload)
    options = _normalize(raw)
    if not options:
        raise HTTPException(status_code=422, detail="Não conseguimos calcular o frete para este CEP.")
    q = ShippingQuote(
        id=str(uuid.uuid4()), user_id=user_id, destination_postal_code=dest,
        items=[{"product_id": i["product_id"], "quantity": i["quantity"]} for i in snap],
        volumes=[pkg], results=options,
        created_at=_now(), expires_at=(datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
    )
    db.add(q)
    db.commit()
    return {"quote_id": q.id, "provider": "superfrete", "expires_at": q.expires_at,
            "destination_postal_code": dest, "options": options}
