# Deploy guide — Render + Neon (free, ~10 minutes)

This puts your **whole project** (site + API + client/developer dashboards + chat)
online at **`https://smarnb.onrender.com`**, reachable from any device.

You'll do the clicks (it's your Render/Neon accounts); everything in the code is
already wired for it. Two free accounts, no card required.

---

## Step 1 — Create the database (Neon, free, keeps your data)

Render's own disk resets on each deploy, so we store data in a free Neon Postgres.

1. Go to **https://neon.tech** → **Sign up** (use your Google / `shahjee975@gmail.com`).
2. **Create project** → any name (e.g. `smarnb`) → region closest to you → Create.
3. On the project dashboard, find **Connection string** → copy it. It looks like:
   ```
   postgresql://neondb_owner:XXXX@ep-cool-name-12345.eu-central-1.aws.neon.tech/neondb?sslmode=require
   ```
   Keep this tab open — you'll paste this whole string into Render in Step 2.
   (You don't need to edit it — the app converts it to the right driver + SSL automatically.)

---

## Step 2 — Deploy on Render (Blueprint)

1. Go to **https://dashboard.render.com** (you're already signed in).
2. Click **New +** (top right) → **Blueprint**.
3. **Connect GitHub** if asked, and pick the repo **`SMARNB/smarnb-portfolio`**
   (grant access to just that repo if Render asks).
4. Render reads **`backend/render.yaml`** and shows a service named **`smarnb`**.
   It will ask you to fill the values marked "sync:false":
   - **`ADMIN_PASSWORD`** → type a strong password. ⚠️ **This is what protects your
     `/admin` dashboard on the public internet — make it long.**
   - **`DATABASE_URL`** → paste the **Neon connection string** from Step 1 (as-is).
5. Click **Apply** / **Create**. Render installs and starts it (first build ~2–4 min).
6. When it goes live, open **`https://smarnb.onrender.com`** 🎉

> Free tier note: the server **sleeps after ~15 min idle**, so the first visit after
> a quiet period takes ~30–50s to wake. Refresh once and it's fast again.

---

## Step 3 — First-run setup (2 minutes)

1. Open **`https://smarnb.onrender.com/admin`** → log in with `shahjee975@gmail.com`
   and the **ADMIN_PASSWORD** you set.
2. Go to the **Services** tab → click **"Import built-in services"** (one time).
   This loads your 10 services into the database so you can edit/hide/delete them
   and so the chat assistant knows them.
3. (Optional) Edit your **social links** in `assets/js/config.js → socials`, commit,
   and push — Render redeploys automatically (see "Updating" below).

---

## Your address / domain

- **Free:** `https://smarnb.onrender.com` (the service name `smarnb` sets the subdomain).
- **Custom domain** (e.g. `smarnb.com`): you'd **buy** it (~$10–15/yr from Namecheap,
  Cloudflare, GoDaddy…), then in Render → your service → **Settings → Custom Domains**
  → add it and point the DNS record they show you. Render issues HTTPS automatically.
  A `.com`/`.dev` can't be free, but `smarnb.onrender.com` is yours at no cost.

---

## Updating the live site later

Render auto-deploys every push to `main` — **frontend or backend**. (`render.yaml`
sets `buildFilter: "**/*"` so a change *anywhere* in the repo triggers a deploy;
without it, `rootDir: backend` would only redeploy on `backend/` changes.)
```bash
git add -A
git commit -m "Update content"
git push
```
Within a minute Render rebuilds and your live site updates. To confirm exactly
what's live, open **`/api/version`** — `commit` is the deployed git SHA and
`started_at` is when the current instance booted.

---

## Turning on Stripe card payments later (optional)

Right now payments are **manual** (Raast / SadaPay shown to clients; you confirm).
Card payments are scaffolded but **off** — enabling them costs nothing in code, but:

> **Heads-up for Pakistan:** Stripe does **not** onboard Pakistani entities to
> *receive* money. To actually collect card payments you'd need a Stripe-supported
> business (US/UK company, or via a service like Payoneer/Wise business). **Test
> mode** works for demos without any of that.

When you're ready:
1. Create a Stripe account at **https://stripe.com** → **Developers → API keys** →
   copy the **Secret key** (`sk_test_…` for testing, `sk_live_…` for real).
2. In Render → your service → **Environment**, add:
   - `STRIPE_SECRET_KEY` = your secret key
3. Uncomment `stripe>=9.0` in `backend/requirements.txt`, commit, push.
4. (For automatic "paid" status) In Stripe → **Developers → Webhooks** → add endpoint
   `https://smarnb.onrender.com/api/payments/stripe/webhook` → event
   `checkout.session.completed` → copy its **Signing secret** → add it in Render as
   `STRIPE_WEBHOOK_SECRET`.

A "Pay with card" button then appears automatically on unpaid orders. Until you do
this, clients pay you via the manual methods and you mark orders **Paid** in the dashboard.

---

## Troubleshooting

- **Build failed:** Render → your service → **Logs**. Usually a missing env var.
- **"Application error" / 502 on first hit:** it was asleep — wait ~30s and refresh.
- **DB errors:** double-check the `DATABASE_URL` is the full Neon string.
- **Forgot admin password:** change `ADMIN_PASSWORD` in Render → Environment → redeploy.
