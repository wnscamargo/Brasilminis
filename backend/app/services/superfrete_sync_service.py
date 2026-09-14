"""SuperFrete — Etapa C: sincronização defensiva, eventos idempotentes e job.

- Fonte automática de atualização = job de polling (não há contrato de webhook
  verificável na doc oficial; ver LIMITAÇÃO abaixo).
- Concorrência: advisory lock global (PostgreSQL) + claim atômico por envio (TTL).
- Eventos idempotentes via dedupe_key (constraint única) — timeline confiável.
- Transições defensivas: sem regressão de estado; desconhecido preserva.
- Suspensão por erro de autenticação é GLOBAL (o token é do provider).
- NUNCA processa Melhor Envio (tabela separada). NUNCA cria envio na reconciliação.

LIMITAÇÃO (webhook): a documentação oficial descreve o registro de webhook
(POST /api/v0/webhook -> secret_token), porém NÃO define algoritmo de assinatura
verificável do payload recebido. Por isso NÃO expomos um endpoint público
funcional/desprotegido nem improvisamos HMAC. A arquitetura (superfrete_events com
source/dedupe_key + record_event reutilizável) já está pronta para ativar webhook
no futuro assim que houver contrato oficial de autenticação.
"""
import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models import (
    SuperfreteEvent,
    SuperfreteSettings,
    SuperfreteShipment,
    SuperfreteSyncRun,
)
from app.services import audit_service
from app.services import superfrete_client as client

logger = logging.getLogger("brasilminis.superfrete_sync")

_ADVISORY_LOCK_KEY = 815234567  # bigint fixo p/ pg_advisory_lock (job global)

# ---- Máquina de estados defensiva ----
TERMINAL = {"DELIVERED", "RETURNED", "CANCELED"}
_RANK = {
    "NOT_READY": 0, "READY": 1, "CREATING": 1, "PENDING": 1, "PENDING_LABEL": 2,
    "LABEL_READY": 3, "POSTED": 4, "IN_TRANSIT": 5, "OUT_FOR_DELIVERY": 6,
    "DELIVERY_FAILED": 6, "RETURNING": 6, "DELIVERED": 7, "RETURNED": 7,
    "CANCELED": 7, "ERROR": -1,
}
# Exceções permitidas a partir de estado terminal (justificadas por evento oficial).
_TERMINAL_EXCEPTIONS = {"DELIVERED": {"RETURNING", "RETURNED"}}

