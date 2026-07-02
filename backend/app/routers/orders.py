from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import crud, crypto, email_guard, email_send, schemas
from ..database import get_db
from ..deps import get_current_user, get_optional_user
from .blog import MAX_IMAGE, _detect_image

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


@router.post("/{public_id}/proof", response_model=schemas.OrderOut)
async def upload_payment_proof(public_id: str, file: UploadFile = File(...),
                               ref: str = Form(""), db: Session = Depends(get_db)):
    """Attach a payment screenshot to an order after a MANUAL transfer (Raast /
    SadaPay / JazzCash). The screenshot should show the transfer's date & time;
    ``ref`` carries the buyer's transaction id / when-sent note. The developer
    reviews it in the admin dashboard and marks the order paid."""
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "No order found with that ID.")
    if order.payment_status == "paid":
        raise HTTPException(400, "This order is already paid — no proof needed.")
    raw = await file.read(MAX_IMAGE + 1)
    if len(raw) > MAX_IMAGE:
        raise HTTPException(413, "Screenshot is too large (max 6 MB).")
    if not raw:
        raise HTTPException(400, "Empty file.")
    ctype = _detect_image(raw)
    if not ctype:
        raise HTTPException(415, "Please upload the screenshot as PNG, JPG, GIF or WEBP.")
    name = (file.filename or "proof").rsplit("/", 1)[-1][:120] or "proof"
    crud.add_payment_proof(db, order, name, ctype, len(raw), raw, ref=ref)
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
