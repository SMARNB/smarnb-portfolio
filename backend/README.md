# Backend — FastAPI app (API + dashboards)

This turns the static portfolio into a full product: client accounts, ordering,
**project tracking with progress bars**, and a **developer dashboard**. The same
server also serves the marketing site, so it's one app, one deploy.

```
backend/app/
├── main.py        # app, static serving, security headers, admin seed
├── config.py      # env/.env settings
├── database.py    # SQLAlchemy engine/session
├── models.py      # User, Order, OrderUpdate
├── schemas.py     # Pydantic
├── security.py    # PBKDF2 password hashing + JWT
├── crud.py        # DB operations
├── deps.py        # auth dependencies (client / admin)
└── routers/       # auth, orders, admin
```

## Run locally (Windows)
```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8100
```
(macOS/Linux: `.venv/bin/python …`.)

Then open:
- **http://localhost:8100/** — the marketing site
- **http://localhost:8100/app** — client login / projects
- **http://localhost:8100/admin** — developer dashboard
- **http://localhost:8100/docs** — interactive API docs

**Admin login:** `shahjee975@gmail.com` / `admin12345` → **change this** before
deploying (set `ADMIN_PASSWORD` in `.env`).

Helpers: `python smoke_test.py` (end-to-end API check), `python seed_demo.py`
(creates a demo client + in-progress order for screenshots).

## Configuration (`backend/.env`, copy from `.env.example`)
| Var | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing — set a long random string in prod |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` | the seeded developer account |
| `DATABASE_URL` | defaults to local SQLite; use Postgres in prod |
| `CORS_ORIGINS` | allowed browser origins (your domain in prod) |

## Deploy free (perpetual free tier)
SQLite is great locally but resets on most hosts' redeploys, so use a free
**Neon** Postgres for persistence + a free **Render** web service:

1. **Database (Neon):** create a free project at <https://neon.tech> → copy the
   connection string. Convert it to a pure-python driver URL:
   `postgresql+pg8000://USER:PASSWORD@HOST/DBNAME` and uncomment `pg8000` in
   `requirements.txt`.
2. **Web service (Render):** <https://render.com> → New → **Web Service** → connect
   your GitHub repo →
   - **Root directory:** `backend`
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** set `SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_URL` (the Neon
     URL), `CORS_ORIGINS` (your Render URL).
3. Deploy → your whole site + API + dashboards are live at
   `https://your-app.onrender.com` (free tier sleeps when idle, ~30s cold start).

> Prefer keeping the marketing site on Netlify for speed? Deploy this backend on
> Render for the API/dashboards, and set `apiBase` in `assets/js/config.js` to the
> Render URL (and add that URL to the CSP `connect-src`). Both work.

## Security notes
- Passwords hashed with PBKDF2-SHA256 (200k iterations, per-user salt).
- JWT bearer auth; admin-only routes gated by role.
- FastAPI sends a strict CSP + hardening headers; static access to `backend/`,
  `.env`, the DB and dotfiles is blocked.
- Order totals are computed **server-side** from the catalog, never trusted from
  the client.
