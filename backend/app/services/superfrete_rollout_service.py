"""SuperFrete — Etapa E: saúde do rollout + governança (informativo + manual).

- Painel de KPIs/comparação/funil/alertas/recomendação (READ-ONLY).
- Guardrails na troca de modo (bloqueiam, nunca alteram sozinhos).
- Rollback manual para DISABLED (não cancela envios existentes).
- NENHUM auto-rollout. Pedidos de teste (is_test_order) fora das métricas reais.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models import (
    MelhorEnvioShipment,
    Order,
    ShippingQuote,
    SuperfreteRolloutHistory,
    SuperfreteSettings,
    SuperfreteShipment,
    SuperfreteSyncRun,
)
from app.services import audit_service
from app.services import superfrete_service as sf
from app.services import superfrete_sync_service as sync

_ALERT_COOLDOWN_SECONDS = 6 * 3600
_ROLLBACK_CONFIRM = "DESATIVAR SUPERFRETE"
_ROLLOUT_MODES = ("DISABLED", "TEST_ORDER_ONLY", "ADMIN_ONLY", "PERCENTAGE", "ENABLED")
_TRANSIT = ("POSTED", "IN_TRANSIT", "OUT_FOR_DELIVERY")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def period_bounds(period: str, start: str | None, end: str | None) -> tuple[str, str]:
    now = _now()
    if period == "custom" and start and end:
        return start, end
    days = {"24h": 1, "7d": 7, "30d": 30}.get(period, 7)
    return _iso(now - timedelta(days=days)), _iso(now)


def _in(created_at: str | None, a: str, b: str) -> bool:
    return bool(created_at) and a <= created_at <= b


def _avg(vals: list) -> float | None:
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None


def _classify_error(text: str | None) -> str | None:
    if not text:
        return None
    t = str(text).lower()
    if "401" in t or "403" in t or "autentic" in t:
        return "auth"
    if "429" in t or "limite de requisi" in t:
        return "rate_limit"
    if "timeout" in t or "indispon" in t:
        return "timeout"
    if "http 5" in t or " 500" in t or " 502" in t or " 503" in t:
        return "server_5xx"
    return None


# ----------------------------- KPIs / saúde -----------------------------
def compute_health(db: Session, period: str = "7d", start: str | None = None,
                   end: str | None = None, include_test: bool = False) -> dict:
    s = sf._get(db)
    a, b = period_bounds(period, start, end)

    orders = [o for o in db.query(Order).all()
              if not o.deleted_at and _in(o.created_at, a, b)
              and (include_test or not getattr(o, "is_test_order", False))]
    eligible = len(orders)
    sf_orders = [o for o in orders if (o.shipping_provider or "") == "superfrete"]
    me_orders = [o for o in orders if (o.shipping_provider or "") in ("melhor_envio", "", None) or o.shipping_provider is None]
    # ME = todos que não foram SuperFrete
    me_orders = [o for o in orders if o not in sf_orders]
    n_sf, n_me = len(sf_orders), len(me_orders)
    pct_real = round(100.0 * n_sf / (n_sf + n_me), 1) if (n_sf + n_me) else 0.0

    ships = [sh for sh in db.query(SuperfreteShipment).all() if _in(sh.created_at, a, b)]
    if not include_test and s.test_order_id:
        ships = [sh for sh in ships if sh.order_id != s.test_order_id]
    order_created = {o.id: o.created_at for o in db.query(Order).all()}
    ships_created = len(ships)
    ships_error = sum(1 for sh in ships if sh.shipment_status == "ERROR")
    labels_api = sum(1 for sh in ships if sh.label_status == "issued_api")
    labels_hybrid = sum(1 for sh in ships if sh.label_status == "issued_panel")
    tracking_ok = sum(1 for sh in ships if sh.tracking_code)
    delivered = sum(1 for sh in ships if sh.shipment_status == "DELIVERED")
    returned = sum(1 for sh in ships if sh.shipment_status == "RETURNED")

    def _secs(x, y):
        try:
            return (datetime.fromisoformat(x) - datetime.fromisoformat(y)).total_seconds()
        except Exception:
            return None
    time_to_create = _avg([_secs(sh.created_at, order_created.get(sh.order_id))
                           for sh in ships if order_created.get(sh.order_id)])
    active = [sh for sh in ships if sh.shipment_status not in sync.TERMINAL and sh.external_id]
    time_since_update = _avg([_secs(_iso(_now()), sh.last_sync_at) for sh in active if sh.last_sync_at])

    runs = [r for r in db.query(SuperfreteSyncRun).all() if _in(r.started_at, a, b)]
    processed = sum(r.processed or 0 for r in runs)
    failed_runs = sum(r.failed or 0 for r in runs)
    sync_ok_rate = round(100.0 * (processed - failed_runs) / processed, 1) if processed else None

    err_counts = {"auth": 0, "rate_limit": 0, "timeout": 0, "server_5xx": 0}
    for sh in ships:
        c = _classify_error(sh.last_error)
        if c:
            err_counts[c] += 1
    for r in runs:
        c = _classify_error(r.last_error)
        if c:
            err_counts[c] += 1

    quotes_recorded = sum(1 for q in db.query(ShippingQuote).all() if _in(q.created_at, a, b))

    kpis = {
        "eligible_orders": eligible, "orders_superfrete": n_sf, "orders_melhor_envio": n_me,
        "pct_superfrete_real": pct_real,
        "quotes_recorded": quotes_recorded,          # total (não separável por provider)
        "shipments_created": ships_created, "shipments_error": ships_error,
        "labels_api": labels_api, "labels_hybrid": labels_hybrid,
        "tracking_obtained": tracking_ok, "delivered": delivered, "returned": returned,
        "avg_seconds_to_shipment": time_to_create, "avg_seconds_without_update": time_since_update,
        "sync_ok_rate": sync_ok_rate,
        "err_401_403": err_counts["auth"], "err_429": err_counts["rate_limit"],
        "err_5xx": err_counts["server_5xx"], "err_timeout": err_counts["timeout"],
    }
    # Campos sem fonte confiável hoje (honestidade dos dados)
    no_data_fields = ["quotes_superfrete_success", "quotes_superfrete_failed"]

    comparison = _comparison(db, a, b, sf_orders, me_orders, ships, include_test, s)
    funnel = _funnel(eligible, sf_orders, ships)
    observed = _observed_percentage(db, a, b, s, include_test)
    alerts, alert_state = _alerts(db, s, kpis, active)
    recommendation = _recommendation(s, kpis, alerts)

    # cooldown/registro (mutação leve, admin-only)
    _persist_alert_state(db, s, alert_state)

    return {
        "period": {"start": a, "end": b, "label": period}, "include_test": include_test,
        "kpis": kpis, "no_data_fields": no_data_fields,
        "comparison": comparison, "funnel": funnel,
        "percentage": {"configured": int(s.rollout_percentage or 0),
                       "observed": observed["observed"], "delta": observed["delta"],
                       "sample": observed["sample"]},
        "alerts": alerts, "recommendation": recommendation,
        "rollout_mode": s.rollout_mode or "ENABLED",
        "min_orders": int(s.rollout_min_orders or 20),
        "validation_status": (s.controlled_test_state or {}).get("status", "PENDING"),
    }


def _comparison(db, a, b, sf_orders, me_orders, ships, include_test, s) -> dict:
    me_ships = [m for m in db.query(MelhorEnvioShipment).all() if _in(m.created_at, a, b)]
    return {
        "superfrete": {
            "avg_freight": _avg([float(sh.quoted_price) for sh in ships if sh.quoted_price is not None]),
            "avg_delivery_days": _avg([sh.estimated_days for sh in ships if sh.estimated_days]),
            "volume": len(sf_orders),
            "operational_errors": sum(1 for sh in ships if sh.shipment_status == "ERROR"),
            "delivered": sum(1 for sh in ships if sh.shipment_status == "DELIVERED"),
            "returned": sum(1 for sh in ships if sh.shipment_status == "RETURNED"),
        },
        "melhor_envio": {
            "avg_freight": _avg([float(m.price) for m in me_ships if m.price is not None]),
            "avg_delivery_days": _avg([o.shipping_delivery_max for o in me_orders if o.shipping_delivery_max]),
            "volume": len(me_orders),
            "operational_errors": sum(1 for m in me_ships if (m.internal_status or "") == "error"),
            "delivered": sum(1 for m in me_ships if (m.internal_status or "") == "delivered" or m.delivered_at),
            "returned": 0,  # ME legado não rastreia devolução
        },
    }


def _funnel(eligible, sf_orders, ships) -> list:
    stages = [
        ("Elegível", eligible),
        ("Cotação", len(sf_orders)),
        ("Escolha", sum(1 for o in sf_orders if o.shipping_service_id)),
        ("Shipment", len(ships)),
        ("Etiqueta", sum(1 for sh in ships if sh.label_status in ("issued_api", "issued_panel") or sh.label_url)),
        ("Tracking", sum(1 for sh in ships if sh.tracking_code)),
        ("Em trânsito", sum(1 for sh in ships if sh.shipment_status in _TRANSIT)),
        ("Entregue", sum(1 for sh in ships if sh.shipment_status == "DELIVERED")),
    ]
    out = []
    for i, (name, count) in enumerate(stages):
        prev = stages[i - 1][1] if i else count
        conv = round(100.0 * count / prev, 1) if prev else 0.0
        out.append({"stage": name, "count": count, "conversion_from_prev": conv})
    return out


def _observed_percentage(db, a, b, s, include_test) -> dict:
    """% observado calculado apenas sobre pedidos elegíveis logados criados após a última
    mudança de rollout (ignora anônimos não elegíveis, teste e pedidos anteriores)."""
    last_change = (db.query(SuperfreteRolloutHistory)
                   .order_by(SuperfreteRolloutHistory.created_at.desc()).first())
    since = max(a, last_change.created_at) if last_change and last_change.created_at else a
    sample = [o for o in db.query(Order).all()
              if not o.deleted_at and _in(o.created_at, since, b)
              and (include_test or not getattr(o, "is_test_order", False))
              and o.user_id]  # elegível = pedido logado
    n = len(sample)
    n_sf = sum(1 for o in sample if (o.shipping_provider or "") == "superfrete")
    observed = round(100.0 * n_sf / n, 1) if n else 0.0
    return {"observed": observed, "delta": round(observed - int(s.rollout_percentage or 0), 1), "sample": n}


# ----------------------------- Alertas -----------------------------
def _alerts(db, s, kpis, active) -> tuple[list, dict]:
    state = dict(s.rollout_alert_state or {})
    now = _now()
    found = []

    def add(code, severity, message, count=0):
        found.append({"code": code, "severity": severity, "message": message, "count": count})

    if s.sync_suspended or s.status == "error":
        add("AUTH_FAILURE", "critical", "Autenticação inválida/suspensa. Verifique o token.", 1)
    created, err = kpis["shipments_created"], kpis["shipments_error"]
    if created >= 5 and err / created > 0.2:
        add("HIGH_ERROR_RATE", "warning", f"Taxa de erro alta em envios ({err}/{created}).", err)
    stale = [sh for sh in active if sh.last_sync_at and
             (now - datetime.fromisoformat(sh.last_sync_at)).total_seconds() > 12 * 3600]
    if stale:
        add("SYNC_STALE", "warning", f"{len(stale)} envio(s) sem atualização há muito tempo.", len(stale))
    if kpis["err_429"] > 0:
        add("RATE_LIMIT", "warning", f"{kpis['err_429']} ocorrência(s) de limite de requisições (429).", kpis["err_429"])
    pend = [sh for sh in active if sh.shipment_status in ("PENDING_LABEL", "LABEL_READY") and sh.created_at and
            (now - datetime.fromisoformat(sh.created_at)).total_seconds() > 48 * 3600]
    if pend:
        add("LABEL_PENDING", "info", f"{len(pend)} envio(s) aguardando etiqueta há mais de 48h.", len(pend))
    miss = [sh for sh in active if sh.shipment_status in _TRANSIT and not sh.tracking_code]
    if miss:
        add("TRACKING_MISSING", "info", f"{len(miss)} envio(s) em trânsito sem código de rastreio.", len(miss))
    if kpis["delivered"] and kpis["returned"] / max(kpis["delivered"], 1) > 0.1:
        add("RETURN_RATE_HIGH", "warning", "Taxa de devolução acima do esperado.", kpis["returned"])
    delayed = 0
    for sh in active:
        if sh.estimated_days and sh.created_at:
            try:
                due = datetime.fromisoformat(sh.created_at) + timedelta(days=sh.estimated_days + 2)
                if now > due and sh.shipment_status != "DELIVERED":
                    delayed += 1
            except Exception:
                pass
    if delayed:
        add("DELIVERY_DELAY", "warning", f"{delayed} envio(s) com entrega atrasada.", delayed)

    # cooldown: marca quais devem "disparar" (log/notify) sem repetir a cada ciclo
    for alert in found:
        last = state.get(alert["code"])
        should = (not last) or (now - datetime.fromisoformat(last)).total_seconds() > _ALERT_COOLDOWN_SECONDS
        alert["throttled"] = not should
        if should:
            state[alert["code"]] = _iso(now)
    # limpa cooldown de alertas que não estão mais ativos
    active_codes = {a["code"] for a in found}
    for code in list(state.keys()):
        if code not in active_codes:
            state.pop(code, None)
    return found, state


def _persist_alert_state(db, s, state) -> None:
    if (s.rollout_alert_state or {}) != state:
        s.rollout_alert_state = state
        flag_modified(s, "rollout_alert_state")
        db.commit()


# ----------------------------- Recomendação -----------------------------
def _recommendation(s, kpis, alerts) -> dict:
    codes = {a["code"] for a in alerts}
    reasons = []
    if "AUTH_FAILURE" in codes:
        return {"recommendation": "RECOMENDA_DESABILITAR", "reason_codes": ["AUTH_FAILURE_PERSISTENT"]}
    if codes & {"HIGH_ERROR_RATE", "RATE_LIMIT", "SYNC_STALE", "TRACKING_MISSING", "DELIVERY_DELAY", "RETURN_RATE_HIGH"}:
        reasons = sorted(codes)
        return {"recommendation": "RECOMENDA_REDUZIR", "reason_codes": reasons}
    healthy = (s.status == "connected" and not s.sync_suspended
               and (kpis["sync_ok_rate"] is None or kpis["sync_ok_rate"] >= 90))
    enough_volume = kpis["orders_superfrete"] >= int(s.rollout_min_orders or 20)
    if healthy and enough_volume and (s.rollout_mode or "") in ("ADMIN_ONLY", "PERCENTAGE"):
        return {"recommendation": "PODE_AUMENTAR",
                "reason_codes": ["CONNECTION_STABLE", "LOW_ERROR", "SYNC_HEALTHY", "VOLUME_OK"]}
    return {"recommendation": "MANTER", "reason_codes": ["STABLE"] if healthy else ["INSUFFICIENT_SIGNAL"]}


# ----------------------------- Guardrails -----------------------------
def evaluate_guardrails(db: Session, to_mode: str, to_percentage: int | None) -> dict:
    s = sf._get(db)
    from_mode = s.rollout_mode or "ENABLED"
    blockers = []
    validation = (s.controlled_test_state or {}).get("status", "PENDING")
    real_sf = db.query(SuperfreteShipment).filter(
        or_(SuperfreteShipment.order_id != s.test_order_id, s.test_order_id.is_(None))
    ).count() if s.test_order_id else db.query(SuperfreteShipment).count()

    if to_mode not in _ROLLOUT_MODES:
        blockers.append("Modo inválido.")
    if to_mode == "PERCENTAGE" and not (to_percentage and 1 <= int(to_percentage) <= 100):
        blockers.append("Percentual deve estar entre 1 e 100.")
    if not (s.is_enabled and s.token_enc) and to_mode not in ("DISABLED", "TEST_ORDER_ONLY"):
        blockers.append("Configure e habilite o token da SuperFrete antes de liberar.")

    # ADMIN_ONLY -> PERCENTAGE
    if from_mode == "ADMIN_ONLY" and to_mode == "PERCENTAGE":
        if validation != "APPROVED":
            blockers.append("Validação controlada não aprovada. Rode o Teste controlado até VALIDAÇÃO APROVADA.")
    # PERCENTAGE -> ENABLED (e qualquer -> ENABLED exige critérios completos)
    if to_mode == "ENABLED" and from_mode != "ENABLED":
        if validation != "APPROVED":
            blockers.append("Validação controlada não aprovada.")
        if real_sf < int(s.rollout_min_orders or 20):
            blockers.append(f"Mínimo de {int(s.rollout_min_orders or 20)} pedidos reais SuperFrete não atingido (atual: {real_sf}).")
        if s.sync_suspended:
            blockers.append("Sincronização suspensa (autenticação). Resolva antes de liberar para todos.")
        if s.status != "connected":
            blockers.append("Sincronizador/conexão não saudável.")
    return {"from_mode": from_mode, "to_mode": to_mode, "allowed": len(blockers) == 0,
            "blockers": blockers, "validation_status": validation, "real_superfrete_orders": real_sf}


def _metrics_snapshot(db: Session) -> dict:
    h = compute_health(db, "7d")
    return {"pct_real": h["kpis"]["pct_superfrete_real"], "shipments_created": h["kpis"]["shipments_created"],
            "shipments_error": h["kpis"]["shipments_error"], "sync_ok_rate": h["kpis"]["sync_ok_rate"],
            "recommendation": h["recommendation"]["recommendation"]}


def change_rollout(db: Session, admin: dict, to_mode: str, to_percentage: int | None, reason: str) -> dict:
    if not (reason or "").strip():
        raise HTTPException(status_code=400, detail="Motivo é obrigatório para alterar o rollout.")
    guard = evaluate_guardrails(db, to_mode, to_percentage)
    if not guard["allowed"]:
        raise HTTPException(status_code=400, detail="Bloqueado pelos guardrails: " + " ".join(guard["blockers"]))
    s = sf._get(db)
    from_mode, from_pct = s.rollout_mode or "ENABLED", int(s.rollout_percentage or 0)
    snapshot = _metrics_snapshot(db)
    s.rollout_mode = to_mode
    if to_mode == "PERCENTAGE":
        s.rollout_percentage = max(0, min(100, int(to_percentage or 0)))
    db.commit()
    _log_history(db, admin, from_mode, to_mode, from_pct, int(s.rollout_percentage or 0), reason.strip(), snapshot)
    return {"ok": True, "rollout_mode": s.rollout_mode, "rollout_percentage": int(s.rollout_percentage or 0)}


def rollback(db: Session, admin: dict, reason: str, confirm: str) -> dict:
    if (confirm or "").strip() != _ROLLBACK_CONFIRM:
        raise HTTPException(status_code=400, detail=f'Confirmação inválida. Digite exatamente "{_ROLLBACK_CONFIRM}".')
    if not (reason or "").strip():
        raise HTTPException(status_code=400, detail="Motivo é obrigatório.")
    s = sf._get(db)
    from_mode, from_pct = s.rollout_mode or "ENABLED", int(s.rollout_percentage or 0)
    snapshot = _metrics_snapshot(db)
    s.rollout_mode = "DISABLED"
    db.commit()  # NÃO cancela shipments existentes; scheduler segue acompanhando
    _log_history(db, admin, from_mode, "DISABLED", from_pct, int(s.rollout_percentage or 0),
                 "[ROLLBACK] " + reason.strip(), snapshot)
    return {"ok": True, "rollout_mode": "DISABLED"}


def _log_history(db, admin, from_mode, to_mode, from_pct, to_pct, reason, snapshot) -> None:
    db.add(SuperfreteRolloutHistory(
        id=str(uuid.uuid4()), from_mode=from_mode, to_mode=to_mode,
        from_percentage=from_pct, to_percentage=to_pct,
        admin_id=(admin or {}).get("id"), admin_email=(admin or {}).get("email"),
        reason=reason[:500], metrics_snapshot=snapshot, created_at=_iso(_now()),
    ))
    db.commit()
    audit_service.log(db, "SUPERFRETE_ROLLOUT_CHANGED", admin, None,
                      {"from": from_mode, "to": to_mode, "from_pct": from_pct, "to_pct": to_pct}, commit=True)


def list_history(db: Session, limit: int = 50) -> list:
    rows = (db.query(SuperfreteRolloutHistory)
            .order_by(SuperfreteRolloutHistory.created_at.desc()).limit(min(limit, 200)).all())
    return [{
        "id": r.id, "from_mode": r.from_mode, "to_mode": r.to_mode,
        "from_percentage": r.from_percentage, "to_percentage": r.to_percentage,
        "admin_email": r.admin_email, "reason": r.reason,
        "metrics_snapshot": r.metrics_snapshot, "created_at": r.created_at,
    } for r in rows]
