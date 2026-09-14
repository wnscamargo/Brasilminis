"""Scheduler único (APScheduler) do job de sincronização SuperFrete.

- BackgroundScheduler dentro do processo FastAPI.
- Concorrência real entre múltiplas instâncias/pods é protegida pelo advisory
  lock global no PostgreSQL (ver superfrete_sync_service.run_sync_cycle):
  ciclos concorrentes simplesmente pulam (status=skipped_locked).
- Iniciar/parar via startup/shutdown do app.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings

logger = logging.getLogger("brasilminis.superfrete_scheduler")

_scheduler: BackgroundScheduler | None = None
_JOB_ID = "superfrete_sync_cycle"
_RECON_JOB_ID = "superfrete_reconcile"


def _cycle_job():
    try:
        from app.services import superfrete_sync_service as sync
        sync.run_sync_cycle(trigger="auto")
    except Exception:
        logger.exception("Falha no ciclo agendado SuperFrete")


def _reconcile_job():
    try:
        from app.services import superfrete_sync_service as sync
        sync.reconcile()
    except Exception:
        logger.exception("Falha na reconciliação agendada SuperFrete")


def start() -> None:
    global _scheduler
    if not settings.SUPERFRETE_SYNC_ENABLED:
        logger.info("SuperFrete scheduler desabilitado por configuração.")
        return
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="UTC", daemon=True)
    _scheduler.add_job(_cycle_job, "interval", seconds=settings.SUPERFRETE_SYNC_CYCLE_SECONDS,
                       id=_JOB_ID, max_instances=1, coalesce=True, replace_existing=True)
    # Reconciliação periódica (menos frequente).
    _scheduler.add_job(_reconcile_job, "interval",
                       seconds=max(settings.SUPERFRETE_SYNC_CYCLE_SECONDS * 6, 1800),
                       id=_RECON_JOB_ID, max_instances=1, coalesce=True, replace_existing=True)
    _scheduler.start()
    logger.info("SuperFrete scheduler iniciado (ciclo %ss).", settings.SUPERFRETE_SYNC_CYCLE_SECONDS)


def stop() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None


def is_running() -> bool:
    return _scheduler is not None and _scheduler.running
