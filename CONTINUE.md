# SMARNB Portfolio — Master Handoff (`CONTINUE.md`)

> The single source of truth for continuing this project on **any machine**.
> Read this file IN FULL before touching code. Deeper history: `git log --oneline`.

- **Live site:** https://smarnb.onrender.com (Render free tier + Neon Postgres)
- **Repo:** `github.com/SMARNB/smarnb-portfolio` (PRIVATE, branch `main`)
- **Owner:** Muhammad Ali Raza (SMARNB) · shahjee975@gmail.com · Pakistan
- **Deploying:** push to `main` → Render auto-builds (~1–2 min). Verify what's
  live via `GET https://smarnb.onrender.com/api/version` → `{commit, started_at}`.

---

## 1. What this is

Freelance portfolio + sales centre. React SPA with a FastAPI backend serving it
single-origin (FastAPI serves `frontend/dist`, injects per-route SEO `<head>` +
JSON-LD server-side, `/api/*` keeps priority). Features: store + cart + orders
with milestone auto-tracking, Safepay card payments (sandbox), manual-payment
proofs, client & admin dashboards (JWT + TOTP 2FA), rule-based chat with admin
live takeover + WhatsApp bridge (inert), blog (admin-managed, server-rendered),
SEO control centre, résumé generator, invoices (branded PDF) + outbound email +
inventory (inert until email creds), scroll-story frontend.

## 2. Layout

```
frontend/            Vite + React 18 + TS (React Router, Framer Motion, Lenis)
  src/styles/        global.css = design tokens + ALL page CSS (single file)
  src/components/    layout/ sections/ ui/ panels/ chat/ dash/
  src/pages/         Home, ServicesPage, WorkPage, ProjectsPage, AboutPage,
                     ContactPage, Store, BlogList/BlogPost, dashboards
backend/             FastAPI app (app/main.py serves dist + API)
  app/               models, crud, routers/, seo.py, emailer.py, invoicing.py,
                     inventory.py, safepay.py, bot.py, whatsapp.py …
  test_*.py          6 SELF-RUNNING suites (see §5)
  render.yaml        Render blueprint (buildFilter **/*, autoDeploy)
.claude/launch.json  dev servers: "portfolio" = uvicorn :8100 (serves dist),
                     "frontend" = vite :5180 (autoPort, proxies /api→8100)
CONTINUE.md          this file
```

## 3. Golden rules (never break)

1. **Design system:** solid indigo `#6366F1` only — NO gradients anywhere
   (`--grad` is aliased to the solid accent on purpose). Both themes (dark
   default + light) must work; all colors via CSS variables.
2. **First-party only:** no third-party scripts/CDNs/embeds (anti-scam rule).
   Fonts are self-hosted Fontsource; three.js work lives in a separate track.
3. **All 6 backend suites stay green** (331 tests today) before any push.
4. **Preview-verify before pushing** — push to `main` deploys the live site.
5. Don't touch the **3D track** (`portfolio-3d` folder / `design-3d` branch on
   the other machine) unless asked.
6. CSP is strict (`script-src 'self'`, no inline). `test_seo.py` imports `_CSP`
   from `app.main` — keep them consistent if you touch headers.
7. Do not commit secrets. `backend/.env` is gitignored — carry it over manually.

## 4. Fresh-machine setup (Windows-tested; adapt paths elsewhere)

```powershell
git clone https://github.com/SMARNB/smarnb-portfolio portfolio   # gh auth login / GCM if prompted
cd portfolio

# Backend venv — requirements.txt is UNPINNED; fresh resolvers pull a
# starlette/httpx combo whose TestClient breaks the suites. Pin the core trio:
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt
backend/.venv/Scripts/pip install "fastapi==0.138.0" "starlette==1.3.1" "httpx==0.28.1"

# Frontend
cd frontend && npm ci && npm run build && cd ..
```

Then create `backend/.env` (gitignored — paste values from the previous
machine; ask the owner). Keys used locally: `SECRET_KEY`, `ENCRYPTION_KEY`,
`ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME`, `CONTACT_WHATSAPP`,
`SAFEPAY_API_KEY`, `SAFEPAY_SECRET_KEY`, `SAFEPAY_ENVIRONMENT=sandbox`.
No `DATABASE_URL` locally → SQLite file, never touches production Neon.
Production secrets live in the Render dashboard, not in git.

**Run dev:** backend `backend/.venv/Scripts/python -m uvicorn app.main:app
--app-dir backend --port 8100` (serves the built dist at :8100), or use the
`.claude/launch.json` configs. Vite dev server: `npm run dev` in `frontend/`
(port 5180, proxies `/api` to :8100).

## 5. Tests (before every push)

Self-running scripts, NOT pytest. On Windows shells set `PYTHONUTF8=1`
(a `→` print crashes cp1252). `test_seo.py` + `test_blog.py` need
`frontend/dist` to exist (run `npm run build` first).

