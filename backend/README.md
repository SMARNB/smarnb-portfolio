# Backend — FastAPI app (API + dashboards)

This turns the static portfolio into a full product: client accounts, ordering,
**project tracking with progress bars**, a **developer dashboard**, a built-in
**chat assistant + live chat**, **client testimonials**, and **dashboard-managed
services**. The same server also serves the marketing site, so it's one app, one deploy.

```
backend/app/
├── main.py        # app, static serving, security headers, admin seed, mini-migration
├── config.py      # env/.env settings
├── database.py    # SQLAlchemy engine/session
├── models.py      # User, Order, OrderUpdate, Deliverable, Service, Setting,
│                  #   Testimonial, Conversation, ChatMessage, ChatAttachment
├── schemas.py     # Pydantic
├── security.py    # PBKDF2 password hashing + JWT
├── crypto.py      # encryption-at-rest for PII + email blind index
├── bot.py         # rule-based chat assistant (reads the services catalog)
├── crud.py        # DB operations
├── deps.py        # auth dependencies (client / admin)
└── routers/       # auth, orders, admin, services, testimonials, chat
```

## What the dashboard does (tabs)
- **Orders** — manage status, progress, due date, payment, updates, gated deliverables.
- **Inbox** — every chat thread. The bot answers automatically; click in to reply
  live (that pauses the bot for that thread). Unread + "needs you" badges included.
- **Reviews** — approve / reject / delete testimonials submitted from the site.
- **Services** — add / edit / hide / delete every service. **First run:** click
  **"Import built-in services"** once to pull the catalog from `assets/js/data.js`
  into the DB. After that the DB is authoritative (the bot and the site both use it).

## Chat & uploads (security)
- Visitors get a per-thread secret stored in their browser; logged-in clients are
  matched by account. Files are **images + PDF only**, validated by extension **and**
  magic bytes (SVG is rejected), 10 MB cap, stored in the DB, and served only to the
  thread's participants + admin. No embedded third-party forms.

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
2. **Web service (Render):** <https://render.com> →
   - **Easiest:** New → **Blueprint** → pick this repo. `backend/render.yaml`
     configures everything; just fill the secret values it asks for
     (`ADMIN_PASSWORD`, `DATABASE_URL`, `CORS_ORIGINS`).
   - **Manual:** New → **Web Service** → **Root directory** `backend` →
     **Build** `pip install -r requirements.txt` →
     **Start** `uvicorn app.main:app --host 0.0.0.0 --port $PORT` →
     set `SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_URL`, `CORS_ORIGINS`.
3. Deploy → your whole site + API + dashboards are live at
   `https://your-app.onrender.com` (free tier sleeps when idle, ~30s cold start).
   Open `…/admin` from any device — phone or laptop — and log in.

> Prefer keeping the marketing site on Netlify for speed? Deploy this backend on
> Render for the API/dashboards, set `apiBase` in `assets/js/config.js` to the
> Render URL, and add that URL to the CSP in `_headers`, `netlify.toml` and
> `vercel.json` — both `connect-src` (API calls) **and** `img-src` (so chat image
> attachments load). All-on-Render needs no CSP change since it's same-origin.

## Security notes
- Passwords hashed with PBKDF2-SHA256 (200k iterations, per-user salt).
- JWT bearer auth; admin-only routes gated by role.
- FastAPI sends a strict CSP + hardening headers; static access to `backend/`,
  `.env`, the DB and dotfiles is blocked.
- Order totals are computed **server-side** from the catalog, never trusted from
  the client.
