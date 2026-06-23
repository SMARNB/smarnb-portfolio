"""Payments.

- **Manual methods (Raast / SadaPay / JazzCash)** need no backend — the client
  sees the details, pays, uploads a receipt in chat, and the developer marks the
  order Paid. So there's nothing to wire here for those.
- **Stripe (card)** is OPTIONAL and stays OFF until `STRIPE_SECRET_KEY` is set
  (and the `stripe` package installed). The scaffold below is ready for the day you
  switch it on — no cost or external calls happen until then.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import config, crud
from ..database import get_db

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _stripe():
    """Return a configured stripe module, or None if not enabled/installed."""
    if not config.STRIPE_SECRET_KEY:
        return None
    try:
        import stripe
    except Exception:
        return None
    stripe.api_key = config.STRIPE_SECRET_KEY
    return stripe


@router.get("/config")
def payment_config():
    """Frontend uses this to decide whether to show the 'Pay with card' button."""
    return {"stripe_enabled": bool(config.STRIPE_SECRET_KEY)}


@router.post("/stripe/checkout/{public_id}")
def stripe_checkout(public_id: str, request: Request, db: Session = Depends(get_db)):
    stripe = _stripe()
    if not stripe:
        raise HTTPException(503, "Card payments aren't enabled yet.")
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.payment_status == "paid":
        raise HTTPException(400, "This order is already paid.")

    line_items = []
    for it in order.items:
        price = float(it.get("price", 0) or 0)
        qty = int(it.get("qty", 1) or 1)
        if price <= 0:
            continue
        name = (str(it.get("service", "Service")) + " — " + str(it.get("tier", ""))).strip(" —")[:120] or "Service"
        line_items.append({
            "price_data": {
                "currency": config.CURRENCY_CODE,
                "product_data": {"name": name},
                "unit_amount": int(round(price * 100)),
            },
            "quantity": qty,
        })
    if not line_items:
        raise HTTPException(400, "Nothing to charge on this order.")

    base = config.PUBLIC_BASE_URL or str(request.base_url).rstrip("/")
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=base + "/app?paid=" + order.public_id,
        cancel_url=base + "/app",
        client_reference_id=order.public_id,
        metadata={"public_id": order.public_id},
    )
    return {"url": session.url}


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    stripe = _stripe()
    if not stripe:
        raise HTTPException(503, "Stripe not enabled.")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        if config.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig, config.STRIPE_WEBHOOK_SECRET)
        else:
            event = json.loads(payload.decode() or "{}")
    except Exception:
        raise HTTPException(400, "Invalid webhook signature/payload.")

    if event.get("type") == "checkout.session.completed":
        obj = event["data"]["object"]
        pid = (obj.get("client_reference_id") or (obj.get("metadata") or {}).get("public_id") or "").strip().upper()
        order = crud.get_order(db, pid) if pid else None
        if order:
            crud.mark_paid(db, order, "Card payment received via Stripe. ✅")
    return {"received": True}
