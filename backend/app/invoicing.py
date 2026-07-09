"""Invoices — branded PDF + email, snapshotted per order.

Lifecycle: ``ensure_invoice`` creates a draft snapshot (sequential number
INV-YYYY-NNNN) when the order is placed; ``on_order_paid`` marks it paid,
emails the customer a branded HTML message with the PDF attached (owner gets a
copy) and lets the inventory module consume stock. The admin can also send an
unpaid invoice as a payment request, void, or resend. Anyone who knows the
order's public id (the same trust as order tracking) can download the PDF.

The PDF is generated with fpdf2 (pure python — Render has no headless Chrome).
All email goes through emailer.py, so this whole flow is INERT until email is
configured; everything is best-effort and never breaks the payment path.
"""
import datetime as dt
import json

from . import config, models
from .database import SessionLocal


# --- Create / numbering -----------------------------------------------------------

def _next_number(db) -> str:
    year = dt.datetime.utcnow().year
    prefix = "INV-%d-" % year
    count = (db.query(models.Invoice)
             .filter(models.Invoice.number.like(prefix + "%")).count())
    return "%s%04d" % (prefix, count + 1)


def _lines_for(order) -> list:
    lines = []
    for it in (order.items or []):
        qty = int(it.get("qty") or 1)
        unit = float(it.get("price") or 0)
        title = (it.get("service") or "Service").strip()
        tier = (it.get("tier") or "").strip()
        if tier:
            title = "%s — %s" % (title, tier)
        lines.append({"title": title, "qty": qty, "unit": unit,
                      "amount": round(qty * unit, 2)})
    return lines


def ensure_invoice(db, order) -> models.Invoice:
    """Get the order's invoice, creating the draft snapshot if it doesn't exist."""
    if order.invoice:
        return order.invoice
    inv = models.Invoice(
        number=_next_number(db), order_id=order.id, currency=config.CURRENCY,
        subtotal=order.total or 0, total=order.total or 0,
        lines_json=json.dumps(_lines_for(order)),
        status="draft",
    )
    db.add(inv)
    db.commit()
    db.refresh(order)
    return order.invoice


def serialize_invoice(inv: models.Invoice, order=None) -> dict:
    order = order or inv.order
    return {
        "number": inv.number, "status": inv.status, "currency": inv.currency,
        "subtotal": inv.subtotal, "total": inv.total, "lines": inv.lines,
        "notes": inv.notes or "", "created_at": inv.created_at,
        "sent_at": inv.sent_at, "paid_at": inv.paid_at,
        "order_public_id": order.public_id if order else "",
        "customer_name": (order.customer_name or "") if order else "",
        "customer_email": (order.customer_email or "") if order else "",
        "payment_status": order.payment_status if order else "",
    }


# --- PDF -------------------------------------------------------------------------

_INDIGO = (99, 102, 241)
_INK = (23, 23, 35)
_MUTED = (100, 108, 130)
_LINE = (226, 229, 240)


def _latin(s: str) -> str:
    """fpdf core fonts are latin-1 — replace anything outside it."""
    return (s or "").encode("latin-1", "replace").decode("latin-1")


def _money(inv, amount: float) -> str:
    return "%s%s" % (_latin(inv.currency or "$"), format(amount or 0, ",.2f"))