_RAW_STATUS_MAP = {
    "pending": "PENDING_LABEL", "created": "PENDING_LABEL", "waiting": "PENDING_LABEL",
    "released": "LABEL_READY", "generated": "LABEL_READY", "paid": "LABEL_READY",
    "posted": "POSTED", "post": "POSTED", "postado": "POSTED",
    "in_transit": "IN_TRANSIT", "transit": "IN_TRANSIT", "shipped": "IN_TRANSIT",
    "out_for_delivery": "OUT_FOR_DELIVERY", "out-for-delivery": "OUT_FOR_DELIVERY",
    "delivered": "DELIVERED", "entregue": "DELIVERED",
    "delivery_failed": "DELIVERY_FAILED", "failed": "DELIVERY_FAILED",
    "returning": "RETURNING", "returned": "RETURNED", "devolvido": "RETURNED",
    "canceled": "CANCELED", "cancelled": "CANCELED", "cancelado": "CANCELED",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def normalize_status(raw) -> str | None:
    """Normaliza o status bruto. Retorna None se DESCONHECIDO (preservar estado)."""
    if raw is None:
        return None
    key = str(raw).strip().lower().replace(" ", "_")
    return _RAW_STATUS_MAP.get(key)  # None => desconhecido (defensivo)


def can_transition(current: str | None, new: str | None) -> bool:
    """Impede regressões e transições inválidas."""
    if not new or new == current:
        return False
    cur = current or "NOT_READY"
    if cur in TERMINAL:
        return new in _TERMINAL_EXCEPTIONS.get(cur, set())
    return _RANK.get(new, -99) >= _RANK.get(cur, 0)


# ---- Intervalos / backoff ----
def compute_next_sync_at(status: str | None, attempts: int = 0,
                         temporary_error: bool = False, retry_after: int | None = None) -> str | None:
    if status in TERMINAL:
        return None  # para de sincronizar
    if temporary_error:
        if retry_after and retry_after > 0:
            secs = min(retry_after, settings.SUPERFRETE_BACKOFF_MAX)
        else:
            secs = min(settings.SUPERFRETE_BACKOFF_BASE * (2 ** max(0, attempts - 1)),
                       settings.SUPERFRETE_BACKOFF_MAX)
        return _iso(_now() + timedelta(seconds=secs))
    if status == "OUT_FOR_DELIVERY":
        secs = settings.SUPERFRETE_INTERVAL_OUT
    elif status in ("POSTED", "IN_TRANSIT", "DELIVERY_FAILED", "RETURNING"):
        secs = settings.SUPERFRETE_INTERVAL_TRANSIT
    else:  # PENDING_LABEL / LABEL_READY / aguardando postagem
        secs = settings.SUPERFRETE_INTERVAL_AWAITING
    return _iso(_now() + timedelta(seconds=secs))


# ---- Eventos idempotentes ----
def _dedupe_key(shipment_id: str, source: str, raw_status: str | None,
                provider_event_at: str | None, extra: str | None = None) -> str:
    base = "|".join([shipment_id, source, str(raw_status or ""), str(provider_event_at or ""), str(extra or "")])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def record_event(db: Session, shipment: SuperfreteShipment, *, source: str,
                 raw_status: str | None, normalized_status: str | None,
                 description: str | None = None, provider_event_at: str | None = None,
                 external_event_id: str | None = None, extra: str | None = None,
                 payload: dict | None = None) -> bool:
    """Insere um evento idempotente na timeline. Retorna True se criado (novo)."""
    key = _dedupe_key(shipment.id, source, raw_status, provider_event_at, extra)
    safe_payload = None
    if payload:
        # apenas campos permitidos/sanitizados (NUNCA token/headers/segredos)
        safe_payload = {k: payload.get(k) for k in ("status", "tracking", "id") if payload.get(k) is not None}
    ev = SuperfreteEvent(
        id=str(uuid.uuid4()),
        order_id=shipment.order_id,
        shipment_id=shipment.id,
        external_event_id=external_event_id,
        event_type=source.lower(),
        source=source,
        raw_status=str(raw_status) if raw_status is not None else None,
        normalized_status=normalized_status,
        description=(description or "")[:300] or None,
        dedupe_key=key,
        payload_hash=key[:32],
        payload_json=safe_payload,
        provider_event_at=provider_event_at,
        received_at=_iso(_now()),
        processed=True,
        processed_at=_iso(_now()),
        created_at=_iso(_now()),
    )
    db.add(ev)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return False  # já registrado (idempotente)
    return True


# ---- Suspensão global por erro de autenticação ----
def _suspend_global(db: Session, reason: str) -> None:
    s = db.get(SuperfreteSettings, 1)
    if s:
        s.sync_suspended = True
        s.sync_suspended_reason = (reason or "Falha de autenticação.")[:300]
        s.sync_suspended_at = _iso(_now())
        s.status = "error"
        s.last_error = s.sync_suspended_reason
        db.commit()


def clear_global_suspension(db: Session) -> None:
    """Reativa a sincronização automática após troca+teste bem-sucedido do token."""
    s = db.get(SuperfreteSettings, 1)
    if s and s.sync_suspended:
        s.sync_suspended = False
        s.sync_suspended_reason = None
        s.sync_suspended_at = None
        db.commit()


# ---- Elegibilidade / claim ----
def _global_ok(db: Session) -> tuple[bool, str]:
    s = db.get(SuperfreteSettings, 1)
    if not s or not (s.is_enabled and s.token_enc):
        return False, "SuperFrete desabilitada/sem token."
    if not s.sync_enabled:
        return False, "Sincronização desativada na configuração."
    if s.sync_suspended:
        return False, "Sincronização suspensa (autenticação inválida)."
    return True, ""


def _eligible_ids(db: Session, batch: int) -> list[str]:
    now = _iso(_now())
    ttl_cut = _iso(_now() - timedelta(seconds=settings.SUPERFRETE_LOCK_TTL_SECONDS))
    rows = (
        db.query(SuperfreteShipment.id)
        .filter(
            SuperfreteShipment.external_id.isnot(None),
            SuperfreteShipment.sync_enabled.is_(True),
            SuperfreteShipment.shipment_status.notin_(tuple(TERMINAL)),
            or_(SuperfreteShipment.next_sync_at.is_(None), SuperfreteShipment.next_sync_at <= now),
            or_(SuperfreteShipment.locked_at.is_(None), SuperfreteShipment.locked_at < ttl_cut),
        )
        .order_by(SuperfreteShipment.next_sync_at.asc().nullsfirst())
        .limit(batch)
        .all()
    )
    return [r[0] for r in rows]


def _claim(db: Session, shipment_id: str, worker: str) -> bool:
    """Claim atômico do envio (TTL). Retorna True se este worker travou."""
    ttl_cut = _iso(_now() - timedelta(seconds=settings.SUPERFRETE_LOCK_TTL_SECONDS))
    res = (
        db.query(SuperfreteShipment)
        .filter(
            SuperfreteShipment.id == shipment_id,
            or_(SuperfreteShipment.locked_at.is_(None), SuperfreteShipment.locked_at < ttl_cut),
        )
        .update({"locked_at": _iso(_now()), "locked_by": worker}, synchronize_session=False)
    )
    db.commit()
    return res == 1


def _release(db: Session, sh: SuperfreteShipment) -> None:
    sh.locked_at = None
    sh.locked_by = None


# ---- Sincronização de UM envio (usa sessão própria) ----
def sync_one(shipment_id: str, worker: str, admin: dict | None = None) -> str:
    """Sincroniza um envio já elegível. Retorna 'updated' | 'unchanged' | 'failed'."""
    db = SessionLocal()
    try:
        if not _claim(db, shipment_id, worker):
            return "skipped"
        sh = db.get(SuperfreteShipment, shipment_id)
        if not sh:
            return "skipped"
        s = db.get(SuperfreteSettings, 1)
        from app.services.superfrete_service import _token, _user_agent  # lazy (evita ciclo)
        tok = _token(s)
        if not tok or not sh.external_id:
            _release(db, sh)
            sh.last_sync_at = _iso(_now())
            db.commit()
            return "skipped"
        try:
            data = client.request(s.environment, tok, "GET",
                                  f"/api/v0/order/info/{sh.external_id}", user_agent=_user_agent(s))
        except client.SuperfreteAuthError as e:
            _suspend_global(db, "Token inválido/expirado durante a sincronização.")
            db2 = SessionLocal()
            try:
                sh2 = db2.get(SuperfreteShipment, shipment_id)
                if sh2:
                    _release(db2, sh2)
                    sh2.last_error = "Autenticação inválida."
                    sh2.last_sync_at = _iso(_now())
                    db2.commit()
            finally:
                db2.close()
            logger.warning("SuperFrete sync suspenso por auth inválida (%s).", e.status)
            return "failed"
        except client.SuperfreteError as e:
            temporary = e.status in (429,) or e.status >= 500
            sh.sync_attempts = (sh.sync_attempts or 0) + 1
            sh.last_error = f"HTTP {e.status}"
            if e.status not in (429,) and e.status >= 400 and e.status < 500:
                sh.shipment_status = "ERROR" if sh.shipment_status not in TERMINAL else sh.shipment_status
                temporary = False
            sh.next_sync_at = compute_next_sync_at(sh.shipment_status, sh.sync_attempts,
                                                   temporary_error=temporary, retry_after=getattr(e, "retry_after", None))
            _release(db, sh)
            sh.last_sync_at = _iso(_now())
            sh.updated_at = _iso(_now())
            db.commit()
            return "failed"
        except client.SuperfreteUnavailable:
            sh.sync_attempts = (sh.sync_attempts or 0) + 1
            sh.last_error = "SuperFrete indisponível (temporário)."
            sh.next_sync_at = compute_next_sync_at(sh.shipment_status, sh.sync_attempts, temporary_error=True)
            _release(db, sh)
            sh.last_sync_at = _iso(_now())
            db.commit()
            return "failed"

        # ---- Sucesso: interpreta defensivamente ----
        raw = data.get("status") if isinstance(data, dict) else None
        provider_event_at = (data.get("updated_at") or data.get("posted_at")) if isinstance(data, dict) else None
        tracking = data.get("tracking") if isinstance(data, dict) else None
        normalized = normalize_status(raw)
        result = "unchanged"
        if tracking and not sh.tracking_code:
            sh.tracking_code = tracking
        if normalized is None:
            # desconhecido -> preserva estado; auditoria técnica
            audit_service.log(db, "SUPERFRETE_STATUS_UNKNOWN", admin, sh.order_id,
                              {"shipment_id": sh.id, "raw_status": str(raw)[:80]})
        elif can_transition(sh.shipment_status, normalized):
            created = record_event(db, sh, source="POLL", raw_status=raw, normalized_status=normalized,
                                   description=f"Status atualizado: {normalized}", provider_event_at=provider_event_at,
                                   payload={"status": raw, "tracking": tracking})
            sh.shipment_status = normalized
            sh.raw_status = str(raw) if raw is not None else sh.raw_status
            sh.last_status_at = provider_event_at or _iso(_now())
            sh.version = (sh.version or 0) + 1
            result = "updated" if created else "updated"
        else:
            # regressão/transição inválida -> ignora, auditoria técnica
            audit_service.log(db, "SUPERFRETE_TRANSITION_IGNORED", admin, sh.order_id,
                              {"shipment_id": sh.id, "from": sh.shipment_status, "to": normalized})
        sh.sync_attempts = 0
        sh.last_error = None
        sh.next_sync_at = compute_next_sync_at(sh.shipment_status)
        _release(db, sh)
        sh.last_sync_at = _iso(_now())
        sh.updated_at = _iso(_now())
        db.commit()
        return result
    except Exception:
        db.rollback()
        logger.exception("Erro inesperado ao sincronizar envio %s", shipment_id)
        return "failed"
    finally:
        db.close()


# ---- Advisory lock global ----
def _acquire_global_lock(conn) -> bool:
    return bool(conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": _ADVISORY_LOCK_KEY}).scalar())


def _release_global_lock(conn) -> None:
    conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _ADVISORY_LOCK_KEY})


