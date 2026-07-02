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

from .. import config, crud, safepay
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
    """Frontend uses this to decide which online-payment buttons to show."""
    return {"stripe_enabled": bool(config.STRIPE_SECRET_KEY),
            "safepay_enabled": safepay.enabled()}


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


# --- Safepay (Pakistan card/wallet, hosted redirect) --------------------------
_SAFEPAY_PAID_NOTE = "Card/wallet payment received via Safepay. ✅"


@router.post("/safepay/checkout/{public_id}")
def safepay_checkout(public_id: str, request: Request, return_to: str = "/app",
                     db: Session = Depends(get_db)):
    """Create a Safepay tracker and hand back the hosted-checkout URL to redirect to.
    The buyer pays on getsafepay.com, so nothing third-party runs on our origin.
    ``return_to`` is where Safepay sends the buyer back (the store checkout uses
    /store so a guest lands on the public site, not the login-gated /app)."""
    if not safepay.enabled():
        raise HTTPException(503, "Safepay isn't enabled yet.")
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.payment_status == "paid":
        raise HTTPException(400, "This order is already paid.")
    if not order.total or order.total <= 0:
        raise HTTPException(400, "Nothing to charge on this order.")

    tracker = safepay.create_tracker(order.total)
    if not tracker:
        raise HTTPException(502, "Could not start Safepay checkout. Please try again.")
    # Remember the tracker so the return/webhook can be verified against this order.
    order.payment_ref = tracker
    order.payment_method = order.payment_method or "Safepay"
    db.commit()

    base = config.PUBLIC_BASE_URL or str(request.base_url).rstrip("/")
    # Only allow a local return path (never an open redirect off our origin).
    rt = return_to if return_to.startswith("/") and not return_to.startswith("//") else "/app"
    sep = "&" if "?" in rt else "?"
    url = safepay.checkout_url(
        tracker,
        redirect_url=base + rt + sep + "sfpy=" + order.public_id,
        cancel_url=base + rt,
        order_id=order.public_id,
    )
    return {"url": url}


@router.get("/safepay/verify/{public_id}")
def safepay_verify(public_id: str, db: Session = Depends(get_db)):
    """Called by the client dashboard after the Safepay redirect. Re-verifies the
    stored tracker with Safepay server-side (the browser can't fake this) and marks
    the order paid if the payment actually completed."""
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.payment_status == "paid":
        return {"paid": True}
    if safepay.verify_tracker(order.payment_ref):
        crud.mark_paid(db, order, _SAFEPAY_PAID_NOTE)
        return {"paid": True}
    return {"paid": False}


@router.post("/safepay/webhook")
async def safepay_webhook(request: Request, db: Session = Depends(get_db)):
    """Safepay's server-to-server confirmation (a backstop to verify-on-return).
    Always 200 so Safepay never disables the webhook; a payment is only ever marked
    paid after the tracker is re-verified with Safepay's API (source of truth)."""
    if not safepay.enabled():
        return {"received": True}
    raw = await request.body()
    # (Optional) authenticate the sender when a webhook secret is configured — but the
    # authoritative check is always re-verifying the tracker's state with Safepay
    # below, so a spoofed post can never mark an order paid on its own.
    signature = request.headers.get("x-sfpy-signature", "") or request.headers.get("x-safepay-signature", "")
    safepay.verify_webhook_signature(raw, signature)
    try:
        body = json.loads(raw.decode() or "{}")
    except Exception:
        body = {}
    data = body.get("data") if isinstance(body, dict) else {}
    tracker = (body.get("tracker") or (data or {}).get("tracker")
               or (data or {}).get("token") or "")
    if tracker and safepay.verify_tracker(tracker):
        order = crud.get_order_by_payment_ref(db, tracker)
        if order:
            crud.mark_paid(db, order, _SAFEPAY_PAID_NOTE)
    return {"received": True}
