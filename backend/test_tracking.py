"""End-to-end checks for automatic project tracking: every order is seeded with a
milestone pipeline, ticking milestones auto-derives status + progress + a client
update, payment auto-advances the tracker, and custom milestones work.

Run:  .venv/Scripts/python test_tracking.py
"""
import os
import tempfile

# Throwaway DB BEFORE importing the app (config reads env at import).
_DB = os.path.join(tempfile.gettempdir(), "portfolio_track_test.db")
if os.path.exists(_DB):
    os.remove(_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _DB
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "test-admin-123"
# Neutralize any real email creds from backend/.env — config's dotenv setdefault
# would refill popped keys, so set them to empty instead.
for _var in ("SENDGRID_API_KEY", "BREVO_API_KEY", "SMTP_HOST", "EMAIL_FROM"):
    os.environ[_var] = ""

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app import seo as _seo  # noqa: E402

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


with TestClient(app) as c:
    r = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-admin-123"})
    tok = r.json()["access_token"]
    AH = {"Authorization": "Bearer " + tok}

    print("== New order is auto-seeded with a pipeline ==")
    r = c.post("/api/orders", json={"customer_name": "Track Client", "customer_email": "track@example.com",
                                    "items": [{"service": "App", "tier": "Standard", "price": 500, "qty": 1}]})
    o = r.json()
    pid = o["public_id"]
    check("order created", r.status_code == 200)
    check("4 milestones seeded", len(o["milestones"]) == 4)
    check("starts at received / 0%", o["status"] == "received" and o["progress"] == 0)
    check("next_step is the first milestone", o["next_step"] == "Requirements confirmed")

    print("== Ticking a milestone auto-derives status + progress + a client update ==")
    confirmed = [m for m in o["milestones"] if m["status_key"] == "confirmed"][0]
    r = c.patch("/api/admin/milestones/%d" % confirmed["id"], headers=AH, json={"done": True})
    o = r.json()
    check("status auto-advanced to confirmed", o["status"] == "confirmed")
    check("progress auto-set to 25%", o["progress"] == 25)
    check("a client-visible update was logged", any("Requirements confirmed" in u["message"] for u in o["updates"]))
    check("next_step moved on", o["next_step"] == "Build in progress")

    print("== Completing all milestones -> delivered / 100% ==")
    for m in o["milestones"]:
        if not m["done"]:
            o = c.patch("/api/admin/milestones/%d" % m["id"], headers=AH, json={"done": True}).json()
    check("all done → delivered", o["status"] == "delivered")
    check("progress 100%", o["progress"] == 100)
    check("no next step left", o["next_step"] is None)

    print("== Un-ticking a milestone walks the tracker back ==")
    delivered = [m for m in o["milestones"] if m["status_key"] == "delivered"][0]
    o = c.patch("/api/admin/milestones/%d" % delivered["id"], headers=AH, json={"done": False}).json()
    check("reopening 'delivered' drops status to in_review", o["status"] == "in_review")
    check("progress recomputed to 75%", o["progress"] == 75)

    print("== Custom milestones contribute to progress ==")
    o = c.post("/api/admin/orders/%s/milestones" % pid, headers=AH, json={"title": "Handover call"}).json()
    check("custom milestone added (now 5 steps)", len(o["milestones"]) == 5)
    check("progress recomputed for 3/5 done", o["progress"] == 60)
    custom = [m for m in o["milestones"] if m["title"] == "Handover call"][0]
    o = c.delete("/api/admin/milestones/%d" % custom["id"], headers=AH).json()
    check("custom milestone removable", len(o["milestones"]) == 4)

    print("== Payment auto-advances the tracker ==")
    r = c.post("/api/orders", json={"customer_name": "Pay Client", "customer_email": "pay@example.com",
                                    "items": [{"service": "App", "tier": "Basic", "price": 100, "qty": 1}]})
    pid2 = r.json()["public_id"]
    check("fresh order is received", r.json()["status"] == "received")
    o2 = c.patch("/api/admin/orders/%s" % pid2, headers=AH, json={"payment_status": "paid"}).json()
    check("paying auto-completes the 'confirmed' milestone",
          [m for m in o2["milestones"] if m["status_key"] == "confirmed"][0]["done"] is True)
    check("paying auto-advanced status to confirmed", o2["status"] == "confirmed")

    print("== Cancel is respected (milestones don't override it) ==")
    o2 = c.patch("/api/admin/orders/%s" % pid2, headers=AH, json={"status": "cancelled"}).json()
    check("order cancelled", o2["status"] == "cancelled")
    check("cancelled order has no next step", o2["next_step"] is None)

    print("== Client sees the milestones on their own order ==")
    reg = c.post("/api/auth/register", json={"email": "track@example.com", "password": "secret123"}).json()
    CH = {"Authorization": "Bearer " + reg["access_token"]}
    mine = c.get("/api/orders/mine", headers=CH).json()
    mine_o = [x for x in mine if x["public_id"] == pid][0]
    check("client order exposes milestones", len(mine_o["milestones"]) == 4)
    check("client order exposes next_step", "next_step" in mine_o)

print("\n==== RESULT: %d passed, %d failed ====" % (ok, fail))
if os.path.exists(_DB):
    try:
        os.remove(_DB)
    except Exception:
        pass
raise SystemExit(1 if fail else 0)
