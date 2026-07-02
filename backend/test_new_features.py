"""End-to-end checks for the new features: services import + managed catalog,
testimonials submit/moderate, and chat (bot replies, order-via-chat, uploads,
admin inbox). Runs against a throwaway SQLite DB via FastAPI's TestClient.

Run:  .venv/Scripts/python test_new_features.py
"""
import base64
import hashlib as _hashlib
import hmac as _hmac
import os
import tempfile

# Point at a throwaway DB BEFORE importing the app (config reads env at import).
_DB = os.path.join(tempfile.gettempdir(), "portfolio_test.db")
if os.path.exists(_DB):
    os.remove(_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _DB
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "test-admin-123"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app import seo as _seo  # noqa: E402

_seo.STATIC_DIR = None   # don't let the app-boot sitemap mirror touch the dev dist

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

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


BUILTINS = [
    {"title": "Full-Stack SaaS Dashboards in Python", "category": "Development", "icon": "code",
     "short": "Dashboards.", "tags": ["Python"], "deliverables": ["Code"], "slug": "saas-dashboard",
     "packages": [{"tier": "Starter", "price": 150, "delivery": "5 days", "revisions": 1,
                   "summary": "Single page.", "features": ["1 page"], "popular": False},
                  {"tier": "Standard", "price": 450, "delivery": "10 days", "revisions": 3,
                   "summary": "Multi page.", "features": ["5 pages"], "popular": True}]},
    {"title": "Brand & Logo Design", "category": "Design", "icon": "pen", "short": "Logos.",
     "tags": ["Logo"], "deliverables": ["Logo"], "slug": "brand-identity",
     "packages": [{"tier": "Starter", "price": 50, "delivery": "2 days", "revisions": 2,
                   "summary": "A logo.", "features": ["1 logo"], "popular": False}]},
]


with TestClient(app) as c:
    print("== Auth ==")
    r = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-admin-123"})
    check("admin login", r.status_code == 200)
    tok = r.json()["access_token"]
    AH = {"Authorization": "Bearer " + tok}

    print("== Services: import + managed catalog ==")
    r = c.get("/api/services")
    check("public catalog shape", r.status_code == 200 and "managed" in r.json())
    check("not managed before import", r.json()["managed"] is False)

    r = c.post("/api/admin/services/import", headers=AH, json={"services": BUILTINS})
    check("import created built-ins", r.status_code == 200 and r.json()["created"] == 2)

    r = c.get("/api/services")
    check("managed after import", r.json()["managed"] is True)
    check("catalog has 2 services", len(r.json()["services"]) == 2)
    svc = [s for s in r.json()["services"] if s["slug"] == "saas-dashboard"][0]
    check("deliverables preserved", svc["deliverables"] == ["Code"])

    # re-import is idempotent (skips existing)
    r = c.post("/api/admin/services/import", headers=AH, json={"services": BUILTINS})
    check("re-import idempotent", r.json()["created"] == 0)

    # hide one built-in → drops from public catalog
    sid = [s for s in c.get("/api/admin/services", headers=AH).json() if s["slug"] == "brand-identity"][0]["id"]
    body = dict(BUILTINS[1]); body["active"] = False
    r = c.patch("/api/admin/services/%d" % sid, headers=AH, json=body)
    check("hide service", r.status_code == 200)
    check("hidden not in public catalog", len(c.get("/api/services").json()["services"]) == 1)

    print("== Testimonials ==")
    r = c.post("/api/testimonials", json={"name": "Jane Doe", "role": "CTO", "location": "NYC",
                                          "rating": 5, "text": "Fantastic work, super fast!", "company": ""})
    check("submit testimonial", r.status_code == 200 and r.json()["ok"])
    check("not shown until approved", c.get("/api/testimonials").json() == [])
    pend = c.get("/api/admin/testimonials", headers=AH).json()
    check("admin sees pending", len(pend) == 1 and pend[0]["status"] == "pending")
    tid = pend[0]["id"]
    c.patch("/api/admin/testimonials/%d" % tid, headers=AH, json={"status": "approved"})
    pub = c.get("/api/testimonials").json()
    check("approved now public", len(pub) == 1 and pub[0]["name"] == "Jane Doe")
    # honeypot
    r = c.post("/api/testimonials", json={"name": "Bot", "rating": 5, "text": "spam spam spam!!", "company": "x"})
    check("honeypot accepted-but-not-saved", r.status_code == 200 and len(c.get("/api/admin/testimonials", headers=AH).json()) == 1)

    print("== Chat: bot + order flow ==")
    r = c.post("/api/chat/start", json={})
    th = r.json()
    cid, secret = th["public_id"], th["secret"]
    SH = {"X-Chat-Secret": secret}
    check("start returns greeting + secret", bool(secret) and len(th["messages"]) == 1)

    r = c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "what services do you offer?"})
    txt = " ".join(m["body"] for m in r.json()["messages"])
    check("bot lists services", "SaaS" in txt or "Logo" in txt)

    # order flow
    c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "I want to order"})
    c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "Full-Stack SaaS Dashboards in Python"})
    c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "Standard"})
    c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "I need a metrics dashboard with auth"})
    c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "Test Client"})
    c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "client@example.com"})
    r = c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "yes"})
    alltxt = " ".join(m["body"] for m in r.json()["messages"])
    check("order created via chat (ALR- id)", "ALR-" in alltxt)
    check("order shows in admin orders", any("client@example.com" == o["customer_email"]
          for o in c.get("/api/admin/orders", headers=AH).json()))

    print("== Chat: file uploads ==")
    r = c.post("/api/chat/%s/upload" % cid, headers=SH,
               files={"file": ("shot.png", PNG_1x1, "image/png")})
    check("valid PNG accepted", r.status_code == 200)
    att = [m for m in r.json()["messages"] if m.get("attachment")][-1]["attachment"]
    check("attachment recorded", att["content_type"] == "image/png")
    # serve it back with the secret
    r = c.get("/api/chat/%s/attachments/%d?s=%s" % (cid, att["id"], secret))
    check("attachment served to participant", r.status_code == 200 and r.content[:4] == b"\x89PNG")
    # without secret → blocked
    check("attachment blocked w/o secret", c.get("/api/chat/%s/attachments/%d" % (cid, att["id"])).status_code == 403)
    # disguised file (txt bytes, .png name) → rejected by magic-byte check
    r = c.post("/api/chat/%s/upload" % cid, headers=SH,
               files={"file": ("evil.png", b"<script>alert(1)</script>", "image/png")})
    check("fake image rejected (magic bytes)", r.status_code == 415)
    # svg explicitly rejected
    r = c.post("/api/chat/%s/upload" % cid, headers=SH,
               files={"file": ("x.svg", b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", "image/svg+xml")})
    check("SVG rejected", r.status_code == 415)

    print("== Chat: admin inbox + live takeover ==")
    convs = c.get("/api/admin/chat/conversations", headers=AH).json()
    check("admin sees conversation", len(convs) == 1)
    r = c.post("/api/admin/chat/conversations/%s/messages" % cid, headers=AH,
               json={"body": "Hi, this is Ali — happy to help!", "let_bot_resume": False})
    check("dev reply ok + takeover", r.status_code == 200 and r.json()["human_takeover"] is True)
    # after takeover, the bot should NOT auto-reply
    before = len(c.get("/api/chat/%s" % cid, headers=SH).json()["messages"])
    c.post("/api/chat/%s/messages" % cid, headers=SH, json={"body": "thanks!"})
    after = len(c.get("/api/chat/%s" % cid, headers=SH).json()["messages"])
    check("no bot auto-reply during takeover", after == before + 1)
    # auth: anonymous cannot read admin inbox
    check("admin inbox requires auth", c.get("/api/admin/chat/conversations").status_code == 401)

    print("== Chat: admin attachment previews ==")
    # admin can fetch any attachment's bytes (no per-thread secret needed) — this
    # powers the Inbox image/PDF previews.
    r = c.get("/api/admin/chat/attachments/%d" % att["id"], headers=AH)
    check("admin attachment served", r.status_code == 200 and r.content[:4] == b"\x89PNG")
    check("admin attachment inline disposition",
          r.headers.get("content-disposition", "").startswith("inline"))
    check("admin attachment content-type", r.headers.get("content-type") == "image/png")
    # the route is admin-gated — anonymous is rejected
    check("admin attachment requires auth",
          c.get("/api/admin/chat/attachments/%d" % att["id"]).status_code == 401)
    # unknown id → 404 (not a 500)
    check("admin attachment 404 for unknown id",
          c.get("/api/admin/chat/attachments/999999", headers=AH).status_code == 404)

    print("== Chat: smarter bot + curated learning ==")
    # common-language question answered from the built-in knowledge base
    r = c.post("/api/chat/start", json={})
    cid2, sec2 = r.json()["public_id"], r.json()["secret"]
    SH2 = {"X-Chat-Secret": sec2}
    msgs = c.post("/api/chat/%s/messages" % cid2, headers=SH2,
                  json={"body": "how do i pay you?"}).json()["messages"]
    last = msgs[-1]["body"].lower()
    check("bot answers a common-language question", "payment" in last or "raast" in last)

    # intent priority: a service/pricing question must NOT get hijacked by a
    # small-talk fuzzy match. Regression: "...how much for a dashboard" used to hit
    # the "how are you" reply because how/do/you appear scattered in it.
    blob = " ".join(m["body"] for m in c.post(
        "/api/chat/%s/messages" % cid2, headers=SH2,
        json={"body": "what services do you offer and how much for a dashboard?"}
    ).json()["messages"]).lower()
    check("service+price question lists services (not small talk)",
          ("saas" in blob or "logo" in blob or "from $" in blob) and "doing great" not in blob)

    # a purely-social opener yields when a real business ask rides along
    blob = " ".join(m["body"] for m in c.post(
        "/api/chat/%s/messages" % cid2, headers=SH2,
        json={"body": "hey, how are you? what is your pricing?"}
    ).json()["messages"]).lower()
    check("social opener yields to a pricing ask",
          "doing great" not in blob and ("saas" in blob or "logo" in blob or "package" in blob or "from $" in blob))

    # plain small talk still gets the friendly answer (not over-corrected)
    last = c.post("/api/chat/%s/messages" % cid2, headers=SH2,
                  json={"body": "how are you?"}).json()["messages"][-1]["body"].lower()
    check("plain small talk still answered", "doing great" in last or "help with your project" in last)

    # an unknown question is flagged unanswered + logged for the developer
    c.post("/api/chat/%s/messages" % cid2, headers=SH2,
           json={"body": "do you sell vintage typewriters from 1920"})
    unans = c.get("/api/admin/chat/unanswered", headers=AH).json()
    check("unanswered question logged", any("typewriter" in u["question"].lower() for u in unans))

    # admin teaches the bot an answer (curated knowledge)
    kn = c.post("/api/admin/chat/knowledge", headers=AH,
                json={"question": "do you sell typewriters",
                      "answer": "I focus on software, not typewriters — but I can build you a typewriter-themed app!",
                      "keywords": "typewriter, typewriters"}).json()
    check("knowledge created", "id" in kn)

    # the bot now answers from the taught knowledge (typo-tolerant)
    msgs = c.post("/api/chat/%s/messages" % cid2, headers=SH2,
                  json={"body": "do you sel typewritters"}).json()["messages"]
    check("bot answers from taught knowledge", "typewriter" in msgs[-1]["body"].lower())

    # the hit counter incremented
    klist = c.get("/api/admin/chat/knowledge", headers=AH).json()
    check("knowledge hit recorded", any(k["id"] == kn["id"] and k["hits"] >= 1 for k in klist))

    # knowledge base is admin-only
    check("knowledge requires auth", c.get("/api/admin/chat/knowledge").status_code == 401)

    # cleanup
    check("knowledge deletable",
          c.delete("/api/admin/chat/knowledge/%s" % kn["id"], headers=AH).status_code == 200)

    print("== Chat: contact intent + owner ping ==")
    # "contact you" now gives contact details, not the human-handoff escape
    r = c.post("/api/chat/start", json={})
    cid3, sec3 = r.json()["public_id"], r.json()["secret"]
    SH3 = {"X-Chat-Secret": sec3}
    last = c.post("/api/chat/%s/messages" % cid3, headers=SH3,
                  json={"body": "how can i contact you?"}).json()["messages"][-1]["body"].lower()
    check("contact question gives details (not handoff)", "email" in last or "whatsapp" in last)
    # asking for a human flags needs_human (which is what triggers the owner ping)
    th = c.post("/api/chat/%s/messages" % cid3, headers=SH3,
                json={"body": "i want to talk to a human"}).json()
    check("human request flags needs_human", th["needs_human"] is True)
    # owner ping is a no-op (returns False) until a sender is configured
    from app import notify  # noqa: E402
    check("owner ping off by default", notify.notify_owner("test") is False)

    print("== WhatsApp bridge (inert by default; two-way when configured) ==")
    from app import config as appcfg, whatsapp  # noqa: E402

    # Inert by default: GET verification rejects everyone, send is a no-op.
    check("webhook rejects when unconfigured (403)",
          c.get("/api/whatsapp/webhook", params={"hub.mode": "subscribe",
                "hub.verify_token": "x", "hub.challenge": "1"}).status_code == 403)
    check("send_text no-op when unconfigured", whatsapp.send_text("15551234567", "hi") is False)

    # parse_messages is a pure helper over Meta's webhook shape.
    sample = {"entry": [{"changes": [{"value": {
        "contacts": [{"wa_id": "15551234567", "profile": {"name": "Sara"}}],
        "messages": [{"from": "15551234567", "type": "text",
                      "text": {"body": "what services do you offer?"}}],
    }}]}]}
    check("parse_messages extracts (wa_id, name, text)",
          whatsapp.parse_messages(sample) == [("15551234567", "Sara", "what services do you offer?")])

    # Configure the bridge at runtime and capture outbound sends (no real network).
    appcfg.WHATSAPP_TOKEN, appcfg.WHATSAPP_PHONE_ID, appcfg.WHATSAPP_VERIFY_TOKEN = "t", "9999", "verify-secret"
    sent = []
    whatsapp.send_text_async = lambda to, body: (sent.append((to, body)) or True)

    r = c.get("/api/whatsapp/webhook", params={"hub.mode": "subscribe",
              "hub.verify_token": "verify-secret", "hub.challenge": "CHALLENGE42"})
    check("webhook verify echoes challenge for right token", r.status_code == 200 and r.text == "CHALLENGE42")
    check("webhook verify rejects wrong token",
          c.get("/api/whatsapp/webhook", params={"hub.mode": "subscribe",
                "hub.verify_token": "nope", "hub.challenge": "x"}).status_code == 403)

    # Inbound message → a whatsapp conversation + the bot auto-reply forwarded out.
    check("inbound webhook 200", c.post("/api/whatsapp/webhook", json=sample).status_code == 200)
    wa = [x for x in c.get("/api/admin/chat/conversations", headers=AH).json() if x.get("channel") == "whatsapp"]
    check("whatsapp conversation created", len(wa) == 1)
    check("bot reply forwarded to the visitor's WhatsApp", len(sent) >= 1 and sent[0][0] == "15551234567")

    # Same number reuses the one thread (not a new one each message).
    c.post("/api/whatsapp/webhook", json=sample)
    again = [x for x in c.get("/api/admin/chat/conversations", headers=AH).json() if x.get("channel") == "whatsapp"]
    check("same number reuses one thread", len(again) == 1)

    # Developer Inbox reply is bridged back to WhatsApp.
    sent.clear()
    c.post("/api/admin/chat/conversations/%s/messages" % wa[0]["public_id"], headers=AH,
           json={"body": "Hi! Thanks for reaching out."})
    check("dev Inbox reply bridged to WhatsApp", any(b == "Hi! Thanks for reaching out." for _, b in sent))

    appcfg.WHATSAPP_TOKEN = appcfg.WHATSAPP_PHONE_ID = appcfg.WHATSAPP_VERIFY_TOKEN = ""

    print("== Safepay gateway (inert by default; hosted-redirect when configured) ==")
    from app import safepay  # noqa: E402

    # OFF by default: config advertises the flag, endpoints refuse, helpers stay pure.
    pc = c.get("/api/payments/config").json()
    check("payment config exposes safepay flag",
          pc.get("safepay_enabled") is False and pc.get("stripe_enabled") is False)
    check("safepay disabled by default", safepay.enabled() is False)
    check("safepay checkout 503 when off",
          c.post("/api/payments/safepay/checkout/ANY123").status_code == 503)
    check("safepay webhook 200 (never disables) when off",
          c.post("/api/payments/safepay/webhook", json={"tracker": "t"}).status_code == 200)

    # Pure helpers — no network: amount unit, hosted-checkout URL, signature.
    check("amount honors the configured multiplier",
          safepay.minor_amount(150) == 150 * safepay._MULTIPLIER)
    url = safepay.checkout_url("track_abc", "https://x/app?sfpy=ORD1", "https://x/app", "ORD1")
    check("checkout url is safepay-hosted w/ beacon",
          "getsafepay.com" in url and "beacon=track_abc" in url and "ORD1" in url)
    # Official SDK path — the older /components host 301s to the marketing site.
    check("checkout url uses the official /checkout/pay path", "/checkout/pay?" in url)
    check("webhook sig false without secret",
          safepay.verify_webhook_signature(b"{}", "deadbeef") is False)

    # Switch it on at runtime → enabled(); a valid HMAC verifies (still no network).
    appcfg.SAFEPAY_API_KEY = "sec_test_key"
    appcfg.SAFEPAY_WEBHOOK_SECRET = "whsec_test"
    check("safepay enabled once key set", safepay.enabled() is True)
    _body = b'{"tracker":"track_abc"}'
    _good = _hmac.new(b"whsec_test", _body, _hashlib.sha256).hexdigest()
    check("valid webhook signature accepted", safepay.verify_webhook_signature(_body, _good) is True)
    check("bad webhook signature rejected", safepay.verify_webhook_signature(_body, "nope") is False)

    # Full store-checkout wiring (tracker + verify faked — no real network): an order
    # → hosted-checkout URL that returns to /store, then verify-on-return marks it paid.
    safepay.create_tracker = lambda *a, **k: "track_TEST123"
    _o = c.post("/api/orders", json={
        "customer_name": "Sara", "customer_email": "sara@example.com",
        "payment_method": "Credit / Debit card",
        "items": [{"service": "SaaS Dashboard", "tier": "Starter", "price": 150, "qty": 1}],
    }).json()
    _pid = _o["public_id"]
    _co = c.post("/api/payments/safepay/checkout/%s?return_to=/store" % _pid).json()
    check("safepay checkout returns a hosted url",
          "getsafepay.com" in _co["url"] and "beacon=track_TEST123" in _co["url"])
    check("checkout returns to the store with the order id",
          "%2Fstore" in _co["url"] and ("order_id=" + _pid) in _co["url"])
    safepay.verify_tracker = lambda *a, **k: True
    check("verify-on-return marks the order paid",
          c.get("/api/payments/safepay/verify/%s" % _pid).json().get("paid") is True)
    check("paid order isn't charged again",
          c.post("/api/payments/safepay/checkout/%s" % _pid).status_code == 400)

    appcfg.SAFEPAY_API_KEY = ""
    appcfg.SAFEPAY_WEBHOOK_SECRET = ""

print("\n==== RESULT: %d passed, %d failed ====" % (ok, fail))
if os.path.exists(_DB):
    try:
        os.remove(_DB)
    except Exception:
        pass
raise SystemExit(1 if fail else 0)
