"""End-to-end checks for the new features: services import + managed catalog,
testimonials submit/moderate, and chat (bot replies, order-via-chat, uploads,
admin inbox). Runs against a throwaway SQLite DB via FastAPI's TestClient.

Run:  .venv/Scripts/python test_new_features.py
"""
import base64
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

    print("== Chat: smarter bot + curated learning ==")
    # common-language question answered from the built-in knowledge base
    r = c.post("/api/chat/start", json={})
    cid2, sec2 = r.json()["public_id"], r.json()["secret"]
    SH2 = {"X-Chat-Secret": sec2}
    msgs = c.post("/api/chat/%s/messages" % cid2, headers=SH2,
                  json={"body": "how do i pay you?"}).json()["messages"]
    last = msgs[-1]["body"].lower()
    check("bot answers a common-language question", "payment" in last or "raast" in last)

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

print("\n==== RESULT: %d passed, %d failed ====" % (ok, fail))
if os.path.exists(_DB):
    try:
        os.remove(_DB)
    except Exception:
        pass
raise SystemExit(1 if fail else 0)
