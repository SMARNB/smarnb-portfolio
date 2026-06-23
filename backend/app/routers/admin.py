from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from ..deps import get_current_admin

# Every route requires an admin (the developer).
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


# ---- Orders ------------------------------------------------------------------
@router.get("/orders", response_model=List[schemas.OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return [crud.serialize_order(o, reveal_final=True) for o in crud.all_orders(db)]


@router.get("/orders/{public_id}", response_model=schemas.OrderOut)
def get_order(public_id: str, db: Session = Depends(get_db)):
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "Order not found.")
    return crud.serialize_order(order, reveal_final=True)


@router.patch("/orders/{public_id}", response_model=schemas.OrderOut)
def patch_order(public_id: str, data: schemas.OrderAdminPatch, db: Session = Depends(get_db)):
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "Order not found.")
    changes = []
    if data.status and data.status != order.status:
        if data.status not in models.STATUS_LABELS:
            raise HTTPException(400, "Unknown status.")
        order.status = data.status
        changes.append("status → " + models.STATUS_LABELS[data.status])
    if data.progress is not None and data.progress != order.progress:
        order.progress = data.progress
        changes.append("progress → {}%".format(data.progress))
    if data.due_date is not None:
        order.due_date = data.due_date
    if data.notes is not None:
        order.notes = data.notes
    if data.payment_status and data.payment_status != order.payment_status:
        if data.payment_status not in ("unpaid", "paid", "refunded"):
            raise HTTPException(400, "Unknown payment status.")
        order.payment_status = data.payment_status
        changes.append("payment → " + data.payment_status)
    db.commit()
    db.refresh(order)
    if changes:
        crud.add_update(db, order, "Updated " + ", ".join(changes) + ".",
                        status=order.status, progress=order.progress)
    return crud.serialize_order(order, reveal_final=True)


@router.post("/orders/{public_id}/updates", response_model=schemas.OrderOut)
def post_update(public_id: str, data: schemas.UpdateCreate, db: Session = Depends(get_db)):
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "Order not found.")
    if data.status and data.status not in models.STATUS_LABELS:
        raise HTTPException(400, "Unknown status.")
    crud.add_update(db, order, data.message, status=data.status, progress=data.progress)
    return crud.serialize_order(order, reveal_final=True)


# ---- Deliverables (product files, gated by payment) --------------------------
@router.post("/orders/{public_id}/deliverables", response_model=schemas.OrderOut)
def add_deliverable(public_id: str, data: schemas.DeliverableIn, db: Session = Depends(get_db)):
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "Order not found.")
    crud.add_deliverable(db, order, data)
    return crud.serialize_order(order, reveal_final=True)


@router.delete("/deliverables/{did}", response_model=dict)
def delete_deliverable(did: int, db: Session = Depends(get_db)):
    d = crud.get_deliverable(db, did)
    if not d:
        raise HTTPException(404, "Not found.")
    crud.delete_deliverable(db, d)
    return {"ok": True}


# ---- Stats / clients ---------------------------------------------------------
@router.get("/stats", response_model=schemas.Stats)
def stats(db: Session = Depends(get_db)):
    return crud.stats(db)


@router.get("/clients")
def clients(db: Session = Depends(get_db)):
    out = []
    for u in db.query(models.User).filter(models.User.role == "client").all():
        out.append({"id": u.id, "name": u.name, "email": u.email, "whatsapp": u.whatsapp,
                    "created_at": u.created_at.isoformat(), "orders": len(u.orders)})
    return out


# ---- Services CRUD -----------------------------------------------------------
@router.get("/services", response_model=List[schemas.ServiceOut])
def list_services(db: Session = Depends(get_db)):
    return crud.list_services(db, active_only=False)


@router.post("/services", response_model=schemas.ServiceOut)
def create_service(data: schemas.ServiceIn, db: Session = Depends(get_db)):
    return crud.create_service(db, data)


@router.patch("/services/{sid}", response_model=schemas.ServiceOut)
def update_service(sid: int, data: schemas.ServiceIn, db: Session = Depends(get_db)):
    svc = crud.get_service(db, sid)
    if not svc:
        raise HTTPException(404, "Service not found.")
    return crud.update_service(db, svc, data)


@router.delete("/services/{sid}", response_model=dict)
def delete_service(sid: int, db: Session = Depends(get_db)):
    svc = crud.get_service(db, sid)
    if not svc:
        raise HTTPException(404, "Service not found.")
    crud.delete_service(db, svc)
    return {"ok": True}
