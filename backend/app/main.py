"""FastAPI application: JSON API + serves the static site and dashboards."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config, crud
from .database import Base, SessionLocal, engine
from .routers import admin, auth, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed the admin (developer) account on first run.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not crud.get_user_by_email(db, config.ADMIN_EMAIL):
            crud.create_user(db, config.ADMIN_EMAIL, config.ADMIN_PASSWORD,
                             config.ADMIN_NAME, role="admin")
            print("[seed] created admin account:", config.ADMIN_EMAIL)
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
    "img-src 'self' data:; font-src 'self'; connect-src 'self' https://formspree.io; "
    "form-action 'self' https://formspree.io; base-uri 'self'; object-src 'none'; frame-ancestors 'none'"
)


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
    return resp

app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "portfolio-api"}


# Clean URLs for the two dashboards (the HTML lives in the site root).
@app.get("/app")
def client_dashboard():
    return FileResponse(os.path.join(config.SITE_DIR, "app.html"))


@app.get("/admin")
def admin_dashboard():
    return FileResponse(os.path.join(config.SITE_DIR, "admin.html"))


# Mount the whole static site LAST so /api/* and the routes above take priority.
app.mount("/", StaticFiles(directory=config.SITE_DIR, html=True), name="site")
