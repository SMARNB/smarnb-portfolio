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
from app import seo as seo_mod  # noqa: E402
from app.database import SessionLocal  # noqa: E402

# Importing app.main points seo.STATIC_DIR at the real frontend/dist; disable the
# on-disk mirror for the main run so tests never overwrite the dev-served files.
# (A dedicated block below re-enables it against a temp dir to exercise the writer.)
seo_mod.STATIC_DIR = None

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

    # same_as (social profiles) must UNION with the code defaults — a doc saved
    # before a new profile was added can't silently hide it.
    doc2 = c.get("/api/admin/seo", headers=AH).json()
    doc2["general"]["same_as"] = ["https://example.com/custom-profile"]
    saved = c.put("/api/admin/seo", headers=AH, json=doc2).json()
    got = saved["general"]["same_as"]
    check("same_as keeps code defaults after a save",
          "https://github.com/SMARNB" in got and any("linkedin.com" in s for s in got))
    check("same_as keeps the stored custom entry", "https://example.com/custom-profile" in got)

    print("== SEO: sitemap.xml (conventional path) ==")
    r = c.get("/sitemap.xml")
    check("sitemap 200 + xml", r.status_code == 200 and "xml" in r.headers.get("content-type", ""))
    body = r.text
    check("sitemap urlset", "<urlset" in body and "</urlset>" in body)
    check("sitemap has home + store", "/store</loc>" in body or "/store<" in body)
    check("sitemap includes a service deep-link", "/store#svc-saas-dashboard" in body)
    check("sitemap has lastmod/priority", "<lastmod>" in body and "<priority>" in body)

    print("== SEO: /sitemap_index.xml redirects to /sitemap.xml ==")
    r = c.get("/sitemap_index.xml", follow_redirects=False)
    check("index-alias sitemap 301", r.status_code == 301)
    check("index-alias redirects to canonical path", r.headers.get("location") == "/sitemap.xml")

    print("== SEO: robots.txt ==")
    r = c.get("/robots.txt")
    check("robots 200", r.status_code == 200)
    check("robots references sitemap", "Sitemap:" in r.text and "/sitemap.xml" in r.text)
    check("robots does not reference stale sitemap_index", "/sitemap_index.xml" not in r.text)
    check("robots disallows admin", "Disallow: /admin" in r.text)

    print("== SEO: sitemap is crash-proof (DB unavailable) ==")
    # Even if the DB call blows up, the core route pages must still be emitted
    # (Google fail-closes the entire site if the sitemap errors).
    class _Boom:
        def query(self, *a, **k):
            raise RuntimeError("db down")
    boom_xml = seo_mod.build_sitemap(_Boom())
    check("crash-proof sitemap still has <urlset>", "<urlset" in boom_xml and "</urlset>" in boom_xml)
    check("crash-proof sitemap still lists home", "smarnb.onrender.com/</loc>" in boom_xml)

    print("== SEO: write_seo_files mirrors real files to disk ==")
    _mirror = tempfile.mkdtemp()
    seo_mod.STATIC_DIR = _mirror
    try:
        db2 = SessionLocal()
        try:
            seo_mod.write_seo_files(db2)
        finally:
            db2.close()
        sm_path = os.path.join(_mirror, "sitemap.xml")
        rb_path = os.path.join(_mirror, "robots.txt")
        check("sitemap.xml written to disk", os.path.isfile(sm_path))
        check("robots.txt written to disk", os.path.isfile(rb_path))
        with open(sm_path, encoding="utf-8") as fh:
            check("mirrored sitemap is valid xml", "<urlset" in fh.read())
    finally:
        seo_mod.STATIC_DIR = None

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

    print("== SEO: marketing & analytics (opt-in, CSP-safe) ==")
    from app.main import _CSP as BASE_CSP

    # OFF by default: CSP byte-identical to the strict first-party base, no loader.
    csp_off = c.get("/").headers.get("content-security-policy")
    check("CSP first-party (byte-identical) when no marketing ids", csp_off == BASE_CSP)
    check("CSP has no vendor domains when off",
          "googletagmanager" not in (csp_off or "") and "facebook" not in (csp_off or ""))
    check("no /marketing.js loader in head when off", "/marketing.js" not in c.get("/").text)
    mkt_off = c.get("/marketing.js")
    check("/marketing.js served as javascript", "javascript" in mkt_off.headers.get("content-type", ""))
    check("/marketing.js inert when off", "fbq(" not in mkt_off.text and "gtag/js" not in mkt_off.text)

    # Turn on GA4 + Meta Pixel + Meta domain verification.
    doc = c.get("/api/seo").json()
    doc["general"]["ga4_id"] = "G-TEST12345"
    doc["general"]["meta_pixel_id"] = "100200300400500"
    doc["general"]["meta_domain_verification"] = "fbverify-token-xyz"
    r = c.put("/api/admin/seo", headers=AH, json=doc)
    check("marketing ids round-trip on save", r.json()["general"]["ga4_id"] == "G-TEST12345")

    home2 = c.get("/").text
    check("head loads first-party /marketing.js when on", '<script src="/marketing.js" defer></script>' in home2)
    check("inert facebook-domain-verification meta injected",
          'name="facebook-domain-verification"' in home2 and "fbverify-token-xyz" in home2)
    mkt_on = c.get("/marketing.js").text
    check("/marketing.js boots gtag for GA4", "gtag/js?id='+ids[0]" in mkt_on and "G-TEST12345" in mkt_on)
    check("/marketing.js boots Meta Pixel", "fbq('init','100200300400500')" in mkt_on)

    csp_on = c.get("/").headers.get("content-security-policy")
    check("CSP adds googletagmanager to script-src", "https://www.googletagmanager.com" in csp_on)
    check("CSP adds google-analytics to connect-src",
          "https://www.google-analytics.com" in csp_on and "https://*.analytics.google.com" in csp_on)
    check("CSP adds Meta Pixel domains",
          "https://connect.facebook.net" in csp_on and "https://www.facebook.com" in csp_on)
    check("CSP gains a frame-src for the pixel", "frame-src" in csp_on)
    check("CSP has no Google Ads domains until that id is set", "doubleclick" not in csp_on)

    # Add Google Ads → its doubleclick domains appear; both gtag ids configured.
    doc = c.get("/api/seo").json()
    doc["general"]["google_ads_id"] = "AW-99887766"
    c.put("/api/admin/seo", headers=AH, json=doc)
    csp_ads = c.get("/").headers.get("content-security-policy")
    check("CSP adds Google Ads doubleclick domains",
          "https://googleads.g.doubleclick.net" in csp_ads and "https://td.doubleclick.net" in csp_ads)
    mkt_ads = c.get("/marketing.js").text
    check("/marketing.js configures both GA4 + Ads",
          "'G-TEST12345'" in mkt_ads and "'AW-99887766'" in mkt_ads)

    # An injected id can never break the JS string / open the CSP (sanitised).
    doc = c.get("/api/seo").json()
    doc["general"]["ga4_id"] = "G-OK_1';evil//"
    c.put("/api/admin/seo", headers=AH, json=doc)
    check("marketing id is sanitised (no quote/escape leaks)", "';evil" not in c.get("/marketing.js").text)

    # Reversible: clearing every id restores the byte-identical strict CSP.
    doc = c.get("/api/seo").json()
    for k in ("ga4_id", "gtm_id", "google_ads_id", "meta_pixel_id", "meta_domain_verification"):
        doc["general"][k] = ""
    c.put("/api/admin/seo", headers=AH, json=doc)
    check("CSP reverts byte-identical when ids cleared",
          c.get("/").headers.get("content-security-policy") == BASE_CSP)
    check("marketing loader removed from head when cleared", "/marketing.js" not in c.get("/").text)

    # sensitive API still not shadowed by the SPA catch-all
    check("/api/health still json", c.get("/api/health").json().get("ok") is True)

print("\n==== RESULT: %d passed, %d failed ====" % (ok, fail))
if os.path.exists(_DB):
    try:
        os.remove(_DB)
    except Exception:
        pass
raise SystemExit(1 if fail else 0)
