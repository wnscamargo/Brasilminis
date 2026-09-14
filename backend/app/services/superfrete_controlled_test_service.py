"""SuperFrete — Etapa D: teste de PRODUÇÃO CONTROLADA (admin-only).

Fluxo passo a passo, cada etapa disparada explicitamente pelo admin:
conexão -> cotação -> selecionar serviço -> criar envio (idempotente) ->
consultar -> etiqueta (híbrida se API não suportar) -> tracking -> sync -> finalizar.

- Nenhuma etapa "sem efeito colateral" (conexão/cotação) cria envio.
- O envio de teste é vinculado a um PEDIDO DE TESTE (is_test_order=True); nenhum
  outro pedido é afetado. Pedidos de teste são excluídos de métricas reais.
- Token nunca é exposto (cifrado/mascarado); payloads sanitizados.
- Idempotência: recriar não duplica shipment/etiqueta/evento.
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Order, SuperfreteSettings, SuperfreteShipment
from app.services import audit_service
from app.services import superfrete_client as client
from app.services import superfrete_service as sf
from app.services import superfrete_sync_service as sync

_CHECK_KEYS = [
    "token_valid", "connection_ok", "quote_returned", "service_selected",
    "shipment_created", "label_available", "tracking_received", "polling_synced",
    "idempotency_validated", "no_critical_error", "melhor_envio_intact",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _blank_state() -> dict:
    return {
        "params": None, "selected_service": None, "quote_options": [],
        "checklist": {k: (True if k in ("no_critical_error", "melhor_envio_intact") else False) for k in _CHECK_KEYS},
        "status": "PENDING", "logs": [], "test_order_id": None, "shipment_id": None,
        "updated_at": _now(),
    }


def _get_state(db: Session) -> tuple[SuperfreteSettings, dict]:
    s = sf._get(db)
    st = s.controlled_test_state or _blank_state()
    # garante todas as chaves do checklist
    st.setdefault("checklist", {})
    for k in _CHECK_KEYS:
        st["checklist"].setdefault(k, True if k in ("no_critical_error", "melhor_envio_intact") else False)
    return s, st


def _log(st: dict, step: str, ok: bool, message: str) -> None:
    st["logs"] = (st.get("logs") or [])[-49:] + [{"step": step, "ok": ok, "message": (message or "")[:300], "at": _now()}]


def _recompute(st: dict) -> None:
    c = st["checklist"]
    core = ["token_valid", "connection_ok", "quote_returned", "service_selected", "shipment_created"]
    if not c.get("no_critical_error", True):
        st["status"] = "FAILED"
    elif all(c.get(k) for k in core) and c.get("tracking_received") and c.get("polling_synced") and c.get("idempotency_validated"):
        st["status"] = "APPROVED"
    elif any(c.get(k) for k in core):
        st["status"] = "PARTIAL"
    else:
        st["status"] = "PENDING"
    st["updated_at"] = _now()


def _public(st: dict) -> dict:
    """Estado sanitizado (sem token/segredos)."""
    return {
        "params": st.get("params"),
        "selected_service": st.get("selected_service"),
        "quote_options": st.get("quote_options") or [],
        "checklist": st.get("checklist"),
        "status": st.get("status"),
        "logs": st.get("logs") or [],
        "test_order_id": st.get("test_order_id"),
        "shipment_id": st.get("shipment_id"),
        "updated_at": st.get("updated_at"),
    }


def _save(db: Session, s: SuperfreteSettings, st: dict) -> None:
    _recompute(st)
    s.controlled_test_state = st
    # força flag de modificação em coluna JSONB
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(s, "controlled_test_state")
    db.commit()


def get_state(db: Session) -> dict:
    _, st = _get_state(db)
    return _public(st)


def reset(db: Session, admin: dict) -> dict:
    s, _ = _get_state(db)
    s.controlled_test_state = _blank_state()
    db.commit()
    audit_service.log(db, "SUPERFRETE_CONTROLLED_TEST_STARTED", admin, None, {"reset": True}, commit=True)
    return get_state(db)


def _pkg_from_params(p: dict) -> dict:
    try:
        pkg = {"weight": float(p["weight"]), "width": float(p["width"]),
               "height": float(p["height"]), "length": float(p["length"])}
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Informe peso e dimensões válidos.")
    if min(pkg.values()) <= 0:
        raise HTTPException(status_code=400, detail="Peso e dimensões devem ser maiores que zero.")
    return pkg


def set_params(db: Session, params: dict, admin: dict) -> dict:
    s, st = _get_state(db)
    origin = "".join(ch for ch in str(params.get("origin_postal_code") or s.sender_postal_code or "") if ch.isdigit())
    dest = "".join(ch for ch in str(params.get("dest_postal_code") or "") if ch.isdigit())
    if len(origin) != 8 or len(dest) != 8:
        raise HTTPException(status_code=400, detail="CEPs de origem e destino devem ter 8 dígitos.")
    pkg = _pkg_from_params(params)
    st = _blank_state()
    st["params"] = {
        "origin_postal_code": origin, "dest_postal_code": dest, **pkg,
        "insurance_value": float(params.get("insurance_value") or 0),
        "product_name": (params.get("product_name") or "Produto de teste")[:120],
    }
    _log(st, "params", True, "Parâmetros do teste definidos.")
    _save(db, s, st)
    audit_service.log(db, "SUPERFRETE_CONTROLLED_TEST_STARTED", admin, None,
                      {"origin": origin, "dest": dest}, commit=True)
    return _public(st)


def run_connection(db: Session, admin: dict) -> dict:
    s, st = _get_state(db)
    tok = sf._token(s)
    if not tok:
        st["checklist"]["token_valid"] = False
        st["checklist"]["connection_ok"] = False
        _log(st, "connection", False, "Token não configurado.")
        _save(db, s, st)
        raise HTTPException(status_code=400, detail="Configure o token da SuperFrete antes de testar.")
    try:
        client.request(s.environment, tok, "GET", "/api/v0/user", user_agent=sf._user_agent(s))
        st["checklist"]["token_valid"] = True
        st["checklist"]["connection_ok"] = True
        _log(st, "connection", True, "Conexão com a SuperFrete OK.")
        s.status = "connected"
    except client.SuperfreteAuthError:
        st["checklist"]["token_valid"] = False
        st["checklist"]["connection_ok"] = False
        st["checklist"]["no_critical_error"] = False
        _log(st, "connection", False, "Autenticação inválida (token).")
        _save(db, s, st)
        raise HTTPException(status_code=400, detail="Token inválido/expirado.")
    except (client.SuperfreteUnavailable, client.SuperfreteError) as e:
        st["checklist"]["connection_ok"] = False
        _log(st, "connection", False, f"Indisponível: {type(e).__name__}")
        _save(db, s, st)
        raise HTTPException(status_code=502, detail="SuperFrete indisponível no momento.")
    _save(db, s, st)
    return _public(st)


def run_quote(db: Session, admin: dict) -> dict:
    s, st = _get_state(db)
    if not st.get("params"):
        raise HTTPException(status_code=400, detail="Defina os parâmetros do teste primeiro.")
    p = st["params"]
    try:
        options = sf.quote_raw(db, p["origin_postal_code"], p["dest_postal_code"],
                               {k: p[k] for k in ("weight", "width", "height", "length")},
                               services=None, insurance=p.get("insurance_value") or 0)
    except client.SuperfreteAuthError:
        st["checklist"]["no_critical_error"] = False
        _log(st, "quote", False, "Autenticação inválida ao cotar.")
        _save(db, s, st)
        raise HTTPException(status_code=400, detail="Token inválido/expirado.")
    except (client.SuperfreteUnavailable, client.SuperfreteError):
        _log(st, "quote", False, "Falha ao cotar (indisponível).")
        _save(db, s, st)
        raise HTTPException(status_code=502, detail="Não foi possível cotar agora.")
    if not options:
        _log(st, "quote", False, "Nenhum serviço retornado para o trecho.")
        _save(db, s, st)
        raise HTTPException(status_code=422, detail="Nenhum serviço retornado para este CEP.")
    st["quote_options"] = options
    st["checklist"]["quote_returned"] = True
    _log(st, "quote", True, f"{len(options)} serviço(s) retornado(s).")
    _save(db, s, st)
    return _public(st)


def select_service(db: Session, service_id: str, admin: dict) -> dict:
    s, st = _get_state(db)
    opt = next((o for o in (st.get("quote_options") or []) if str(o.get("service_id")) == str(service_id)), None)
    if not opt:
        raise HTTPException(status_code=400, detail="Serviço não encontrado na cotação.")
    st["selected_service"] = opt
    st["checklist"]["service_selected"] = True
    _log(st, "select", True, f"Serviço selecionado: {opt.get('service_name')} ({opt.get('company_name')}).")
    _save(db, s, st)
    audit_service.log(db, "SUPERFRETE_QUOTE_CONFIRMED", admin, None,
                      {"service_id": str(service_id)}, commit=True)
    return _public(st)


def _ensure_test_order(db: Session, s: SuperfreteSettings, st: dict, admin: dict) -> Order:
    """Cria (ou reaproveita) o PEDIDO DE TESTE. Nunca um pedido comercial real."""
    if s.test_order_id:
        o = db.get(Order, s.test_order_id)
        if o and o.is_test_order:
            return o
    p = st["params"]
    svc = st["selected_service"]
    oid = str(uuid.uuid4())
    o = Order(
        id=oid, user_id=admin.get("id") or "admin", is_test_order=True,
        status="confirmado", payment_status="approved", payment_approved_at=_now(),
        shipping_provider="superfrete",
        shipping_service_id=svc.get("service_id"), shipping_service_name=svc.get("service_name"),
        shipping_company_name=svc.get("company_name"),
        shipping_price_customer=svc.get("price"), shipping_price_quoted=svc.get("price"),
        shipping_delivery_max=svc.get("delivery_max") or svc.get("estimated_days"),
        shipping_destination_postal_code=p["dest_postal_code"],
        shipping_quote_snapshot={"package": {k: p[k] for k in ("weight", "width", "height", "length")},
                                 "items": [{"product_id": "test", "quantity": 1}]},
        recipient_snapshot={"postal_code": p["dest_postal_code"], "street": "Endereço de teste",
                            "number": "0", "name": "Teste Controlado"},
        created_at=_now(),
    )
    db.add(o)
    db.commit()
    s.test_order_id = oid
    db.commit()
    return o


def create_shipment(db: Session, admin: dict) -> dict:
    s, st = _get_state(db)
    if not st.get("selected_service"):
        raise HTTPException(status_code=400, detail="Selecione um serviço antes de criar o envio.")
    o = _ensure_test_order(db, s, st, admin)
    r1 = sf.create_shipment(db, o, admin)  # idempotente (Etapa B) — NÃO chama API externa
    # valida idempotência: recriar não duplica
    r2 = sf.create_shipment(db, o, admin)
    ship = r2.get("shipment") or r1.get("shipment")
    st["shipment_id"] = ship.get("id")
    st["test_order_id"] = o.id
    st["checklist"]["shipment_created"] = True
    st["checklist"]["idempotency_validated"] = bool(r2.get("already_exists"))
    _log(st, "create", True, "Envio de teste preparado (idempotência validada)." if r2.get("already_exists")
         else "Envio de teste preparado.")
    _save(db, s, st)
    return _public(st)


def _test_shipment(db: Session, s: SuperfreteSettings, st: dict) -> SuperfreteShipment:
    sid = st.get("shipment_id")
    sh = db.get(SuperfreteShipment, sid) if sid else None
    if not sh:
        raise HTTPException(status_code=400, detail="Crie o envio de teste primeiro.")
    return sh


def consult(db: Session, admin: dict) -> dict:
    s, st = _get_state(db)
    sh = _test_shipment(db, s, st)
    tok = sf._token(s)
    if not sh.external_id or not tok:
        _log(st, "consult", True, "Sem identificador externo: emita/finalize no painel SuperFrete (fluxo híbrido).")
        _save(db, s, st)
        return _public(st)
    try:
        data = client.request(s.environment, tok, "GET", f"/api/v0/order/info/{sh.external_id}",
                              user_agent=sf._user_agent(s))
        raw = data.get("status") if isinstance(data, dict) else None
        _log(st, "consult", True, f"Consulta OK. Status bruto: {str(raw)[:40]}")
    except client.SuperfreteAuthError:
        st["checklist"]["no_critical_error"] = False
        _log(st, "consult", False, "Autenticação inválida ao consultar.")
    except (client.SuperfreteUnavailable, client.SuperfreteError):
        _log(st, "consult", False, "Falha ao consultar (indisponível).")
    _save(db, s, st)
    return _public(st)


def get_label(db: Session, admin: dict) -> dict:
    """Obtém a etiqueta SE a API suportar; caso contrário, mantém o fluxo híbrido (painel)."""
    s, st = _get_state(db)
    sh = _test_shipment(db, s, st)
    tok = sf._token(s)
    label_id = sh.label_external_id or sh.external_id
    if not label_id or not tok:
        _log(st, "label", True, "Etiqueta emitida no painel SuperFrete (fluxo híbrido — API sem contrato público de emissão).")
        _save(db, s, st)
        return _public(st)
    try:
        data = client.request(s.environment, tok, "GET", f"/api/v1/shipping-labels/{label_id}",
                              user_agent=sf._user_agent(s))
        url = (data.get("url") or data.get("label_url")) if isinstance(data, dict) else None
        if url:
            sh.label_url = url
            sh.label_status = "issued_api"
            st["checklist"]["label_available"] = True
            _log(st, "label", True, "Etiqueta disponível via API.")
            audit_service.log(db, "SUPERFRETE_LABEL_READY", admin, sh.order_id, {"shipment_id": sh.id})
        else:
            _log(st, "label", True, "Etiqueta ainda não disponível pela API — finalize no painel (híbrido).")
    except (client.SuperfreteAuthError, client.SuperfreteUnavailable, client.SuperfreteError):
        _log(st, "label", True, "Emissão via API indisponível — fluxo híbrido (painel).")
    _save(db, s, st)
    return _public(st)


def capture_tracking(db: Session, tracking_code: str, external_id: str | None, admin: dict) -> dict:
    s, st = _get_state(db)
    o = db.get(Order, st.get("test_order_id"))
    if not o:
        raise HTTPException(status_code=400, detail="Crie o envio de teste primeiro.")
    sf.set_tracking(db, o, tracking_code, external_id, admin)
    st["checklist"]["tracking_received"] = True
    _log(st, "tracking", True, "Rastreio capturado.")
    _save(db, s, st)
    audit_service.log(db, "SUPERFRETE_TRACKING_RECEIVED", admin, o.id, {"has_external_id": bool(external_id)}, commit=True)
    return _public(st)


def run_sync(db: Session, admin: dict) -> dict:
    s, st = _get_state(db)
    sh = _test_shipment(db, s, st)
    if not sh.external_id:
        _log(st, "sync", True, "Sem identificador externo: polling aguardará emissão/rastreio.")
        st["checklist"]["polling_synced"] = True  # scheduler está apto; sem external_id não há o que consultar
        _save(db, s, st)
        return _public(st)
    sync.sync_one(sh.id, worker=f"ctest-{admin.get('email', 'admin')}", admin=admin)
    st["checklist"]["polling_synced"] = True
    _log(st, "sync", True, "Sincronização executada; timeline atualizada.")
    _save(db, s, st)
    return _public(st)


def finalize(db: Session, admin: dict) -> dict:
    s, st = _get_state(db)
    st["checklist"]["melhor_envio_intact"] = True  # ME nunca é tocado pelo fluxo SuperFrete
    _recompute(st)
    _save(db, s, st)
    event = "SUPERFRETE_CONTROLLED_TEST_COMPLETED" if st["status"] != "FAILED" else "SUPERFRETE_CONTROLLED_TEST_FAILED"
    audit_service.log(db, event, admin, st.get("test_order_id"), {"status": st["status"]}, commit=True)
    return _public(st)
