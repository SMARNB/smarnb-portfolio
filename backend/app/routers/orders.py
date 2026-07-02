from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, crypto, email_guard, email_send, schemas
from ..database import get_db
from ..deps import get_current_user, get_optional_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=schemas.OrderOut)
def create_order(data: schemas.OrderCreate, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    if not data.items:
        raise HTTPException(400, "Your order has no items.")
    # Always block throwaway addresses (cheap, no network).
    if email_guard.is_disposable(data.customer_email):
        raise HTTPException(400, "Temporary / disposable email addresses aren't allowed. Please use a permanent email.")
    # Once verification is configured, orders require a verified client account —
    # this is what stops anonymous spam order requests.
    if email_send.enabled():
        if not user or user.role != "client":
            raise HTTPException(401, "Please create an account and verify your email to place an order.")
        if not user.email_verified:
            raise HTTPException(403, "Please verify your email address before placing an order.")
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
