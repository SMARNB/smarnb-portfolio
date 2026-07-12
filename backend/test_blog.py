"""Blog suite: admin CRUD + image upload + markdown preview, public read of
published posts, XSS-safe server-side markdown rendering, the per-slug <head> +
crawlable article injected into the SPA shell, and sitemap inclusion.

Run:  .venv/Scripts/python test_blog.py
"""
import os
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "portfolio_blog_test.db")
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

# Don't let the on-disk sitemap mirror overwrite the dev-served frontend/dist files
# during tests; the sitemap route generates fresh regardless (see routers/seo.py).
_seo.STATIC_DIR = None

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


# Minimal bytes that satisfy the magic-byte sniff (only the signature is tested).
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
NOT_IMAGE = b"just some text, definitely not an image"

BODY_MD = (
    "# Hello World\n\n"
    "This is my **first** post about Python automation and dashboards.\n\n"
    "Here is a raw tag that must be escaped: <script>alert('xss')</script>\n\n"
    "- one\n- two\n\n"
    "[a link](https://example.com)\n"
)


SERVICE = {
    "title": "Full-Stack SaaS Dashboards", "category": "Development", "icon": "code",
    "short": "Production dashboards.", "tags": ["Python"], "deliverables": ["Code"],
    "slug": "saas-dashboard",
    "packages": [{"tier": "Starter", "price": 150, "delivery": "5 days", "revisions": 1,
                  "summary": "One page.", "features": ["1 page"], "popular": False}]}