```bash
cd backend
python test_new_features.py   # 130
python test_tracking.py       #  23
python test_seo.py            #  69
python test_blog.py           #  42
python test_security.py       #  25
python test_invoicing.py      #  42   → total 331
```

## 6. Deploy / verify-live checklist

1. Suites green + `npm run build` clean + preview-verified.
2. `git push origin main` → Render builds.
3. `curl https://smarnb.onrender.com/api/version` until `commit` = your hash
   (free tier may cold-start ~30–50s; a self-keepalive pings every 10 min).

## 7. Frontend scroll-story architecture (current design)

`frontend/src/components/ui/StoryStack.tsx` + the story CSS block in
`global.css` ("Story stack" section):

- Every stack child is a full-view **stage**: `position: sticky; top: 0;
  min-height: 100svh`, opaque (page bg + ambient glow), content centred,
  `padding-top` clears the floating pill header. ONE section on screen at a
  time; the next slides over the previous (previous recedes to scale 0.97).
- **Entry variants** rotate per panel (cover / swipe-left / split-x / fade /
  swipe-right / zoom-in / split-y), scroll-driven and reversible; non-cover
  variants counter-translate to play out pinned. Override with the `variants`
  prop.
- **Idle snap:** scroll-linked entries freeze wherever the user stops, so after
  190 ms of scroll silence the stack glides to the nearest fully-open section
  (`scrollToTarget` → Lenis when active).
- **no-pin rail:** any panel taller than the viewport skips pinning and flows
  (catalogue rows on phones, everything on landscape phones) and gets a light
  in-view entrance instead — that keeps short viewports animated.
- Pages: Home = hero fold (first stage) + 3 feature slides (heading rides
  slide 1) + teaser/work/projects/CTA sheets; `/services` = 3 slides + the
  catalogue one ROW (3 cards) per screen + process + CTA; `/about` = sticky
  portrait + one card per screen (`cards` variant). `flush` class pulls stage 1
  under the pill on stack-opening pages.
- The FOOTER is a full-screen stage of its own (a single-panel StoryStack in
  `PublicLayout`) — at rest it owns the screen alone on every public page; the
  snap scans from panel 0 and lands at each panel's real pin position.
- `/about` is ZERO-TRAVEL: `#about` starts flush at the body padding, the
  portrait pins at `--stack-top` (= its load position, never shifts) and the
  card stages pin there too. Cards are **cover-only** (non-cover variants
  counter-translate against a top-0 pin and would park cards ~78px high).
