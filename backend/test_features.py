"""Tests the new features: services CRUD, deliverable gating, encryption at rest."""
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:" + os.environ.get("PORT", "8100")


def call(method, path, data=None, token=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "null")


for _ in range(40):
    try:
        if call("GET", "/api/health")[0] == 200:
            break
    except Exception:
        pass
    time.sleep(0.5)

_, adm = call("POST", "/api/auth/login", {"email": "shahjee975@gmail.com", "password": "admin12345"})
at = adm["access_token"]

print("== Services CRUD ==")
_, svc = call("POST", "/api/admin/services", {
    "title": "Discord Bot Development", "category": "Automation", "icon": "bot",
    "short": "Custom Discord bots.", "tags": ["Python", "Discord"],
    "packages": [{"tier": "Basic", "price": 60, "delivery": "3 days", "revisions": 1,
                  "summary": "A simple bot", "features": ["5 commands"]}],
}, at)
print("  created service:", svc.get("slug"), "|", svc.get("title"))
_, pub = call("GET", "/api/services")
print("  public /api/services:", len(pub), "active | includes new:",
      any(x["slug"] == svc["slug"] for x in pub))

print("== Deliverable gating ==")
em = "feat%d@mail.com" % int(time.time())
_, reg = call("POST", "/api/auth/register", {"email": em, "password": "secret123", "name": "Feature Client"})
ct = reg["access_token"]
_, o = call("POST", "/api/orders",
            {"customer_name": "Feature Client", "customer_email": em,
             "items": [{"service": "X", "tier": "Standard", "price": 200, "qty": 1}]}, ct)
pid = o["public_id"]
call("POST", "/api/admin/orders/%s/deliverables" % pid,
     {"title": "Final design", "preview_url": "https://ex.com/preview.png",
      "final_url": "https://ex.com/final.zip", "note": "watermarked"}, at)
_, mine = call("GET", "/api/orders/mine", None, ct)
d0 = mine[0]["deliverables"][0]
print("  before pay -> preview:", bool(d0["preview_url"]), "| final:", d0["final_url"], "| locked:", d0["locked"])
call("PATCH", "/api/admin/orders/%s" % pid, {"payment_status": "paid"}, at)
_, mine2 = call("GET", "/api/orders/mine", None, ct)
d1 = mine2[0]["deliverables"][0]
print("  after pay  -> preview:", bool(d1["preview_url"]), "| final:", d1["final_url"], "| locked:", d1["locked"])

print("== Encryption at rest (raw DB) ==")
dbpath = os.path.join(os.path.dirname(__file__), "portfolio.db")
con = sqlite3.connect(dbpath)
cur = con.cursor()
cur.execute("SELECT email, email_bidx FROM users LIMIT 1")
raw_email, bidx = cur.fetchone()
cur.execute("SELECT customer_name, customer_email FROM orders LIMIT 1")
row = cur.fetchone()
con.close()
print("  users.email in DB has NO '@' (encrypted):", "@" not in raw_email, "| sample:", raw_email[:20] + "...")
print("  email_bidx is a hash:", len(bidx) == 64)
if row:
    print("  orders.customer_email encrypted:", "@" not in (row[1] or ""))
