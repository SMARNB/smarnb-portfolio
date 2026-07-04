"""FastAPI application: JSON API + serves the static site and dashboards."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from . import config, crud, seo
from .database import Base, SessionLocal, engine, get_db
from .routers import admin, auth, blog, chat, orders, payments, services, testimonials
from .routers import seo as seo_router
from .routers import whatsapp as whatsapp_router


def _detect_commit():
    """The deployed git SHA. Render injects RENDER_GIT_COMMIT at build time; locally
    we ask git once at startup (best-effort, never fatal)."""
    sha = os.environ.get("RENDER_GIT_COMMIT", "").strip()
    if sha:
        return sha
    try:
        import subprocess
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=config.SITE_DIR,
            stderr=subprocess.DEVNULL, timeout=2,
        ).decode().strip()
    except Exception:
        return ""


_COMMIT = _detect_commit()
_STARTED_AT = datetime.now(timezone.utc).isoformat()


def _ensure_columns():
    """Tiny migration for pre-existing databases: add columns that newer models
    introduced (create_all only creates missing *tables*, not new columns)."""
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    if "services" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("services")}
        if "deliverables_json" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE services ADD COLUMN deliverables_json TEXT DEFAULT '[]'"))
    if "blog_posts" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("blog_posts")}
        if "related_services_json" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE blog_posts ADD COLUMN related_services_json TEXT DEFAULT '[]'"))
    if "conversations" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("conversations")}
        with engine.begin() as conn:
            if "channel" not in cols:
                conn.execute(text("ALTER TABLE conversations ADD COLUMN channel VARCHAR(20) DEFAULT 'web'"))
            if "wa_id" not in cols:
                conn.execute(text("ALTER TABLE conversations ADD COLUMN wa_id VARCHAR(40) DEFAULT ''"))
    if "orders" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("orders")}
        if "payment_ref" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE orders ADD COLUMN payment_ref VARCHAR(120) DEFAULT ''"))
    if "users" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("users")}
        adds = [
            ("email_verified", "BOOLEAN DEFAULT FALSE"),
            ("verify_code_hash", "VARCHAR(128) DEFAULT ''"),
            ("verify_expires", "TIMESTAMP NULL"),
            ("verify_sent_at", "TIMESTAMP NULL"),
            ("verify_attempts", "INTEGER DEFAULT 0"),
            ("totp_secret", "TEXT"),
            ("totp_enabled", "BOOLEAN DEFAULT FALSE"),
        ]
        added_verified = False
        with engine.begin() as conn:
            for name, ddl in adds:
                if name not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN %s %s" % (name, ddl)))
                    if name == "email_verified":
                        added_verified = True
        # ONE-TIME, only when the column is first created: existing accounts predate
        # verification, so mark them verified (never lock a real customer out later).
        if added_verified:
            with engine.begin() as conn:
                conn.execute(text("UPDATE users SET email_verified = TRUE"))


def _start_self_keepalive():
    """Keep the Render free instance awake by pinging our own public URL on an
    interval (10 min < Render's 15-min idle spin-down window). A cold instance
    breaks Googlebot's robots.txt/sitemap fetches — which makes Search Console
    report "blocked by robots.txt" / "sitemap could not be read" — so staying warm
    fixes indexing. Enabled by default on Render when a public base URL is known;
    set KEEPALIVE_SELF=0 to turn it off. Always-warm ≈720h/mo < the 750h free quota."""
    flag = os.environ.get("KEEPALIVE_SELF", "").strip().lower()
    on_render = os.environ.get("RENDER", "").lower() == "true"
    base = (config.PUBLIC_BASE_URL or "").rstrip("/")
    enabled = flag in ("1", "true", "yes") or (on_render and bool(base) and flag not in ("0", "false", "no"))
    if not (enabled and base):
        return
    import threading
    import time as _time
    import urllib.request
    url = base + "/api/health"

    def _loop():
        while True:
            _time.sleep(600)
            try:
                urllib.request.urlopen(url, timeout=10).read()
            except Exception:
                pass

    threading.Thread(target=_loop, daemon=True).start()
    print("[keepalive] self-ping every 10 min →", url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed the admin (developer) account on first run.
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    db = SessionLocal()
    try:
        if not crud.get_user_by_email(db, config.ADMIN_EMAIL):
            crud.create_user(db, config.ADMIN_EMAIL, config.ADMIN_PASSWORD,
                             config.ADMIN_NAME, role="admin", email_verified=True)
            print("[seed] created admin account:", config.ADMIN_EMAIL)
        crud.backfill_milestones(db)   # give pre-tracking orders a pipeline
        seo.write_seo_files(db)        # mirror sitemap.xml/robots.txt to disk as real files
    finally:
        db.close()
    _start_self_keepalive()
    yield


app = FastAPI(title="Muhammad Ali Raza — Portfolio API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,          # we use bearer tokens, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; font-src 'self'; connect-src 'self' https://formspree.io; "
    "worker-src 'self' blob:; "
    "form-action 'self' https://formspree.io; base-uri 'self'; object-src 'none'; frame-ancestors 'none'"
)
# Note: `blob:` in img-src is first-party (in-memory, same-origin object URLs). The
# admin Inbox fetches chat attachments with the bearer token and renders them from
# URL.createObjectURL(blob), so image/PDF previews need blob: to be allowed.
# `worker-src 'self' blob:` is likewise first-party: three.js's DRACOLoader decodes
# compressed .glb models in a Web Worker built from a same-origin Blob (decoder
# vendored at /draco/, no CDN). Without the directive worker-src falls back to
# script-src 'self', which blocks blob workers.

# Embedded Safepay checkout renders Safepay's payment app in an IFRAME on our page
# (no third-party script ever runs on our origin — script-src stays 'self'). Allow
# framing exactly the configured checkout hosts, and only while Safepay is enabled;
# with no key the CSP above is byte-identical.
if config.SAFEPAY_API_KEY:
    from urllib.parse import urlparse as _urlparse
    _sfpy_hosts = []
    for _u in (config.SAFEPAY_EMBED_BASE, config.SAFEPAY_CHECKOUT_BASE):
        _p = _urlparse(_u)
        _origin = "%s://%s" % (_p.scheme, _p.netloc)
        if _origin not in _sfpy_hosts:
            _sfpy_hosts.append(_origin)
    _CSP += "; frame-src 'self' " + " ".join(_sfpy_hosts)


import re as _re
from fastapi.responses import PlainTextResponse as _PlainText

# Block static access to the backend source, dotfiles (.git/.env/.claude), etc.
_BLOCKED = _re.compile(r"^/(backend(/|$)|\.)", _re.IGNORECASE)


@app.middleware("http")
async def block_sensitive(request, call_next):
    if _BLOCKED.match(request.url.path):
        return _PlainText("Not found", status_code=404)
    return await call_next(request)


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    p = request.url.path
    if not (p.startswith("/docs") or p.startswith("/redoc") or p.startswith("/openapi")):
        h = resp.headers
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()")
        h.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
        # CSP is byte-identical to _CSP until a marketing id is set in the dashboard;
        # then exactly that vendor's domains are appended (see seo.csp_with_marketing).
        h.setdefault("Content-Security-Policy", seo.cached_csp(_CSP))
        # Caching: Vite content-hashes everything under /assets/, so those are
        # immutable; revalidate the SPA shell + other markup; cache loose images.
        last = p.rsplit("/", 1)[-1].lower()
        if p.startswith("/api/"):
            h.setdefault("Cache-Control", "no-store")
        elif p.startswith("/assets/"):
            h.setdefault("Cache-Control", "public, max-age=31536000, immutable")
        elif last.endswith((".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico", ".woff", ".woff2")):
            h.setdefault("Cache-Control", "public, max-age=604800")
        else:
            h.setdefault("Cache-Control", "no-cache")
    return resp

app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(services.router)
app.include_router(testimonials.router)
app.include_router(chat.router)
app.include_router(chat.admin_router)
app.include_router(payments.router)
app.include_router(seo_router.router)   # /api/seo, /api/admin/seo, /sitemap.xml, /robots.txt, /marketing.js
app.include_router(whatsapp_router.router)  # /api/whatsapp/webhook (WhatsApp Cloud API bridge)
app.include_router(blog.router)         # /api/blog, /api/blog/{slug}, /api/blog/images/{id}
app.include_router(blog.admin_router)   # /api/admin/blog CRUD + image upload + preview


@app.get("/api/health")
def health():
    return {"ok": True, "service": "portfolio-api"}


@app.get("/api/version")
def version():
    """What's actually running — confirm a push auto-deployed by checking `commit`,
    and see when the live instance booted via `started_at`."""
    return {
        "commit": _COMMIT[:7] if _COMMIT else "unknown",
        "commit_full": _COMMIT,
        "branch": os.environ.get("RENDER_GIT_BRANCH", ""),
        "on_render": os.environ.get("RENDER", "").lower() == "true",
        "started_at": _STARTED_AT,
    }


# --- Serve the built React app (single origin) --------------------------------
# The frontend is a Vite SPA built to frontend/dist. We serve its real files when
# they exist and fall back to index.html for any other path so client-side routes
# (/, /store, /app, /admin, …) all work on direct load / refresh. Registered LAST
# so /api/* and the routes above keep priority.
_DIST_DIR = os.path.join(config.SITE_DIR, "frontend", "dist")
_INDEX = os.path.join(_DIST_DIR, "index.html")
seo.STATIC_DIR = _DIST_DIR   # where seo.write_seo_files persists sitemap.xml/robots.txt

# Known client-side routes — used to pick the right SEO meta/JSON-LD per page.
_SPA_ROUTES = {"/", "/store", "/services", "/work", "/projects", "/about", "/contact",
               "/blog", "/app", "/admin"}
# Dev-fallback tags we strip from the shell before injecting the managed ones, so
# the page never ends up with two <title>s / descriptions / icons.
_STRIP_SHELL = _re.compile(
    r'\s*(?:<title>.*?</title>|<meta\s+name="description"[^>]*>|<link\s+rel="icon"[^>]*>)',
    _re.IGNORECASE | _re.DOTALL)


def _route_for(full_path: str) -> str:
    """Map a request path to one of the known SPA routes (or 'default')."""
    seg = full_path.strip("/").split("/", 1)[0] if full_path else ""
    path = "/" + seg if seg else "/"
    return path if path in _SPA_ROUTES else "default"


def _blog_slug(full_path: str):
    """The post slug for a /blog/<slug> request, else None."""
    parts = full_path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "blog" and parts[1]:
        return parts[1]
    return None


def _render_shell(db: Session, full_path: str) -> HTMLResponse:
    """The SPA shell with the route's SEO <head> injected, so crawlers get correct
    title/meta/Open Graph/Twitter/canonical/robots + JSON-LD without running JS. For
    a blog post the full article HTML is also injected into #root (React replaces it
    on mount) so crawlers see the whole post."""
    try:
        with open(_INDEX, "r", encoding="utf-8") as fh:
            shell = fh.read()
    except OSError:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        route = _route_for(full_path)
        slug = _blog_slug(full_path) if route == "/blog" else None
        article = ""
        head = None
        if slug:
            head = seo.cached_blog_post_head(db, slug)  # None for unknown/draft slug
            if head is not None:
                article = seo.blog_article_html(db, slug)
        if head is None:
            head = seo.cached_head(db, route)
        shell = _STRIP_SHELL.sub("", shell)
        shell = shell.replace("</head>", "  " + head + "\n</head>", 1)
        if article:
            shell = shell.replace('<div id="root"></div>',
                                  '<div id="root">' + article + "</div>", 1)
    except Exception:
        # Never let an SEO error take down the site — fall back to the raw shell.
        pass
    # The shell must always revalidate (content-hashed assets handle caching).
    return HTMLResponse(shell, headers={"Cache-Control": "no-cache"})


@app.get("/{full_path:path}")
def spa(full_path: str, db: Session = Depends(get_db)):
    # Never let the SPA shell shadow the JSON API.
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    # Serve a real built file if it exists (assets, favicon, manifest, images…),
    # guarding against path traversal outside dist.
    if full_path:
        candidate = os.path.normpath(os.path.join(_DIST_DIR, full_path))
        if candidate.startswith(_DIST_DIR) and os.path.isfile(candidate):
            return FileResponse(candidate)
    # Otherwise hand back the SPA shell (with route-aware SEO) for client routing.
    return _render_shell(db, full_path)
