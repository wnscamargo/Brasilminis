from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import SiteSettings
from app.utils import to_dict


def get_settings(db: Session) -> SiteSettings:
    """Retorna a linha única de configuração (cria com defaults se não existir)."""
    s = db.get(SiteSettings, 1)
    if s is None:
        s = SiteSettings(id=1, maintenance_enabled=False)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def public_status(db: Session) -> dict:
    """Somente informações PÚBLICAS (nada administrativo/sensível)."""
    s = get_settings(db)
    return {
        "maintenance_enabled": bool(s.maintenance_enabled),
        "title": s.maintenance_title or "",
        "subtitle": s.maintenance_subtitle or "",
        "message": s.maintenance_message or "",
        "launch_date": s.launch_date,
        "show_countdown": bool(s.show_countdown),
        "whatsapp_url": s.whatsapp_url if s.show_whatsapp else None,
        "instagram_url": s.instagram_url if s.show_instagram else None,
        "show_whatsapp": bool(s.show_whatsapp and s.whatsapp_url),
        "show_instagram": bool(s.show_instagram and s.instagram_url),
    }


def update_settings(db: Session, data: dict, updated_by: str | None) -> dict:
    s = get_settings(db)
    for key, value in data.items():
        setattr(s, key, value)
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return to_dict(s)


# ---------- Identidade visual global ----------
import io
import os
import uuid

from fastapi import HTTPException

ALLOWED_LOGO = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
MAX_LOGO_BYTES = 3 * 1024 * 1024
MAX_LOGO_DIM = 5000


def public_config(db: Session) -> dict:
    """Somente a identidade visual PÚBLICA (logo + tamanho) + redes sociais ativas."""
    s = get_settings(db)
    return {
        "logo_url": s.logo_url or None,
        "logo_width": s.logo_width or 200,
        "store_name": (s.branding or {}).get("store_name"),
        "social_links": _public_social(s),
    }


def admin_config(db: Session) -> dict:
    s = get_settings(db)
    return {
        "logo_url": s.logo_url or None,
        "logo_width": s.logo_width or 200,
        "branding": s.branding or {},
        "updated_at": s.updated_at,
        "updated_by": s.updated_by,
    }


def update_config(db: Session, logo_width: int, branding: dict | None, updated_by: str | None) -> dict:
    s = get_settings(db)
    s.logo_width = max(60, min(500, int(logo_width or 200)))
    if branding is not None:
        merged = dict(s.branding or {})
        merged.update(branding)
        s.branding = merged
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return admin_config(db)


def _branding_dir() -> str:
    from app.core.config import settings
    d = os.path.join(settings.UPLOADS_DIR, "branding")
    os.makedirs(d, exist_ok=True)
    return d


def _remove_if_custom(logo_url: str | None):
    if logo_url and logo_url.startswith("/api/uploads/branding/"):
        name = os.path.basename(logo_url)
        path = os.path.join(_branding_dir(), name)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass


def save_logo(db: Session, content_type: str, content: bytes, updated_by: str | None) -> dict:
    from PIL import Image

    ext = ALLOWED_LOGO.get(content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="Formato inválido. Use PNG, JPEG ou WEBP.")
    if len(content) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máx. 3MB).")
    try:
        Image.open(io.BytesIO(content)).verify()
        w, h = Image.open(io.BytesIO(content)).size
    except Exception:
        raise HTTPException(status_code=400, detail="Imagem inválida ou corrompida.")
    if w > MAX_LOGO_DIM or h > MAX_LOGO_DIM or w < 1 or h < 1:
        raise HTTPException(status_code=400, detail="Dimensões da imagem fora do permitido.")

    name = f"logo-{uuid.uuid4().hex}.{ext}"  # nome próprio (sem confiar no original)
    with open(os.path.join(_branding_dir(), name), "wb") as f:
        f.write(content)

    s = get_settings(db)
    _remove_if_custom(s.logo_url)
    s.logo_url = f"/api/uploads/branding/{name}"
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return public_config(db)


def delete_logo(db: Session, updated_by: str | None) -> dict:
    s = get_settings(db)
    _remove_if_custom(s.logo_url)
    s.logo_url = None  # volta ao fallback (logo padrão)
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return public_config(db)


