"""Billing & comms endpoints: invoices, email settings + campaigns, inventory.

Admin-gated except two public routes that share the order-tracking trust model:
  • GET /api/orders/{public_id}/invoice.pdf — anyone holding the (unguessable)
    order id can download its invoice, exactly like tracking the order.
  • GET /api/email/unsubscribe — one-click opt-out from promotional email via an
    HMAC token (transactional invoices are unaffected by the flag).
"""
import hashlib
import hmac
import threading

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from .. import config, crud, emailer, inventory, invoicing, models, schemas
from ..database import SessionLocal, get_db
from ..deps import get_current_admin

router = APIRouter(prefix="/api", tags=["billing"])
admin = Depends(get_current_admin)


# --- Invoices (admin) -----------------------------------------------------------

@router.get("/admin/invoices")
def list_invoices(q: str = "", status: str = "", limit: int = 100,
                  db: Session = Depends(get_db), user=admin):
    rows = (db.query(models.Invoice)
            .order_by(models.Invoice.created_at.desc(), models.Invoice.id.desc())
            .limit(max(1, min(limit, 500))).all())
    out = []
    needle = (q or "").strip().lower()
    for inv in rows:
        if status and inv.status != status:
            continue
        data = invoicing.serialize_invoice(inv)
        if needle and needle not in (data["number"] + " " + data["order_public_id"] + " "
                                     + (data["customer_name"] or "") + " "
                                     + (data["customer_email"] or "")).lower():
            continue
        out.append(data)
    return {"invoices": out}


@router.post("/admin/orders/{public_id}/invoice/send")
def send_order_invoice(public_id: str, db: Session = Depends(get_db), user=admin):
    order = crud.get_order(db, public_id.strip().upper())
    if not order:
        raise HTTPException(404, "Order not found.")
    if not (order.customer_email or "").strip():
        raise HTTPException(400, "This order has no customer email.")
    if not emailer.enabled(db):
        raise HTTPException(400, "Email is not configured yet — see /admin → Email.")
    ok = invoicing.send_invoice(db, order)
    if not ok:
        raise HTTPException(502, "Could not send: " + (emailer.last_error() or "unknown error"))
    inv = order.invoice
    return {"ok": True, "invoice": invoicing.serialize_invoice(inv, order)}


@router.patch("/admin/invoices/{number}")
def patch_invoice(number: str, data: schemas.InvoicePatch,
                  db: Session = Depends(get_db), user=admin):
    inv = (db.query(models.Invoice)
           .filter(models.Invoice.number == number.strip().upper()).first())
    if not inv:
        raise HTTPException(404, "Invoice not found.")
    if data.status is not None:
        if data.status not in ("void", "draft"):
            raise HTTPException(400, "Status can only be set to void (or draft to un-void).")
        inv.status = data.status
    if data.notes is not None:
        inv.notes = data.notes
    db.commit()
    return invoicing.serialize_invoice(inv)


def _pdf_response(inv) -> Response:
    try:
        pdf = invoicing.build_pdf(inv)
    except Exception:
        raise HTTPException(500, "Could not render the invoice PDF.")
    return Response(content=pdf, media_type="application/pdf", headers={
        "Content-Disposition": 'inline; filename="%s.pdf"' % inv.number,
        "Cache-Control": "no-store",
    })


@router.get("/admin/invoices/{number}.pdf")
def admin_invoice_pdf(number: str, db: Session = Depends(get_db), user=admin):
    inv = (db.query(models.Invoice)
           .filter(models.Invoice.number == number.strip().upper()).first())
    if not inv:
        raise HTTPException(404, "Invoice not found.")
    return _pdf_response(inv)


# --- Invoice (public, by order id — same trust as order tracking) ----------------

@router.get("/orders/{public_id}/invoice.pdf")
def public_invoice_pdf(public_id: str, db: Session = Depends(get_db)):
    order = crud.get_order(db, public_id.strip().upper())
    if not order or not order.invoice:
        raise HTTPException(404, "Invoice not found.")
    if order.invoice.status == "void":
        raise HTTPException(404, "Invoice not found.")
    return _pdf_response(order.invoice)


