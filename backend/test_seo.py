"""SEO control-centre checks: the public/admin SEO endpoints, the dynamic
sitemap.xml + robots.txt, and the per-route <head> injection (title, meta, Open
Graph, Twitter, canonical, robots, verification, JSON-LD) the FastAPI server adds
to the SPA shell before serving it.

Run:  .venv/Scripts/python test_seo.py
"""
import json
import os
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "portfolio_seo_test.db")
if os.path.exists(_DB):
    os.remove(_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _DB
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "test-admin-123"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

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


SERVICES = [
    {"title": "Full-Stack SaaS Dashboards in Python", "category": "Development", "icon": "code",
     "short": "Production dashboards.", "tags": ["Python"], "deliverables": ["Code"], "slug": "saas-dashboard",
     "packages": [{"tier": "Starter", "price": 150, "delivery": "5 days", "revisions": 1,
                   "summary": "One page.", "features": ["1 page"], "popular": False}]},
    {"title": "Selenium Bots for OCR & Data Scraping", "category": "Automation", "icon": "robot",
     "short": "Automate the boring stuff.", "tags": ["Selenium"], "deliverables": ["Bot"], "slug": "automation-bot",
     "packages": [{"tier": "Standard", "price": 80, "delivery": "4 days", "revisions": 2,
                   "summary": "A bot.", "features": ["1 bot"], "popular": True}]},
]


with TestClient(app) as c:
    r = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-admin-123"})
    tok = r.json()["access_token"]
    AH = {"Authorization": "Bearer " + tok}

    # Seed real data the JSON-LD/sitemap build from.
    c.post("/api/admin/services/import", headers=AH, json={"services": SERVICES})
    sub = c.post("/api/testimonials", json={
        "name": "Omar Al-Rashid", "role": "SaaS Founder", "rating": 5,
        "text": "Delivered a full dashboard ahead of schedule — already hired again.", "company": ""})
    tlist = c.get("/api/admin/testimonials", headers=AH).json()
    c.patch("/api/admin/testimonials/%d" % tlist[0]["id"], headers=AH, json={"status": "approved"})

    print("== SEO: settings endpoints ==")
    r = c.get("/api/seo")
    check("public /api/seo 200", r.status_code == 200)
    doc = r.json()
    check("doc has general/routes/faq", all(k in doc for k in ("general", "routes", "faq")))
    check("default routes present", "/" in doc["routes"] and "/store" in doc["routes"])
    check("admin save requires auth", c.put("/api/admin/seo", json=doc).status_code == 401)

    # Edit a few things and confirm they round-trip.
    doc["general"]["default_title"] = "SMARNB — Custom Title For Test"
    doc["general"]["google_verification"] = "google-test-token-123"
    doc["general"]["twitter_site"] = "@smarnb"
    doc["routes"]["/store"]["title"] = "Store — Buy Services Test"
    r = c.put("/api/admin/seo", headers=AH, json=doc)
    check("admin save 200", r.status_code == 200)
    check("save round-trips title", r.json()["general"]["default_title"] == "SMARNB — Custom Title For Test")

    print("== SEO: sitemap.xml ==")
    r = c.get("/sitemap.xml")
    check("sitemap 200 + xml", r.status_code == 200 and "xml" in r.headers.get("content-type", ""))
    body = r.text
    check("sitemap urlset", "<urlset" in body and "</urlset>" in body)
    check("sitemap has home + store", "/store</loc>" in body or "/store<" in body)
    check("sitemap includes a service deep-link", "/store#svc-saas-dashboard" in body)
    check("sitemap has lastmod/priority", "<lastmod>" in body and "<priority>" in body)

    print("== SEO: robots.txt ==")
    r = c.get("/robots.txt")
    check("robots 200", r.status_code == 200)
    check("robots references sitemap", "Sitemap:" in r.text and "/sitemap.xml" in r.text)
    check("robots disallows admin", "Disallow: /admin" in r.text)

    print("== SEO: per-route <head> injection ==")
    home = c.get("/").text
    check("home injects managed title", "SMARNB — Custom Title For Test" in home or "<title>" in home)
    check("home has canonical", '<link rel="canonical"' in home)
    check("home has robots meta", '<meta name="robots"' in home)
    check("home has Open Graph", 'property="og:title"' in home and 'property="og:image"' in home)
    check("home has Twitter card", 'name="twitter:card"' in home)
    check("home has google verification", 'name="google-site-verification"' in home and "google-test-token-123" in home)
    check("home embeds JSON-LD", 'type="application/ld+json"' in home)
    # only one <title> survives (dev fallback stripped, managed injected)
    check("exactly one <title>", home.count("<title>") == 1)

    # JSON-LD content built from real data.
    start = home.find('<script type="application/ld+json">') + len('<script type="application/ld+json">')
    end = home.find("</script>", start)
    ld = json.loads(home[start:end].replace("<\\/", "</"))
    graph = ld.get("@graph", [])
    types = []
    for n in graph:
        t = n.get("@type")
        types.extend(t if isinstance(t, list) else [t])
    check("JSON-LD has WebSite", "WebSite" in types)
    check("JSON-LD has ProfessionalService/Person", "ProfessionalService" in types or "Person" in types)
    check("JSON-LD has Service entries", types.count("Service") >= 2)
    check("home has no FAQPage (now on /contact)", "FAQPage" not in types)
    check("JSON-LD has BreadcrumbList", "BreadcrumbList" in types)
    ident = next((n for n in graph if "ProfessionalService" in (n.get("@type") or []) or n.get("@type") == "Person"), {})
    check("JSON-LD AggregateRating from approved review", "aggregateRating" in ident)
    check("JSON-LD includes Review", isinstance(ident.get("review"), list) and len(ident["review"]) >= 1)

    store = c.get("/store").text
    check("store route gets its own title", "Store — Buy Services Test" in store)
    # store has services but no FAQ
    check("store has no FAQPage", "FAQPage" not in store)

    # New multi-page routes get their own server-rendered head + JSON-LD.
    services_pg = c.get("/services").text
    check("services route gets its own title", "Services —" in services_pg)
    check("services has Service entries", '"@type": "Service"' in services_pg)
    contact = c.get("/contact").text
    check("contact route gets its own title", "Contact" in contact)
    check("contact has FAQPage", "FAQPage" in contact)
    about = c.get("/about").text
    check("about route gets its own title + canonical", "About" in about and "/about" in about)

    app_shell = c.get("/app").text
    check("/app is noindex", 'content="noindex' in app_shell.replace(", ", ",").replace(" ", "") or "noindex" in app_shell)

    # editing settings is reflected immediately (cache cleared on save)
    doc["general"]["default_title"] = "Changed Again Title"
    doc["routes"]["/"]["title"] = "Changed Again Title"
    c.put("/api/admin/seo", headers=AH, json=doc)
    check("cache cleared on save (new title shows)", "Changed Again Title" in c.get("/").text)

    # sensitive API still not shadowed by the SPA catch-all
    check("/api/health still json", c.get("/api/health").json().get("ok") is True)

print("\n==== RESULT: %d passed, %d failed ====" % (ok, fail))
if os.path.exists(_DB):
    try:
        os.remove(_DB)
    except Exception:
        pass
raise SystemExit(1 if fail else 0)
