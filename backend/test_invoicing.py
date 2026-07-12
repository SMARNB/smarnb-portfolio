"""End-to-end checks for the billing stack: emailer (inert until configured, DB
sender overrides), invoices (draft on order, sequential numbers, paid → receipt
emailed w/ PDF + owner copy), public/admin PDF endpoints, inventory (CRUD, moves
ledger, paid-order consumption, low-stock), promo campaigns + unsubscribe.

Run:  .venv/Scripts/python test_invoicing.py
"""
import os
import tempfile

# Throwaway DB BEFORE importing the app (config reads env at import). Also make
# absolutely sure no real email transport is configured for the test run.
_DB = os.path.join(tempfile.gettempdir(), "portfolio_billing_test.db")
if os.path.exists(_DB):
    os.remove(_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _DB
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "test-admin-123"
os.environ["OWNER_EMAIL"] = "owner@example.com"
# Set to empty (not pop) — config's dotenv setdefault would refill popped keys
# from a real backend/.env.
for var in ("SENDGRID_API_KEY", "BREVO_API_KEY", "SMTP_HOST", "EMAIL_FROM"):
    os.environ[var] = ""

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app import emailer, seo as _seo  # noqa: E402

_seo.STATIC_DIR = None   # don't let the app-boot sitemap mirror touch the dev dist

ok = 0
fail = 0


def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
        print("  [PASS]", name)
    else:
        fail += 1
        print("  [FAIL]", name)


ORDER = {"customer_name": "Bill Client", "customer_email": "bill@example.com",
         "items": [{"service": "AI Chatbot Integration", "tier": "Standard",
                    "price": 350, "qty": 2}]}

with TestClient(app) as c:
    r = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-admin-123"})
    tok = r.json()["access_token"]
    AH = {"Authorization": "Bearer " + tok}

    print("== Email is INERT until configured ==")
    st = c.get("/api/admin/email/settings", headers=AH).json()
    check("settings endpoint admin-gated", c.get("/api/admin/email/settings").status_code == 401)
    check("email disabled with no transport", st["enabled"] is False and st["transport"] == "none")
    check("test-send refuses while off", c.post("/api/admin/email/test", headers=AH).status_code == 400)
    check("campaign refuses while off",
          c.post("/api/admin/email/campaign", headers=AH,
                 json={"subject": "Hi", "body_md": "Hello"}).status_code == 400)

    print("== Order creation snapshots a draft invoice ==")
    o1 = c.post("/api/orders", json=ORDER).json()
    o2 = c.post("/api/orders", json=dict(ORDER, customer_email="second@example.com")).json()
    check("order carries invoice info", bool(o1.get("invoice")))
    n1, n2 = o1["invoice"]["number"], o2["invoice"]["number"]
    check("invoice numbers sequential (INV-YYYY-NNNN)",
          n1.split("-")[-1] == "0001" and n2.split("-")[-1] == "0002" and n1.startswith("INV-"))
    check("invoice starts as draft", o1["invoice"]["status"] == "draft")

    print("== Public + admin invoice PDFs ==")
    r = c.get("/api/orders/%s/invoice.pdf" % o1["public_id"])
    check("public PDF by order id", r.status_code == 200 and r.content[:4] == b"%PDF")
    check("PDF content-type", r.headers["content-type"] == "application/pdf")
    check("wrong order id -> 404", c.get("/api/orders/ALR-NOPE99/invoice.pdf").status_code == 404)
    r = c.get("/api/admin/invoices/%s.pdf" % n1, headers=AH)
    check("admin PDF by number", r.status_code == 200 and r.content[:4] == b"%PDF")
    check("admin PDF gated", c.get("/api/admin/invoices/%s.pdf" % n1).status_code == 401)
    lst = c.get("/api/admin/invoices", headers=AH).json()["invoices"]
    check("admin list shows both invoices", len(lst) == 2)

    print("== Capture transport: sender settings + test send ==")
    sent = []
    emailer._test_capture = sent.append
    st = c.get("/api/admin/email/settings", headers=AH).json()
    check("capture transport reports enabled", st["enabled"] is True)
    r = c.put("/api/admin/email/settings", headers=AH,
              json={"from_name": "SMARNB Studio", "from_email": "hello@smarnb.dev",
                    "reply_to": "shahjee975@gmail.com"})
    check("sender settings saved (dashboard override)",
          r.json()["settings"]["from_email"] == "hello@smarnb.dev")
    r = c.post("/api/admin/email/test", headers=AH)
    check("test email sent to owner", r.status_code == 200 and sent[-1]["to"] == "owner@example.com")
    check("test email uses overridden sender", sent[-1]["from_email"] == "hello@smarnb.dev"
          and sent[-1]["from_name"] == "SMARNB Studio")

    print("== Inventory: CRUD + ledger ==")
    r = c.post("/api/admin/inventory", headers=AH,
               json={"sku": "AI-CHATBOT", "name": "AI Chatbot Integration",
                     "kind": "service", "stock": 5, "low_stock_threshold": 2})
    item = r.json()
    check("item created tracked at 5", r.status_code == 200 and item["stock"] == 5)
    check("duplicate sku rejected",
          c.post("/api/admin/inventory", headers=AH,
                 json={"sku": "AI-CHATBOT", "name": "x"}).status_code == 400)
    r = c.post("/api/admin/inventory/%d/adjust" % item["id"], headers=AH,
               json={"delta": 3, "reason": "restock", "note": "supplier"})
    check("manual restock 5 -> 8", r.json()["stock"] == 8)
    check("inventory gated", c.get("/api/admin/inventory").status_code == 401)

    print("== Paid order: receipt email + stock consumption ==")
    sent.clear()
    r = c.patch("/api/admin/orders/%s" % o1["public_id"], headers=AH,
                json={"payment_status": "paid"})
    o1 = r.json()
    check("order marked paid", o1["payment_status"] == "paid")
    check("invoice flipped to paid", o1["invoice"]["status"] == "paid")
    inv_mails = [m for m in sent if m["kind"] == "invoice"]
    check("receipt emailed to the customer",
          len(inv_mails) == 1 and inv_mails[0]["to"] == "bill@example.com")
    check("owner gets a copy (bcc)", inv_mails[0]["bcc"] == "owner@example.com")
    att = (inv_mails[0]["attachments"] or [])
    check("PDF attached to the receipt",
          len(att) == 1 and att[0][0].endswith(".pdf") and att[0][1][:4] == b"%PDF")
    it = c.get("/api/admin/inventory", headers=AH).json()["items"][0]
    check("stock consumed by qty (8 -> 6)", it["stock"] == 6)
    moves = c.get("/api/admin/inventory/%d/moves" % it["id"], headers=AH).json()["moves"]
    check("ledger recorded the order consumption",
          any(m["reason"] == "order_paid" and m["delta"] == -2 and m["ref"] == o1["public_id"]
              for m in moves))

    print("== Low stock alert fires at the threshold ==")
    sent.clear()
    c.post("/api/admin/inventory/%d/adjust" % it["id"], headers=AH,
           json={"delta": -3, "reason": "correction"})   # 6 -> 3
    o3 = c.post("/api/orders", json=dict(ORDER, customer_email="third@example.com")).json()
    c.patch("/api/admin/orders/%s" % o3["public_id"], headers=AH, json={"payment_status": "paid"})
    it = c.get("/api/admin/inventory", headers=AH).json()["items"][0]
    check("stock 3 -> 1 and flagged low", it["stock"] == 1 and it["low"] is True)
    check("low-stock email sent to owner",
          any(m["to"] == "owner@example.com" and "Low stock" in m["subject"] for m in sent))

    print("== Resend + void ==")
    sent.clear()
    r = c.post("/api/admin/orders/%s/invoice/send" % o2["public_id"], headers=AH)
    check("unpaid invoice sent as payment request",
          r.status_code == 200 and sent and sent[-1]["to"] == "second@example.com")
    check("invoice now marked sent", r.json()["invoice"]["status"] == "sent")
    r = c.patch("/api/admin/invoices/%s" % n2, headers=AH, json={"status": "void"})
    check("invoice voided", r.json()["status"] == "void")
    check("void invoice hides the public PDF",
          c.get("/api/orders/%s/invoice.pdf" % o2["public_id"]).status_code == 404)

    print("== Invoice email carries the work scope + the client's brief ==")
    sent.clear()
    o4 = c.post("/api/orders", json={
        "customer_name": "Zara Khan", "customer_email": "zara@example.com",
        "notes": "Brand: Zaralux. Need product catalog, cart, Stripe checkout and an admin panel.",
        "items": [{"service": "E-commerce Store", "tier": "Premium", "price": 1200, "qty": 1,
                   "summary": "A full online store, ready to launch.",
                   "delivery": "21 days",
                   "scope": ["Product catalog & cart", "Stripe checkout", "Admin dashboard"]}],
    }).json()
    r = c.post("/api/admin/orders/%s/invoice/send" % o4["public_id"], headers=AH)
    html = sent[-1]["html"] if sent else ""
    check("scope section present", "What you're getting" in html)
    check("package summary rendered", "A full online store, ready to launch." in html)
    check("scope bullets rendered",
          "Stripe checkout" in html and "Admin dashboard" in html)
    check("client brief echoed back",
          "Your project brief" in html and "Zaralux" in html)
    check("greets the client by name", "Hi Zara Khan," in html)
    check("html-escapes the brief (no raw injection)",
          "<script" not in html.lower())

    print("== Promo campaign + unsubscribe ==")
    c.post("/api/auth/register", json={"email": "clienta@example.com", "password": "pass12345",
                                       "name": "Client A"})
    c.post("/api/auth/register", json={"email": "clientb@example.com", "password": "pass12345",
                                       "name": "Client B"})
    sent.clear()
    r = c.post("/api/admin/email/campaign", headers=AH,
               json={"subject": "New service!", "body_md": "# Hello\nBig news.", "test_only": True})
    check("test campaign goes only to the owner",
          r.json()["sent"] == 1 and sent[-1]["to"] == "owner@example.com")
    sent.clear()
    r = c.post("/api/admin/email/campaign", headers=AH,
               json={"subject": "New service!", "body_md": "# Hello\nBig news."})
    res = r.json()
    check("campaign sent to both clients", res["sent"] == 2 and len(sent) == 2)
    check("campaign html carries an unsubscribe link",
          all("/api/email/unsubscribe?u=" in m["html"] for m in sent))
    # Pull client A's real unsubscribe link out of the captured email.
    import re
    m = re.search(r"/api/email/unsubscribe\?u=(\d+)&t=([0-9a-f]+)",
                  [x for x in sent if x["to"] == "clienta@example.com"][0]["html"])
    check("bad unsubscribe token rejected",
          c.get("/api/email/unsubscribe?u=%s&t=deadbeef" % m.group(1)).status_code == 400)
    r = c.get("/api/email/unsubscribe?u=%s&t=%s" % (m.group(1), m.group(2)))
    check("valid unsubscribe accepted", r.status_code == 200 and "unsubscribed" in r.text.lower())
    sent.clear()
    res = c.post("/api/admin/email/campaign", headers=AH,
                 json={"subject": "Again!", "body_md": "More news."}).json()
    check("opted-out client skipped next campaign",
          res["sent"] == 1 and sent[0]["to"] == "clientb@example.com")

    print("== Email log recorded the traffic ==")
    log = c.get("/api/admin/email/log", headers=AH).json()["log"]
    check("log has invoice + promo + test rows",
          {"invoice", "promo", "test"} <= {row["kind"] for row in log})
    check("log rows marked ok", all(row["ok"] for row in log))

    emailer._test_capture = None

print("\n==== RESULT: %d passed, %d failed ====" % (ok, fail))
raise SystemExit(1 if fail else 0)