def build_pdf(inv: models.Invoice) -> bytes:
    from fpdf import FPDF

    order = inv.order
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Header band: brand mark (rounded tile + growth arrow) + INVOICE title.
    pdf.set_fill_color(*_INDIGO)
    pdf.rect(0, 0, 210, 34, style="F")
    pdf.set_draw_color(255, 255, 255)
    pdf.set_line_width(1.1)
    # growth-arrow glyph (mirrors the site's BrandMark)
    pdf.line(14, 22, 19, 16.5)
    pdf.line(19, 16.5, 22.5, 19.5)
    pdf.line(22.5, 19.5, 28, 12.5)
    pdf.line(24.5, 12.5, 28, 12.5)
    pdf.line(28, 12.5, 28, 16)
    pdf.set_fill_color(255, 255, 255)
    pdf.ellipse(13, 21, 2.4, 2.4, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 15)
    pdf.set_xy(33, 11)
    pdf.cell(80, 8, _latin("SMARNB"))
    pdf.set_font("helvetica", "", 8.5)
    pdf.set_xy(33, 18.5)
    pdf.cell(90, 5, _latin(config.ADMIN_NAME or "Muhammad Ali Raza"))
    pdf.set_font("helvetica", "B", 21)
    pdf.set_xy(150, 11)
    pdf.cell(46, 10, "INVOICE", align="R")

    # Meta block.
    pdf.set_text_color(*_INK)
    y = 44
    pdf.set_font("helvetica", "B", 11)
    pdf.set_xy(14, y)
    pdf.cell(90, 6, _latin(inv.number))
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*_MUTED)
    pdf.set_xy(14, y + 6)
    pdf.cell(90, 5, _latin("Issued %s  ·  Order %s" % (
        (inv.created_at or dt.datetime.utcnow()).strftime("%d %b %Y"),
        order.public_id)))
    # Status chip (text).
    paid = order.payment_status == "paid" or inv.status == "paid"
    pdf.set_xy(150, y)
    pdf.set_font("helvetica", "B", 11)
    if inv.status == "void":
        pdf.set_text_color(150, 45, 45)
        pdf.cell(46, 6, "VOID", align="R")
    elif paid:
        pdf.set_text_color(16, 130, 92)
        pdf.cell(46, 6, "PAID", align="R")
    else:
        pdf.set_text_color(*_INDIGO)
        pdf.cell(46, 6, "PAYMENT DUE", align="R")

    # Bill to.
    y += 18
    pdf.set_text_color(*_MUTED)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_xy(14, y)
    pdf.cell(90, 5, "BILLED TO")
    pdf.set_text_color(*_INK)
    pdf.set_font("helvetica", "", 10)
    pdf.set_xy(14, y + 5)
    pdf.cell(120, 6, _latin(order.customer_name or "Customer"))
    pdf.set_text_color(*_MUTED)
    pdf.set_font("helvetica", "", 9)
    pdf.set_xy(14, y + 11)
    pdf.cell(120, 5, _latin(order.customer_email or ""))

    # Lines table.
    y += 24
    pdf.set_xy(14, y)
    pdf.set_fill_color(244, 245, 252)
    pdf.set_text_color(*_MUTED)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(110, 8, "  ITEM", fill=True)
    pdf.cell(16, 8, "QTY", fill=True, align="C")
    pdf.cell(28, 8, "UNIT", fill=True, align="R")
    pdf.cell(28, 8, "AMOUNT  ", fill=True, align="R")
    pdf.ln(8)
    pdf.set_font("helvetica", "", 10)
    pdf.set_draw_color(*_LINE)
    pdf.set_line_width(0.2)
    for line in inv.lines:
        pdf.set_x(14)
        pdf.set_text_color(*_INK)
        pdf.cell(110, 9, _latin("  " + (line.get("title") or "")[:64]))
        pdf.set_text_color(*_MUTED)
        pdf.cell(16, 9, str(line.get("qty") or 1), align="C")
        pdf.cell(28, 9, _money(inv, line.get("unit")), align="R")
        pdf.set_text_color(*_INK)
        pdf.cell(28, 9, _money(inv, line.get("amount")) + "  ", align="R")
        pdf.ln(9)
        pdf.line(14, pdf.get_y(), 196, pdf.get_y())

    # Total.
    pdf.ln(3)
    pdf.set_x(14)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*_INK)
    pdf.cell(154, 10, "Total", align="R")
    pdf.set_text_color(*_INDIGO)
    pdf.cell(28, 10, _money(inv, inv.total) + "  ", align="R")
    pdf.ln(14)

    # Payment note + footer.
    footer = ""
    try:
        from . import emailer
        db = SessionLocal()
        try:
            footer = emailer.get_settings(db).get("invoice_footer") or ""
        finally:
            db.close()
    except Exception:
        pass
    if not paid and footer:
        pdf.set_x(14)
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*_MUTED)
        pdf.multi_cell(182, 5, _latin(footer))
        pdf.ln(4)
    pdf.set_x(14)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(*_MUTED)
    base = config.PUBLIC_BASE_URL or "https://smarnb.onrender.com"
    pdf.cell(182, 5, _latin("Track this order any time: %s (Track order → %s)"
                            % (base, order.public_id)))

    out = pdf.output()
    return bytes(out)


# --- Email -----------------------------------------------------------------------