# ================= Conteúdo institucional + Redes sociais =================
import bleach
from sqlalchemy.orm.attributes import flag_modified

PAGES = ("about", "contact", "returns", "shipping")
SOCIAL_PLATFORMS = ("instagram", "facebook", "tiktok", "youtube", "whatsapp", "telegram", "twitter", "pinterest")

# Defaults editáveis (moram no banco, não no React). Admin sobrescreve pelo painel.
DEFAULT_CONTENT = {
    "about": {
        "title": "Sobre Nós",
        "subtitle": "Sua paixão em miniatura.",
        "content": "A **Brasil Minis** nasceu da paixão pelo colecionismo de miniaturas diecast.\n\n## Missão\nLevar as melhores miniaturas e edições exclusivas aos colecionadores brasileiros.\n\n## Visão\nSer a principal referência em miniaturas no Brasil.\n\n## Valores\n- Autenticidade\n- Curadoria\n- Atendimento próximo",
        "active": True, "seo_title": "Sobre a Brasil Minis", "seo_description": "Conheça a Brasil Minis, loja especializada em miniaturas diecast.",
    },
    "contact": {
        "title": "Contato",
        "subtitle": "Fale com nossa equipe de especialistas em colecionismo.",
        "content": "Estamos à disposição para ajudar com pedidos, trocas e dúvidas.",
        "active": True, "seo_title": "Contato | Brasil Minis", "seo_description": "Entre em contato com a Brasil Minis.",
        "email": "contato@brasilminis.com.br", "phone": "(11) 99999-0000", "whatsapp": "",
        "hours": "Seg a Sex, 9h às 18h", "address": "São Paulo · SP · Brasil", "map_url": "",
    },
    "returns": {
        "title": "Trocas e Devoluções",
        "subtitle": "Sua compra protegida.",
        "content": "## Política de Trocas\nVocê tem até **7 dias corridos** após o recebimento para solicitar troca ou devolução, conforme o CDC.\n\n## Condições\n- Produto sem uso e na embalagem original.\n- Nota fiscal ou comprovante.\n\n## Procedimento\nEntre em contato pelo nosso WhatsApp ou e-mail para iniciar o processo.",
        "active": True, "seo_title": "Trocas e Devoluções | Brasil Minis", "seo_description": "Política de trocas e devoluções da Brasil Minis.",
    },
    "shipping": {
        "title": "Frete e Entrega",
        "subtitle": "Enviamos para todo o Brasil.",
        "content": "## Formas de Envio\nTrabalhamos com transportadoras e Correios via Melhor Envio.\n\n## Prazos\nO prazo é calculado no checkout de acordo com o seu CEP.\n\n## Processamento\nPedidos aprovados são processados em até 2 dias úteis.\n\n## Rastreamento\nVocê recebe o código de rastreio assim que o pedido é postado.",
        "active": True, "seo_title": "Frete e Entrega | Brasil Minis", "seo_description": "Informações sobre frete, prazos e rastreamento.",
    },
}

# Tags/atributos permitidos (defesa extra; o frontend já renderiza Markdown sem HTML bruto).
_ALLOWED_TAGS = ["p", "br", "strong", "b", "em", "i", "ul", "ol", "li", "a", "h1", "h2", "h3", "h4", "blockquote", "code"]
_ALLOWED_ATTRS = {"a": ["href", "title"]}


def _sanitize_rich(text: str | None) -> str:
    """Sanitiza conteúdo rico: remove script/iframe/js e HTML perigoso. Mantém Markdown."""
    if not text:
        return ""
    return bleach.clean(str(text), tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS,
                        protocols=["http", "https", "mailto", "tel"], strip=True)


def _sanitize_plain(text: str | None) -> str:
    if not text:
        return ""
    return bleach.clean(str(text), tags=[], strip=True).strip()


def _valid_url(url: str | None) -> str:
    if not url:
        return ""
    u = str(url).strip()
    if not u:
        return ""
    if not (u.startswith("http://") or u.startswith("https://")):
        raise HTTPException(status_code=400, detail=f"URL inválida (use http/https): {u}")
    if "javascript:" in u.lower():
        raise HTTPException(status_code=400, detail="URL não permitida.")
    return u