with TestClient(app) as c:
    tok = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-admin-123"}).json()["access_token"]
    AH = {"Authorization": "Bearer " + tok}
    c.post("/api/admin/services/import", headers=AH, json={"services": [SERVICE]})

    print("== Blog: empty + auth ==")
    r = c.get("/api/blog")
    check("public /api/blog 200", r.status_code == 200)
    check("categories present", r.json().get("categories") and "Tech" in r.json()["categories"])
    check("no posts yet", r.json().get("posts") == [])
    check("admin create requires auth", c.post("/api/admin/blog", json={"title": "x"}).status_code == 401)

    print("== Blog: create draft ==")
    r = c.post("/api/admin/blog", headers=AH, json={
        "title": "First Post — Automation Wins", "body_md": BODY_MD,
        "category": "Tech", "tags": ["python", "automation"], "status": "draft"})
    check("create 200", r.status_code == 200)
    post = r.json()
    slug = post["slug"]
    pid = post["id"]
    check("slug derived from title", slug == "first-post-automation-wins")
    check("body rendered to HTML", "<h1>" in post["body_html"] and "<strong>first</strong>" in post["body_html"])
    check("raw <script> is escaped (XSS-safe)", "&lt;script&gt;" in post["body_html"] and "<script>alert" not in post["body_html"])
    check("excerpt auto-derived", len(post["excerpt"]) > 0 and "<" not in post["excerpt"])
    check("reading minutes >= 1", post["reading_minutes"] >= 1)

    print("== Blog: draft is private ==")
    check("draft not in public list", c.get("/api/blog").json()["posts"] == [])
    check("draft 404 on public slug", c.get("/api/blog/%s" % slug).status_code == 404)
    check("admin list includes draft", any(p["id"] == pid for p in c.get("/api/admin/blog", headers=AH).json()))

    print("== Blog: publish ==")
    r = c.put("/api/admin/blog/%d" % pid, headers=AH, json={
        "title": "First Post — Automation Wins", "body_md": BODY_MD,
        "category": "Tech", "tags": ["python", "automation"], "status": "published"})
    check("publish 200", r.status_code == 200)
    check("published_at set", r.json()["published_at"] is not None)
    pub = c.get("/api/blog").json()["posts"]
    check("post now public in list", len(pub) == 1 and pub[0]["slug"] == slug)
    check("list omits body (summary only)", "body_html" not in pub[0])
    full = c.get("/api/blog/%s" % slug)
    check("public single 200 + full body", full.status_code == 200 and "<h1>" in full.json()["body_html"])

    print("== Blog: markdown preview (no save) ==")
    r = c.post("/api/admin/blog/preview", headers=AH, json={"body_md": "## Hi <script>bad</script>"})
    check("preview renders + escapes", "<h2>" in r.json()["body_html"] and "&lt;script&gt;" in r.json()["body_html"])

    print("== Blog: image upload ==")
    r = c.post("/api/admin/blog/images", headers=AH, files={"file": ("cover.png", PNG, "image/png")})
    check("upload 200 + url", r.status_code == 200 and r.json()["url"].startswith("/api/blog/images/"))
    img_url = r.json()["url"]
    img = c.get(img_url)
    check("image served with image content-type", img.status_code == 200 and img.headers.get("content-type", "").startswith("image/"))
    check("non-image rejected (415)", c.post("/api/admin/blog/images", headers=AH,
          files={"file": ("note.txt", NOT_IMAGE, "text/plain")}).status_code == 415)
    # attach the uploaded cover to the post
    c.put("/api/admin/blog/%d" % pid, headers=AH, json={
        "title": "First Post — Automation Wins", "body_md": BODY_MD, "cover_image": img_url,
        "category": "Tech", "tags": ["python", "automation"], "status": "published"})

    print("== Blog: related services (attach + resolve + sidebar/SSR) ==")
    c.put("/api/admin/blog/%d" % pid, headers=AH, json={
        "title": "First Post — Automation Wins", "body_md": BODY_MD, "cover_image": img_url,
        "category": "Tech", "tags": ["python", "automation"], "status": "published",
        "related_services": ["saas-dashboard", "does-not-exist"]})
    single = c.get("/api/blog/%s" % slug).json()
    check("related slugs persisted", single.get("related_services") == ["saas-dashboard", "does-not-exist"])
    check("related resolved to active services only (unknown dropped)",
          isinstance(single.get("related"), list) and len(single["related"]) == 1
          and single["related"][0]["slug"] == "saas-dashboard")
    check("resolved related carries title + min price",
          single["related"][0]["title"] == "Full-Stack SaaS Dashboards" and single["related"][0]["min_price"] == 150)
    page_rel = c.get("/blog/%s" % slug).text
    check("SSR article links the related service",
          'href="' in page_rel and "/store#svc-saas-dashboard" in page_rel and "Related services" in page_rel)

    print("== Blog: per-slug <head> + crawlable article (SPA shell) ==")
    page = c.get("/blog/%s" % slug).text
    check("post title in <title>", "First Post" in page and page.count("<title>") == 1)
    check("canonical points at the post", '/blog/%s"' % slug in page and '<link rel="canonical"' in page)
    check("og:type article", 'property="og:type" content="article"' in page)
    check("BlogPosting JSON-LD present", '"BlogPosting"' in page)
    check("full article injected into #root", '<div id="root"><article class="post-article">' in page)
    check("article carries the rendered body", "Automation Wins</h1>" in page or "<h1>" in page)
    check("article body keeps the escaped script", "&lt;script&gt;" in page)

    print("== Blog: index head + unknown slug fallback ==")
    idx = c.get("/blog").text
    check("blog index gets its own title", "Blog —" in idx)
    check("blog index Blog JSON-LD", '"Blog"' in idx)
    unknown = c.get("/blog/nope-not-real").text
    check("unknown slug falls back to index head", "Blog —" in unknown and "post-article" not in unknown)

    print("== Blog: sitemap inclusion ==")
    sm = c.get("/sitemap.xml").text
    check("sitemap lists the post", "/blog/%s</loc>" % slug in sm)
    check("sitemap lists the blog index", "/blog</loc>" in sm)

    print("== Blog: slug uniqueness + delete ==")
    r2 = c.post("/api/admin/blog", headers=AH, json={
        "title": "First Post — Automation Wins", "body_md": "dup", "status": "draft"})
    check("duplicate title => unique slug", r2.json()["slug"] != slug)
    pid2 = r2.json()["id"]
    check("delete 200", c.delete("/api/admin/blog/%d" % pid2, headers=AH).status_code == 200)
    check("deleted draft gone from admin list", not any(p["id"] == pid2 for p in c.get("/api/admin/blog", headers=AH).json()))

    print("== Blog: API not shadowed by SPA ==")
    check("/api/blog still json after all", isinstance(c.get("/api/blog").json().get("posts"), list))

print("\n==== RESULT: %d passed, %d failed ====" % (ok, fail))
if os.path.exists(_DB):
    try:
        os.remove(_DB)
    except Exception:
        pass
raise SystemExit(1 if fail else 0)