- Hero entrance is PURE CSS (`.hero-enter` keyframes) — BOTH JS approaches
  stranded the first screen blank in the wild (mount-time `animate` vs frozen
  background-tab rAF; whileInView's stagger stalled on real fresh loads too).
  CSS keyframes with `both` fill complete by declaration. RULE: first-screen
  entrances must be CSS; framer is fine for scroll-driven MotionValues and
  below-the-fold whileInView reveals. (The visual's keyframe animates opacity
  ONLY — a transform keyframe with `both` fill would permanently override
  framer's inline scroll-drift transform.)
- `/about` breathes via `--about-gap` (50px): `#about` padding AND the sticky
  pins (portrait + card stages) shift by the same amount, so the zero-travel
  invariant (load position == pin position) still holds; stage min-heights
  subtract the gap.
- The page scrollbar is hidden for visitors (`scrollbar-width:none` +
  `::-webkit-scrollbar` on html); inner scrollers keep theirs.
- Sheets have NO chrome (no radius/border/shadow) — pinned sheets sit at the
  exact viewport top where corners/borders read as a visible seam; identical
  stage backgrounds keep covers seamless (the recede-scale is the depth cue).
- The tech MARQUEE is fixed site chrome at the viewport bottom (rendered in
  PublicLayout, z-95, `--marquee-h`; stages pad their bottom by it; the ≤640
  tier re-declares the token at 36px). Its edge lights are full-width on BOTH
  lines and PULSE in sync (`marquee-glow` opacity breathing — no travelling
  sweeps).
- Size tiers keep every stage inside its pin budget: desktop fill (≥900px
  wide), SHORT desktop (≤820px tall), phone (≤640px wide). If a stage stops
  pinning after a content change, measure `panel.offsetHeight` vs
  `innerHeight + 4` and trim the tier that overflowed.
- Header nav = fit-measured floating pill; the measurement probes geometry
  with a synchronous mutate→read→restore (never `setExpanded(true)` probing —
  that flashed) and the ResizeObserver watches the HEADER WRAPPER, never the
  pill itself (self-observation looped → visible flicker).

**Preview gotchas (cost real time — believe them):** hidden/backgrounded tabs
freeze rAF + compositor frames — screenshots return STALE paints and Lenis
scrolls never move; verify with DOM geometry (`getBoundingClientRect`), not
pixels. `body`/`html` must keep `overflow-x: clip` (NOT `hidden` — hidden
silently kills every `position: sticky`).

## 8. Email status (updated 2026-07-13 — LIVE via Brevo)

Two modules, both transport-agnostic (SendGrid HTTPS **or** Brevo REST, first
configured wins; Render blocks outbound SMTP on every plan so HTTPS is required):
- `backend/app/emailer.py` — invoices, receipts, promo campaigns (+ generic SMTP
  for local).
- `backend/app/email_send.py` — verification / security codes. Its `enabled()` is
  ALSO the switch that turns on the **mandatory signup+verify order gate**
  (`routers/orders.py`): once email is configured, anonymous `POST /api/orders`
  → 401 and unverified → 403, so every order carries a verified name/email.

Owner uses **Brevo** (free tier 300/day), sending from **shahjee975@gmail.com**
(name "Muhammad Ali Raza") until a domain is bought. Locally `backend/.env` has
`BREVO_API_KEY` + `EMAIL_FROM=shahjee975@gmail.com` + `EMAIL_FROM_NAME=Muhammad
Ali Raza`; test email + invoices verified delivering 2026-07-13.
**To turn it on for the LIVE site:** set those three vars in Render → Environment
(this also activates mandatory signup for real visitors). Test from
`/admin → Email → Send test email`.

Invoice email + PDF (`invoicing.py`) are branded with the **favicon logo**
(`frontend/public/email-logo.png`, served at `/email-logo.png`) — NO "SMARNB"
wordmark. Email = "Hi {client}," + warm welcome + **What you're getting**
(per-service price/delivery/work-scope) + **Your project brief** (echoes the
client's checkout `notes`) + invoice table + Track button + "Warm regards,
Muhammad Ali Raza". Header text is pinned `#fffffe !important` for dark-mode
legibility. The work-scope is snapshotted onto each order item at checkout
(`OrderItem.summary/scope/delivery`; Pricing.tsx passes `p.summary`/`p.features`).

## 9. Open items (top = next)

1. **iPhone animation lag:** scroll-story animations lag badly on iPhone ("feels
   like something is crashing" — likely WebKit compositor pressure). Suspects:
   backdrop-filter/blur glows, the infinite `max-content` marquee track,
   marquee-glow pulse. Not yet investigated.
2. **Safepay — ON HOLD (owner):** blocked until the company is registered +
   trademark + business name decided (owner now has a partner; business won't be
   under his personal name). Do NOT push Safepay go-live until he confirms. When
   unblocked: end-to-end test card `4242…` → webhook marks order paid → delete
   ALR-* test orders; then production keys + `SAFEPAY_ENVIRONMENT=production`.
3. **Email go-live on Render:** add the 3 Brevo env vars (see §8) — also flips
   mandatory signup on for the live site.
4. **Blog content roadmap** (first post: CodeWatch build story).
5. GSC housekeeping (submit `sitemap.xml`, request indexing on key pages).
6. Custom domain (when bought): unlocks a proper email sender domain; consider
   Render Starter (~$7/mo) to kill the cold start; set `PUBLIC_BASE_URL`.
7. 3D redesign track continues separately in `portfolio-3d` (branch
   `design-3d`, NOT pushed) on the original machine.

## 10. Continuation prompt (paste into Claude Code on a new machine)

```text
Set up and continue my SMARNB portfolio project on this machine.

Repo: https://github.com/SMARNB/smarnb-portfolio (PRIVATE — if the clone fails,
run `gh auth login` or sign into Git Credential Manager with my GitHub account
first).

1. Clone it: git clone https://github.com/SMARNB/smarnb-portfolio portfolio
   (into my Documents folder unless I say otherwise), then cd into it.
2. Read CONTINUE.md at the repo root IN FULL — it is the master handoff:
   architecture, golden rules, setup gotchas, tests, deploy workflow, email
   status, and the prioritized open-items list. Follow its §4 setup exactly
   (pinned fastapi/starlette/httpx trio, npm ci + build).
3. backend/.env is not in git — ask me to paste my .env from the old machine
   before running anything that needs secrets.
4. Verify the setup: run all 6 backend suites (they must be green — 331 tests)
   and preview the site locally per CONTINUE.md §4.
5. Save the key facts from CONTINUE.md into your persistent project memory so
   future sessions here start informed.
6. Then give me a short status report and either ask me what to build next or
   propose the top item from CONTINUE.md §9 "Open items".

Always follow CONTINUE.md §3 "Golden rules" (solid-indigo no-gradient design
system, first-party only, suites green + preview-verify before any push —
pushing main deploys the live site).
```

---
*Keep this file current: update §7–§9 whenever a session ships something.*