def _whatsapp_url(value: str | None) -> str:
    """Aceita URL completa (http/https) OU número — gera https://wa.me/<digitos>."""
    if not value:
        return ""
    v = str(value).strip()
    if v.startswith("http://") or v.startswith("https://"):
        return _valid_url(v)
    digits = "".join(c for c in v if c.isdigit())
    if not digits:
        raise HTTPException(status_code=400, detail="WhatsApp inválido. Informe um número ou link https://wa.me/...")
    return f"https://wa.me/{digits}"


def _merged_content(s: SiteSettings) -> dict:
    stored = dict(s.institutional_content or {})
    out = {}
    for page in PAGES:
        base = dict(DEFAULT_CONTENT[page])
        base.update(stored.get(page) or {})
        out[page] = base
    return out


def _public_page(page_key: str, data: dict) -> dict:
    pub = {
        "title": data.get("title", ""),
        "subtitle": data.get("subtitle", ""),
        "content": data.get("content", ""),
        "seo_title": data.get("seo_title", ""),
        "seo_description": data.get("seo_description", ""),
    }
    if page_key == "contact":
        for k in ("email", "phone", "whatsapp", "hours", "address", "map_url"):
            v = data.get(k)
            if v:
                pub[k] = v
    return pub


def _public_social(s: SiteSettings) -> dict:
    stored = dict(s.social_links or {})
    out = {}
    for plat in SOCIAL_PLATFORMS:
        item = stored.get(plat) or {}
        url = item.get("url")
        if item.get("active") and url:
            out[plat] = url
    return out


# ---------- Conteúdo institucional ----------
def public_content(db: Session) -> dict:
    """Público: só páginas ATIVAS (campos públicos) + redes sociais ativas."""
    s = get_settings(db)
    merged = _merged_content(s)
    pages = {k: _public_page(k, v) for k, v in merged.items() if v.get("active", True)}
    return {"pages": pages, "social_links": _public_social(s)}


def admin_content(db: Session) -> dict:
    """Admin: conteúdo completo (inclui inativas e todos os campos)."""
    s = get_settings(db)
    return {"content": _merged_content(s), "updated_at": s.updated_at, "updated_by": s.updated_by}


def update_content(db: Session, data: dict, updated_by: str | None) -> dict:
    s = get_settings(db)
    stored = dict(s.institutional_content or {})
    for page in PAGES:
        incoming = data.get(page)
        if incoming is None:
            continue
        cur = dict(stored.get(page) or {})
        for key, value in incoming.items():
            if value is None:
                continue
            if key == "content":
                cur[key] = _sanitize_rich(value)
            elif key in ("title", "subtitle", "seo_title", "seo_description", "hours", "address", "email", "phone"):
                cur[key] = _sanitize_plain(value)
            elif key == "whatsapp":
                cur[key] = _whatsapp_url(value)
            elif key == "map_url":
                cur[key] = _valid_url(value)
            elif key == "active":
                cur[key] = bool(value)
            else:
                cur[key] = value
        stored[page] = cur
    s.institutional_content = stored
    flag_modified(s, "institutional_content")
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return admin_content(db)


# ---------- Redes sociais ----------
def admin_social(db: Session) -> dict:
    s = get_settings(db)
    stored = dict(s.social_links or {})
    out = {}
    for plat in SOCIAL_PLATFORMS:
        item = stored.get(plat) or {}
        out[plat] = {"url": item.get("url", ""), "active": bool(item.get("active"))}
    return {"social_links": out}


def update_social(db: Session, data: dict, updated_by: str | None) -> dict:
    s = get_settings(db)
    stored = dict(s.social_links or {})
    for plat in SOCIAL_PLATFORMS:
        incoming = data.get(plat)
        if incoming is None:
            continue
        url = _valid_url(incoming.get("url"))
        active = bool(incoming.get("active")) and bool(url)
        stored[plat] = {"url": url, "active": active}
    s.social_links = stored
    flag_modified(s, "social_links")
    s.updated_at = datetime.now(timezone.utc).isoformat()
    s.updated_by = updated_by
    db.commit()
    db.refresh(s)
    return admin_social(db)
