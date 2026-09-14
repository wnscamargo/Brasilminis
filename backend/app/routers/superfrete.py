from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin, get_db
from app.services import superfrete_service as sf

router = APIRouter(prefix="/api", tags=["superfrete"])


@router.get("/superfrete/status")
def public_status(db: Session = Depends(get_db)):
    return sf.public_status(db)


@router.get("/admin/superfrete/config")
def admin_config(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.admin_config(db)


@router.put("/admin/superfrete/config")
def admin_update_config(payload: dict, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.update_config(db, payload, admin)


@router.post("/admin/superfrete/test")
def admin_test(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.test_connection(db, admin)


@router.post("/admin/superfrete/disconnect")
def admin_disconnect(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.disconnect(db, admin)


# ---------------- Etapa B: logística por pedido ----------------
from fastapi import HTTPException
from app.models import Order


def _order_or_404(db: Session, order_id: str) -> Order:
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return o


@router.get("/admin/orders/{order_id}/logistics")
def order_logistics(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.get_logistics(db, _order_or_404(db, order_id))


@router.post("/admin/orders/{order_id}/logistics/create")
def order_logistics_create(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.create_shipment(db, _order_or_404(db, order_id), admin)


@router.post("/admin/orders/{order_id}/logistics/sync")
def order_logistics_sync(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.sync_shipment(db, _order_or_404(db, order_id), admin)


@router.post("/admin/orders/{order_id}/logistics/retry")
def order_logistics_retry(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.retry_shipment(db, _order_or_404(db, order_id), admin)


@router.post("/admin/orders/{order_id}/logistics/tracking")
def order_logistics_tracking(order_id: str, payload: dict, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sf.set_tracking(db, _order_or_404(db, order_id), payload.get("tracking_code", ""), payload.get("external_id"), admin)


# ---------------- Etapa C: sincronização automática / observabilidade ----------------
from app.services import superfrete_sync_service as sync


@router.get("/admin/superfrete/sync/status")
def sync_status(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sync.get_sync_status(db)


@router.get("/admin/superfrete/sync/runs")
def sync_runs(limit: int = 20, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {"runs": sync.list_runs(db, limit)}


@router.post("/admin/superfrete/sync/run")
def sync_run_now(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    # Protegido contra execução simultânea via advisory lock global (skipped_locked).
    return sync.run_sync_cycle(trigger="manual", admin=admin)


@router.post("/admin/superfrete/sync/reprocess-failures")
def sync_reprocess(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sync.reprocess_failures(admin=admin)


@router.post("/admin/superfrete/sync/reconcile")
def sync_reconcile(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return sync.reconcile(admin=admin)


@router.get("/admin/orders/{order_id}/logistics/timeline")
def order_logistics_timeline(order_id: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    from app.models import SuperfreteShipment
    _order_or_404(db, order_id)
    sh = db.query(SuperfreteShipment).filter(SuperfreteShipment.order_id == order_id).first()
    return {"timeline": sync.timeline(db, sh.id) if sh else []}


# ---------------- Etapa D: produção controlada / teste ponta a ponta ----------------
from app.services import superfrete_controlled_test_service as ctest


@router.get("/admin/superfrete/controlled-test")
def ct_get(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.get_state(db)


@router.post("/admin/superfrete/controlled-test/reset")
def ct_reset(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.reset(db, admin)


@router.post("/admin/superfrete/controlled-test/params")
def ct_params(payload: dict, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.set_params(db, payload, admin)


@router.post("/admin/superfrete/controlled-test/connection")
def ct_connection(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.run_connection(db, admin)


@router.post("/admin/superfrete/controlled-test/quote")
def ct_quote(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.run_quote(db, admin)


@router.post("/admin/superfrete/controlled-test/select")
def ct_select(payload: dict, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.select_service(db, str(payload.get("service_id", "")), admin)


@router.post("/admin/superfrete/controlled-test/create")
def ct_create(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.create_shipment(db, admin)


@router.post("/admin/superfrete/controlled-test/consult")
def ct_consult(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.consult(db, admin)


@router.post("/admin/superfrete/controlled-test/label")
def ct_label(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.get_label(db, admin)


@router.post("/admin/superfrete/controlled-test/tracking")
def ct_tracking(payload: dict, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.capture_tracking(db, payload.get("tracking_code", ""), payload.get("external_id"), admin)


@router.post("/admin/superfrete/controlled-test/sync")
def ct_sync(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.run_sync(db, admin)


@router.post("/admin/superfrete/controlled-test/finalize")
def ct_finalize(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return ctest.finalize(db, admin)
