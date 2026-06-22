"""Seed a demo client + an in-progress order (handy for demos/screenshots).
Run with the server up:  python seed_demo.py   (PORT env optional, default 8100)
Login afterwards at /app.html with  demo@clientmail.com / secret123
"""
import json
import os
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


s, reg = call("POST", "/api/auth/register",
              {"email": "demo@clientmail.com", "password": "secret123", "name": "Demo Client"})
if s != 200:
    s, reg = call("POST", "/api/auth/login", {"email": "demo@clientmail.com", "password": "secret123"})
tok = reg["access_token"]

_, o = call("POST", "/api/orders", {
    "customer_name": "Demo Client", "customer_email": "demo@clientmail.com",
    "payment_method": "Credit / Debit card (Stripe)",
    "items": [
        {"service": "Full-Stack SaaS Dashboards in Python", "tier": "Standard", "price": 450, "qty": 1},
        {"service": "Brand & Logo Design", "tier": "Starter", "price": 50, "qty": 1},
    ],
}, tok)
pid = o["public_id"]

_, adm = call("POST", "/api/auth/login", {"email": "shahjee975@gmail.com", "password": "admin12345"})
at = adm["access_token"]
call("PATCH", "/api/admin/orders/" + pid,
     {"status": "in_progress", "progress": 65, "due_date": "2026-07-10"}, at)
call("POST", "/api/admin/orders/" + pid + "/updates",
     {"message": "Design approved — building the dashboard now.", "progress": 65}, at)

print("demo ready:", pid, "| login at /app.html with demo@clientmail.com / secret123")
