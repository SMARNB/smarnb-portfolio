from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, crypto, schemas
from ..database import get_db
from ..deps import get_current_user, get_optional_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=schemas.OrderOut)
def create_order(data: schemas.OrderCreate, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    if not data.items:
        raise HTTPException(400, "Your order has no items.")
    client = user if (user and user.role == "client") else None
    order = crud.create_order(db, data, client=client)
    return crud.serialize_order(order)


@router.get("/mine", response_model=List[schemas.OrderOut])
def my_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [crud.serialize_order(o) for o in crud.orders_for_user(db, user)]


@router.get("/{public_id}", response_model=schemas.OrderOut)
def track_order(public_id: str, db: Session = Depends(get_db)):
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "No order found with that ID.")
    return crud.serialize_order(order)


@router.post("/{public_id}/cancel", response_model=schemas.OrderOut)
def cancel_order(public_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "No order found with that ID.")
    if order.client_id != user.id and order.customer_email_bidx != crypto.blind_index(user.email):
        raise HTTPException(403, "This isn't your order.")
    if order.status not in ("received", "confirmed"):
        raise HTTPException(400, "This order is already in progress and can't be cancelled here — message me directly.")
    crud.add_update(db, order, "Order cancelled by the client.", status="cancelled")
    return crud.serialize_order(order)
