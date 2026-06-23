# Security & data protection

A plain-English rundown of how your data is protected, and the **3 things you must
set before going live**.

## What's protected
| Data | How it's protected |
|---|---|
| **Passwords** | One-way hashed (PBKDF2-SHA256, 200k iterations, per-user salt). Never stored or recoverable in plain text. |
| **Client & order PII** (names, emails, WhatsApp, order notes) | **Encrypted at rest** with Fernet (AES-128-CBC + HMAC). A database dump shows only ciphertext like `gAAAAAB…`. The key lives in your environment, not the DB. |
| **Email lookups** | A keyed **blind index** (HMAC) lets login/“my orders” still work without storing the email in the clear. |
| **Card / payment details** | **Not stored at all.** Card data is handled by the gateway (Stripe/JazzCash), which is PCI-compliant. We only store the *method chosen* (e.g. “Stripe”) and a paid/unpaid flag. |
| **Order totals** | Computed **server-side** from the catalog — a tampered client can't change the price. |
| **The whole app** | Strict Content-Security-Policy + hardening headers; static access to the backend source, `.env`, the database and `.git` is blocked (404). |
| **Sessions** | JWT bearer tokens; admin-only routes gated by role. |

## The developer dashboard is private to you
- `/admin` is a **login wall** — anyone can see the login box, nobody gets in without your admin password.
- The **admin account can't be self-registered** — it's seeded from `.env`; public sign-up only ever creates *client* accounts.
- **Login is rate-limited** (8 tries / 15 min per IP) to stop brute-force.
- Want it even more locked down? On your host (Render/Netlify/Cloudflare) you can add **IP allow-listing** so `/admin` only answers from your home/office IP. Ask me and I'll wire it for your host.

## Deliverables: preview before pay, unlock after
- Attach files to an order from the admin panel: a **Preview URL** (always visible to the client — use a watermarked/low-res/demo link) and a **Final URL** (the real product).
- The backend **withholds the Final URL** until you mark the order **Paid** — the client sees a “🔒 Unlocks after payment” badge until then. The locked link is never even sent to the browser.

## ⚠️ Before you deploy — set these 3 (in `backend/.env`)
1. **`SECRET_KEY`** — a long random string:
   `python -c "import secrets;print(secrets.token_urlsafe(48))"`
2. **`ENCRYPTION_KEY`** — a dedicated encryption key (recommended):
   `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`
   Keep it stable and backed up — if it changes, previously-encrypted data can't be decrypted.
3. **`ADMIN_PASSWORD`** — change it from the default `admin12345` to something strong.

> Tip: set these in your host's Environment Variables (Render/Railway/Fly), not in a committed file. `.env` and the database are already git-ignored.
