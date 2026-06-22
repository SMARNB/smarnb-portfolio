# ALIRA — Portfolio & Sales Center

A fast, accessible, secure freelance portfolio with a built-in **sales center**:
service packages, a cart, direct ordering, **order tracking**, and custom-quote
requests — all in a single static site with **zero dependencies** and **no build step**.

- ⚡ **Instant load** — no frameworks, no web fonts, no third-party scripts. Just HTML/CSS/JS.
- 📱 **Fully responsive** — phones, tablets, laptops, desktops, every size.
- ♿ **Accessible** — semantic HTML, keyboard nav, focus traps, ARIA, `prefers-reduced-motion`, AA contrast, light/dark themes.
- 🔒 **Secure** — strict Content-Security-Policy, hardened headers, no inline JS, honeypot spam trap, all user input rendered safely.
- 🛒 **Sales center** — packages → cart → checkout → order ID → live tracking. Orders reach you by **email + WhatsApp**.

---

## 1. Make it yours (5 minutes)

Open **`assets/js/config.js`** and edit the values at the top. This is the single
source of truth — change it once and the whole site updates:

| What | Where |
|------|-------|
| Your name / brand / initials | `name`, `brand`, `initials` |
| Bio, role, tagline | `role`, `tagline`, `bio` |
| Email | `email` (already set to shahjee975@gmail.com) |
| **WhatsApp number** | `whatsapp` — full international format, digits only (e.g. `14155550123`) |
| Social links | `socials` (blank ones are hidden automatically) |
| Trust stats | `stats` |

> ⚠️ I guessed your name as **"Ali Raza"** from your username — please correct it in `config.js` (and the `<title>`/meta in `index.html`).

Edit **`assets/js/data.js`** to change your **services, package prices, portfolio
projects, testimonials, and FAQ**. Prices are placeholders based on your Fiverr gigs.

Add images to **`assets/img/`** and reference them:
- Portfolio: set each project's `image` in `data.js` (leave `""` for an auto gradient).
- Your photo: replace the placeholder block in the **About** section of `index.html`.

---

## 2. Turn on order/inquiry emails (recommended, free)

Orders and custom requests already work via **WhatsApp** with no setup. To also get
them by **email**, connect a free Formspree endpoint:

1. Sign up at <https://formspree.io> and create a form.
2. Copy the form ID (the part after `/f/` in your endpoint, e.g. `xpzgkqab`).
3. Paste it into `formspreeId` in `assets/js/config.js`.

That's it — every order and custom request is now emailed to you, **and** the
visitor still gets an order ID to track. No server, no database.

> How fulfillment works: a customer places an order → it's saved in *their* browser
> so they can track it → you're notified by email + WhatsApp → you confirm details
> and payment (Fiverr, invoice, or direct) before starting. No payment is processed
> on the site, which keeps it 100% static and secure.

---

## 3. Run it locally

It's just static files — open `index.html`, or serve it (recommended, so the
security headers and fetch work as expected):

```bash
# Python (you've got it)
python -m http.server 8080
# then open http://localhost:8080
```

---

## 4. Deploy (pick one — all free)

**Netlify / Cloudflare Pages** (security headers applied automatically via `_headers`):
- Drag-and-drop this folder at <https://app.netlify.com/drop>, **or** connect a Git repo.

**GitHub Pages / Vercel** also work. Note: GitHub Pages can't set custom headers, so
your CSP/security headers won't apply there — prefer Netlify or Cloudflare Pages for
the full security posture. On Vercel, the `_headers` file isn't read; add a
`vercel.json` with the same headers (ask if you want it).

After deploying, update the domain in: `index.html` (`canonical`, `og:*`),
`robots.txt`, `sitemap.xml`, and `config.js` (`siteUrl`).

---

## 5. File map

```
portfolio/
├── index.html              # the whole site (sections + modals/drawer shells)
├── 404.html                # on-brand not-found page
├── manifest.webmanifest    # installable PWA metadata
├── robots.txt / sitemap.xml# SEO
├── _headers / netlify.toml # security + cache headers
├── README.md
└── assets/
    ├── css/styles.css      # design system, responsive, animations
    ├── js/
    │   ├── config.js       # ✏️ your details  (edit first)
    │   ├── data.js         # ✏️ services, prices, portfolio, reviews
    │   ├── store.js        # cart / orders / tracking (localStorage) + notify
    │   └── app.js          # rendering, interactions, a11y, sales flow
    ├── img/                # your images go here
    ├── favicon.svg
    └── og-image.svg        # social share image (export to PNG for best support)
```

---

## Notes & nice-to-haves
- **Order tracking is per-browser** (localStorage) — perfect for a freelance flow
  without a backend. If you later want cross-device tracking and automatic status
  updates, that needs a small backend/DB (happy to add one — you're a Python dev,
  so FastAPI + SQLite would slot in nicely).
- The `og-image.svg` looks great, but some social platforms only render PNG/JPG —
  export it to `og-image.png` and update the `og:image` URL for guaranteed previews.
- Everything respects **reduced motion** and works **without JavaScript** for the
  core readable content.