# --- Email settings / test / log (admin) -----------------------------------------

@router.get("/admin/email/settings")
def email_settings(db: Session = Depends(get_db), user=admin):
    return emailer.status(db)


@router.put("/admin/email/settings")
def save_email_settings(data: schemas.EmailSettingsIn,
                        db: Session = Depends(get_db), user=admin):
    emailer.save_settings(db, data.model_dump(exclude_none=True))
    return emailer.status(db)


@router.post("/admin/email/test")
def send_test_email(db: Session = Depends(get_db), user=admin):
    if not emailer.enabled(db):
        raise HTTPException(400, "Email is not configured yet (no transport / from-address).")
    ok = emailer.send(db, config.OWNER_EMAIL, "Email test — outbound email works",
                      "<p>Success — outbound email from your site works. 🎉</p>",
                      kind="test", background=False)
    if not ok:
        raise HTTPException(502, "Send failed: " + (emailer.last_error() or "unknown error"))
    return {"ok": True, "to": config.OWNER_EMAIL}


@router.get("/admin/email/log")
def email_log(limit: int = 50, db: Session = Depends(get_db), user=admin):
    rows = (db.query(models.EmailLog)
            .order_by(models.EmailLog.created_at.desc(), models.EmailLog.id.desc())
            .limit(max(1, min(limit, 200))).all())
    return {"log": [
        {"id": r.id, "kind": r.kind, "to": r.to_email or "", "subject": r.subject,
         "ok": r.ok, "error": r.error or "", "created_at": r.created_at}
        for r in rows
    ]}


# --- Promotional campaigns --------------------------------------------------------

def _unsub_token(user_id: int) -> str:
    return hmac.new(config.SECRET_KEY.encode("utf-8"),
                    b"unsubscribe:%d" % user_id, hashlib.sha256).hexdigest()[:32]


def _campaign_html(db, body_html: str, user_id: int) -> str:
    doc = emailer.get_settings(db)
    base = config.PUBLIC_BASE_URL or "https://smarnb.onrender.com"
    unsub = "%s/api/email/unsubscribe?u=%d&t=%s" % (base, user_id, _unsub_token(user_id))
    return (
        "<div style='font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
        "max-width:560px;margin:0 auto;color:#171723'>"
        "%s"   # brand header band (first-party CSS mark, no raster image)
        "<div style='border:1px solid #e8eaf3;border-top:0;border-radius:0 0 12px 12px;"
        "padding:22px;font-size:15px;line-height:1.6'>%s"
        "<p style='margin:22px 0 0;color:#9aa1b5;font-size:12px'>%s · "
        "<a href='%s' style='color:#9aa1b5'>Unsubscribe</a></p>"
        "</div></div>"
        % (emailer.brand_header_html(doc.get("from_name")), body_html,
           doc.get("promo_footer") or "", unsub)
    )


@router.post("/admin/email/campaign")
def send_campaign(data: schemas.CampaignIn, db: Session = Depends(get_db), user=admin):
    if not emailer.enabled(db):
        raise HTTPException(400, "Email is not configured yet (no transport / from-address).")
    from ..blog_render import render_markdown
    body_html = render_markdown(data.body_md)

    if data.test_only:
        ok = emailer.send(db, config.OWNER_EMAIL, "[TEST] " + data.subject,
                          _campaign_html(db, body_html, user.id),
                          kind="promo", background=False)
        if not ok:
            raise HTTPException(502, "Send failed: " + (emailer.last_error() or "unknown error"))
        return {"ok": True, "sent": 1, "skipped": 0, "test_only": True}

    clients = (db.query(models.User)
               .filter(models.User.role == "client").all())
    audience = [(c.id, c.email) for c in clients
                if (c.email or "").strip() and not bool(c.email_opt_out)]
    skipped = len(clients) - len(audience)
    subject = data.subject

    def _blast(pairs):
        bg = SessionLocal()
        try:
            for uid, email in pairs:
                emailer.send(bg, email, subject, _campaign_html(bg, body_html, uid),
                             kind="promo", background=False)
        finally:
            bg.close()

    if emailer._test_capture:  # tests: run synchronously for deterministic capture
        _blast(audience)
    else:
        threading.Thread(target=_blast, args=(audience,), daemon=True).start()
    return {"ok": True, "sent": len(audience), "skipped": skipped, "test_only": False}


