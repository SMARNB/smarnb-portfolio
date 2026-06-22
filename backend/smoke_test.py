"""Quick end-to-end API check. Run while the server is up: python smoke_test.py"""
import json
import os
import random
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:" + os.environ.get("PORT", "8000")


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


# wait for the server
for _ in range(40):
    try:
        if call("GET", "/api/health")[0] == 200:
            break
    except Exception:
        pass
    time.sleep(0.5)

email = "client%d@test.com" % random.randint(1000, 9999)
s, reg = call("POST", "/api/auth/register",
              {"email": email, "password": "secret123", "name": "Test Client", "whatsapp": "15551234567"})
print("register            ", s, "->", reg.get("user", {}).get("email"))
ctoken = reg["access_token"]

s, order = call("POST", "/api/orders", {
    "customer_name": "Test Client", "customer_email": email, "customer_whatsapp": "15551234567",
    "notes": "Please make it dark mode",
    "items": [
        {"service": "Full-Stack SaaS Dashboards in Python", "tier": "Standard", "price": 450, "qty": 1},
        {"service": "Figma UI/UX", "tier": "Starter", "price": 90, "qty": 2},
    ],
}, token=ctoken)
pid = order["public_id"]
print("create order        ", s, "->", pid, "total", order.get("total"), order.get("status"))

s, mine = call("GET", "/api/orders/mine", token=ctoken)
print("my orders           ", s, "->", len(mine), "order(s)")

s, adm = call("POST", "/api/auth/login", {"email": "shahjee975@gmail.com", "password": "admin12345"})
print("admin login         ", s, "->", adm.get("user", {}).get("role"))
atoken = adm["access_token"]

s, allo = call("GET", "/api/admin/orders", token=atoken)
print("admin list orders   ", s, "->", len(allo), "order(s)")

s, patched = call("PATCH", "/api/admin/orders/" + pid,
                  {"status": "in_progress", "progress": 45}, token=atoken)
print("admin patch         ", s, "->", patched.get("status"), patched.get("progress"), "%")

s, upd = call("POST", "/api/admin/orders/" + pid + "/updates",
              {"message": "Wireframes done, building the API now.", "progress": 60}, token=atoken)
print("admin add update    ", s, "->", upd.get("progress"), "% /", len(upd.get("updates", [])), "updates")

s, track = call("GET", "/api/orders/" + pid)
print("public track        ", s, "->", track.get("status_label"), track.get("progress"), "%")

s, stats = call("GET", "/api/admin/stats", token=atoken)
print("admin stats         ", s, "->", stats)

s, denied = call("GET", "/api/admin/orders", token=ctoken)
print("client->admin (403?)", s)