# ---- Ciclo de sincronização ----
def run_sync_cycle(trigger: str = "auto", admin: dict | None = None) -> dict:
    """Executa um ciclo protegido por advisory lock global. Retorna o resumo do run."""
    started = _now()
    run_id = str(uuid.uuid4())
    status = "ok"
    last_error = None
    counts = {"processed": 0, "updated": 0, "unchanged": 0, "failed": 0, "skipped": 0}

    conn = engine.connect()
    try:
        if not _acquire_global_lock(conn):
            status = "skipped_locked"
        else:
            db = SessionLocal()
            try:
                ok, reason = _global_ok(db)
                if not ok:
                    status = "skipped_locked"
                    last_error = reason
                    ids = []
                else:
                    ids = _eligible_ids(db, settings.SUPERFRETE_SYNC_BATCH)
            finally:
                db.close()

            worker = f"cycle-{run_id[:8]}"
            for sid in ids:
                r = sync_one(sid, worker, admin)
                counts["processed"] += 1 if r != "skipped" else 0
                if r in counts:
                    counts[r] += 1
    finally:
        try:
            _release_global_lock(conn)
        finally:
            conn.close()

    finished = _now()
    duration_ms = int((finished - started).total_seconds() * 1000)
    result = {
        "id": run_id, "trigger": trigger, "status": status,
        "started_at": _iso(started), "finished_at": _iso(finished),
        "duration_ms": duration_ms, "last_error": last_error,
        "created_by": (admin or {}).get("email"), **counts,
    }
    _persist_run(result)
    logger.info("SuperFrete sync (%s): %s", trigger, counts)
    return result