@router.get("/email/unsubscribe", response_class=HTMLResponse)
def unsubscribe(u: int, t: str = "", db: Session = Depends(get_db)):
    user = db.get(models.User, u)
    ok = bool(user and t and hmac.compare_digest(t, _unsub_token(u)))
    if ok:
        user.email_opt_out = True
        db.commit()
    title = "You're unsubscribed" if ok else "Link not valid"
    body = ("You won't receive promotional emails any more. Order receipts and "
            "invoices still arrive normally." if ok else
            "This unsubscribe link is invalid or expired.")
    return HTMLResponse(
        "<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
        "<title>%s</title>"
        "<body style='font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0a0d14;"
        "color:#eef2f9;display:grid;place-items:center;min-height:100vh;margin:0'>"
        "<div style='text-align:center;padding:2rem'>"
        "<div style='width:56px;height:56px;border-radius:14px;background:#6366f1;color:#fff;"
        "display:grid;place-items:center;font-weight:800;font-size:1.4rem;margin:0 auto 1rem'>S</div>"
        "<h1 style='font-size:1.3rem;margin:0 0 .4rem'>%s</h1>"
        "<p style='color:#9aa6bd;margin:0'>%s</p></div></body>" % (title, title, body),
        status_code=200 if ok else 400)


# --- Inventory (admin) -------------------------------------------------------------

@router.get("/admin/inventory")
def list_inventory(db: Session = Depends(get_db), user=admin):
    return {"items": [inventory.serialize_item(i) for i in inventory.list_items(db)]}


@router.post("/admin/inventory")
def create_inventory_item(data: schemas.InventoryItemIn,
                          db: Session = Depends(get_db), user=admin):
    if inventory.get_item_by_sku(db, data.sku):
        raise HTTPException(400, "That SKU already exists.")
    item = inventory.create_item(db, sku=data.sku, name=data.name, kind=data.kind,
                                 stock=data.stock,
                                 low_stock_threshold=data.low_stock_threshold,
                                 notes=data.notes)
    if data.stock is not None:
        inventory.adjust_stock(db, item, 0, reason="correction", note="initial stock set")
    return inventory.serialize_item(item)


@router.patch("/admin/inventory/{item_id}")
def patch_inventory_item(item_id: int, data: schemas.InventoryItemPatch,
                         db: Session = Depends(get_db), user=admin):
    item = inventory.get_item(db, item_id)
    if not item:
        raise HTTPException(404, "Item not found.")
    fields = data.model_dump(exclude_none=True)
    fields.pop("untrack", None)
    if data.untrack:
        fields["stock"] = None
    elif "stock" not in fields:
        fields.pop("stock", None)
    if "sku" in fields:
        other = inventory.get_item_by_sku(db, fields["sku"])
        if other and other.id != item.id:
            raise HTTPException(400, "That SKU already exists.")
    item = inventory.update_item(db, item, **fields)
    return inventory.serialize_item(item)


@router.post("/admin/inventory/{item_id}/adjust")
def adjust_inventory(item_id: int, data: schemas.StockAdjust,
                     db: Session = Depends(get_db), user=admin):
    item = inventory.get_item(db, item_id)
    if not item:
        raise HTTPException(404, "Item not found.")
    if item.stock is None:
        raise HTTPException(400, "This item is untracked — set a stock number first.")
    item = inventory.adjust_stock(db, item, data.delta, reason=data.reason or "manual",
                                  note=data.note)
    return inventory.serialize_item(item)


@router.get("/admin/inventory/{item_id}/moves")
def inventory_moves(item_id: int, db: Session = Depends(get_db), user=admin):
    item = inventory.get_item(db, item_id)
    if not item:
        raise HTTPException(404, "Item not found.")
    return {"moves": [inventory.serialize_move(m) for m in inventory.moves_for(db, item)]}
