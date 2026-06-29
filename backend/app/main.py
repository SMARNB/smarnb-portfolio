"""FastAPI application: JSON API + serves the static site and dashboards."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import config, crud
from .database import Base, SessionLocal, engine
from .routers import admin, auth, chat, orders, payments, services, testimonials


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed the admin (developer) account on first run.
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    db = SessionLocal()
    try:
        if not crud.get_user_by_email(db, config.ADMIN_EMAIL):
            crud.create_user(db, config.ADMIN_EMAIL, config.ADMIN_PASSWORD,
                             config.ADMIN_NAME, role="admin")
            print("[seed] created admin account:", config.ADMIN_EMAIL)
        crud.backfill_milestones(db)   # give pre-tracking orders a pipeline
    finally:
        db.close()
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
    "form-action 'self' https://formspree.io; base-uri 'self'; object-src 'none'; frame-ancestors 'none'"
)
# Note: `blob:` in img-src is first-party (in-memory, same-origin object URLs). The
# admin Inbox fetches chat attachments with the bearer token and renders them from
# URL.createObjectURL(blob), so image/PDF previews need blob: to be allowed.


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
        h.setdefault("Content-Security-Policy", _CSP)
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


@app.get("/{full_path:path}")
def spa(full_path: str):
    # Never let the SPA shell shadow the JSON API.
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    # Serve a real built file if it exists (assets, favicon, manifest, images…),
    # guarding against path traversal outside dist.
    if full_path:
        candidate = os.path.normpath(os.path.join(_DIST_DIR, full_path))
        if candidate.startswith(_DIST_DIR) and os.path.isfile(candidate):
            return FileResponse(candidate)
    # Otherwise hand back the SPA shell for client-side routing.
    return FileResponse(_INDEX)