def _persist_run(result: dict) -> None:
    db = SessionLocal()
    try:
        db.add(SuperfreteSyncRun(
            id=result["id"], trigger=result["trigger"], status=result["status"],
            started_at=result["started_at"], finished_at=result["finished_at"],
            duration_ms=result["duration_ms"], last_error=result["last_error"],
            created_by=result.get("created_by"),
            processed=result["processed"], updated=result["updated"],
            unchanged=result["unchanged"], failed=result["failed"], skipped=result["skipped"],
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


# ---- Reconciliação (só corrige situações seguras; NUNCA cria envio) ----
def reconcile(admin: dict | None = None) -> dict:
    db = SessionLocal()
    fixed = {"unlocked": 0, "rescheduled": 0, "recovered": 0}
    try:
        now = _now()
        ttl_cut = _iso(now - timedelta(seconds=settings.SUPERFRETE_LOCK_TTL_SECONDS))
        stale_cut = _iso(now - timedelta(seconds=settings.SUPERFRETE_STALE_SECONDS))
        # 1) destrava locks expirados
        fixed["unlocked"] = (
            db.query(SuperfreteShipment)
            .filter(SuperfreteShipment.locked_at.isnot(None), SuperfreteShipment.locked_at < ttl_cut)
            .update({"locked_at": None, "locked_by": None}, synchronize_session=False)
        )
        # 2) reprograma ativos sem sync recente
        fixed["rescheduled"] = (
            db.query(SuperfreteShipment)
            .filter(
                SuperfreteShipment.external_id.isnot(None),
                SuperfreteShipment.sync_enabled.is_(True),
                SuperfreteShipment.shipment_status.notin_(tuple(TERMINAL)),
                or_(SuperfreteShipment.last_sync_at.is_(None), SuperfreteShipment.last_sync_at < stale_cut),
            )
            .update({"next_sync_at": _iso(now)}, synchronize_session=False)
        )
        # 3) recupera ERROR (reprograma imediatamente, sem regredir estado terminal)
        fixed["recovered"] = (
            db.query(SuperfreteShipment)
            .filter(SuperfreteShipment.shipment_status == "ERROR")
            .update({"shipment_status": "PENDING_LABEL", "last_error": None, "next_sync_at": _iso(now)},
                    synchronize_session=False)
        )
        db.commit()
        audit_service.log(db, "SUPERFRETE_RECONCILE", admin, None, fixed, commit=True)
    except Exception:
        db.rollback()
        logger.exception("Erro na reconciliação SuperFrete")
    finally:
        db.close()
    return fixed


def reprocess_failures(admin: dict | None = None) -> dict:
    """Reprograma envios em ERROR recuperável para nova tentativa imediata."""
    db = SessionLocal()
    try:
        n = (
            db.query(SuperfreteShipment)
            .filter(SuperfreteShipment.shipment_status == "ERROR")
            .update({"shipment_status": "PENDING_LABEL", "last_error": None,
                     "sync_attempts": 0, "next_sync_at": _iso(_now())}, synchronize_session=False)
        )
        db.commit()
        audit_service.log(db, "SUPERFRETE_REPROCESS_FAILURES", admin, None, {"count": n}, commit=True)
        return {"reprocessed": n}
    except Exception:
        db.rollback()
        return {"reprocessed": 0}
    finally:
        db.close()


# ---- Observabilidade ----
def get_sync_status(db: Session) -> dict:
    from app.services import superfrete_scheduler as sched
    s = db.get(SuperfreteSettings, 1)
    last = (
        db.query(SuperfreteSyncRun)
        .order_by(SuperfreteSyncRun.started_at.desc())
        .first()
    )
    active = (
        db.query(SuperfreteShipment)
        .filter(SuperfreteShipment.shipment_status.notin_(tuple(TERMINAL)),
                SuperfreteShipment.external_id.isnot(None))
        .count()
    )
    return {
        "scheduler_running": sched.is_running(),
        "cycle_seconds": settings.SUPERFRETE_SYNC_CYCLE_SECONDS,
        "sync_enabled": bool(s.sync_enabled) if s else False,
        "sync_suspended": bool(s.sync_suspended) if s else False,
        "sync_suspended_reason": s.sync_suspended_reason if s else None,
        "auth_valid": (s.status == "connected") if s else False,
        "provider_status": s.status if s else "not_configured",
        "is_enabled": bool(s.is_enabled and s.token_enc) if s else False,
        "active_shipments": active,
        "last_run": _run_row_public(last) if last else None,
    }


def _run_row_public(r: SuperfreteSyncRun) -> dict:
    return {
        "id": r.id, "trigger": r.trigger, "status": r.status,
        "started_at": r.started_at, "finished_at": r.finished_at, "duration_ms": r.duration_ms,
        "processed": r.processed, "updated": r.updated, "unchanged": r.unchanged,
        "failed": r.failed, "skipped": r.skipped, "last_error": r.last_error,
    }


def list_runs(db: Session, limit: int = 20) -> list:
    rows = (
        db.query(SuperfreteSyncRun)
        .order_by(SuperfreteSyncRun.started_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [_run_row_public(r) for r in rows]


def timeline(db: Session, shipment_id: str) -> list:
    """Timeline sanitizada de eventos de um envio (ordem cronológica)."""
    rows = (
        db.query(SuperfreteEvent)
        .filter(SuperfreteEvent.shipment_id == shipment_id)
        .order_by(SuperfreteEvent.created_at.asc())
        .all()
    )
    return [
        {
            "id": e.id, "source": e.source, "status": e.normalized_status,
            "raw_status": e.raw_status, "description": e.description,
            "provider_event_at": e.provider_event_at, "received_at": e.received_at,
            "created_at": e.created_at,
        }
        for e in rows
    ]