def _email_html(inv: models.Invoice, paid: bool, footer: str) -> str:
    order = inv.order
    rows = "".join(
        "<tr>"
        "<td style='padding:9px 12px;border-bottom:1px solid #e8eaf3;color:#171723'>%s</td>"
        "<td style='padding:9px 12px;border-bottom:1px solid #e8eaf3;color:#646c82;text-align:center'>%s</td>"
        "<td style='padding:9px 12px;border-bottom:1px solid #e8eaf3;color:#171723;text-align:right'>%s%s</td>"
        "</tr>"
        % (line.get("title") or "", line.get("qty") or 1,
           inv.currency, format(line.get("amount") or 0, ",.2f"))
        for line in inv.lines
    )
    base = config.PUBLIC_BASE_URL or "https://smarnb.onrender.com"
    headline = ("Thanks — payment received!" if paid
                else "Your invoice from SMARNB")
    sub = (("Here's your receipt for order %s. The PDF is attached for your records."
            if paid else
            "Here's the invoice for order %s. The PDF is attached; payment details are below.")
           % order.public_id)
    return (
        "<div style='font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
        "max-width:560px;margin:0 auto;color:#171723'>"
        "<div style='background:#6366f1;border-radius:12px 12px 0 0;padding:18px 22px;color:#fff'>"
        "<div style='font-size:18px;font-weight:800'>SMARNB</div>"
        "<div style='font-size:12px;opacity:.85'>%s</div></div>"
        "<div style='border:1px solid #e8eaf3;border-top:0;border-radius:0 0 12px 12px;padding:22px'>"
        "<h2 style='margin:0 0 6px;font-size:19px'>%s</h2>"
        "<p style='margin:0 0 16px;color:#646c82;font-size:14px'>%s</p>"
        "<div style='font-size:13px;color:#646c82;margin-bottom:14px'>"
        "Invoice <b style='color:#171723'>%s</b> · %s</div>"
        "<table style='width:100%%;border-collapse:collapse;font-size:14px'>%s"
        "<tr><td style='padding:12px'></td>"
        "<td style='padding:12px;text-align:right;font-weight:700'>Total</td>"
        "<td style='padding:12px;text-align:right;font-weight:800;color:#6366f1'>%s%s</td></tr>"
        "</table>"
        "%s"
        "<a href='%s' style='display:inline-block;margin-top:16px;background:#6366f1;color:#fff;"
        "padding:10px 18px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px'>"
        "Track your order</a>"
        "<p style='margin:18px 0 0;color:#9aa1b5;font-size:12px'>%s</p>"
        "</div></div>"
        % (config.ADMIN_NAME or "", headline, sub, inv.number,
           ("PAID" if paid else "PAYMENT DUE"), rows,
           inv.currency, format(inv.total or 0, ",.2f"),
           ("" if paid else
            "<p style='margin:14px 0 0;color:#646c82;font-size:13px'>%s</p>" % footer),
           base, footer if paid else
           "Questions? Just reply to this email.")
    )


def send_invoice(db, order, *, background: bool = True) -> bool:
    """Email the invoice (PDF attached) to the customer, owner copy included.
    Used both for payment requests (unpaid) and receipts (paid)."""
    from . import emailer
    inv = ensure_invoice(db, order)
    paid = order.payment_status == "paid"
    footer = emailer.get_settings(db).get("invoice_footer") or ""
    try:
        pdf = build_pdf(inv)
    except Exception:
        pdf = b""
    subject = ("Receipt %s — thanks for your payment" if paid
               else "Invoice %s from SMARNB") % inv.number
    ok = emailer.send(
        db, order.customer_email or "", subject,
        _email_html(inv, paid, footer),
        attachments=([("%s.pdf" % inv.number, pdf, "application/pdf")] if pdf else None),
        kind="invoice", bcc_owner=True, background=background)
    if ok:
        inv.sent_at = models.utcnow()
        if inv.status == "draft":
            inv.status = "sent"
        db.commit()
    return ok


def on_order_paid(db, order, *, background: bool = True):
    """The single hook the payment paths call after an order flips to paid:
    invoice → paid, receipt emailed, stock consumed. Never raises."""
    try:
        inv = ensure_invoice(db, order)
        if inv.status != "void":
            inv.status = "paid"
            inv.paid_at = models.utcnow()
            db.commit()
        send_invoice(db, order, background=background)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    try:
        from . import inventory
        inventory.consume_for_order(db, order)
    except Exception:
        pass
