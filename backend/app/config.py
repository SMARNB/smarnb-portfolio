"""App configuration. Reads from environment (or a local backend/.env file)."""
import os

_APP_DIR = os.path.dirname(os.path.abspath(__file__))      # backend/app
BACKEND_DIR = os.path.dirname(_APP_DIR)                     # backend/
SITE_DIR = os.path.dirname(BACKEND_DIR)                     # portfolio/  (the static site root)


def _load_dotenv(path):
    """Minimal .env loader so we don't need an extra dependency."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv(os.path.join(BACKEND_DIR, ".env"))

# --- Security -----------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))  # 7 days

# Encryption-at-rest key for PII. If empty, derived from SECRET_KEY.
# Generate a dedicated one with: python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")

# Login brute-force throttle (per IP)
LOGIN_MAX_ATTEMPTS = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "8"))
LOGIN_WINDOW_SECONDS = int(os.environ.get("LOGIN_WINDOW_SECONDS", str(15 * 60)))

# --- Database -----------------------------------------------------------------
# Default: SQLite file next to the backend. For production set DATABASE_URL to a
# persistent Postgres (e.g. a free Neon database): postgresql+pg8000://user:pass@host/db
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(BACKEND_DIR, "portfolio.db"))
# Accept a plain Neon/Postgres URL as-is and route it through the bundled
# pure-python driver (pg8000) so no compiler/libpq is needed on the host.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+pg8000://" + DATABASE_URL[len("postgres://"):]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+pg8000://" + DATABASE_URL[len("postgresql://"):]

# --- Seeded admin (the developer) --------------------------------------------
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "shahjee975@gmail.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin12345")   # ⚠️ change via env in production
ADMIN_NAME = os.environ.get("ADMIN_NAME", "Muhammad Ali Raza")

# --- Contact (used by the chat assistant for common-language answers) ---------
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", ADMIN_EMAIL)
CONTACT_WHATSAPP = os.environ.get("CONTACT_WHATSAPP", "")   # e.g. +92 324 2225073
LOCATION = os.environ.get("LOCATION", "Pakistan · working with clients worldwide (remote)")

# --- Owner WhatsApp pings (OPTIONAL) ------------------------------------------
# The bot can ping YOU on WhatsApp (with the chat/client id) when a visitor asks
# for a human or places an order. OFF until a sender is configured below.
# Recipient defaults to CONTACT_WHATSAPP. Choose ONE sender:
#   • CallMeBot (easiest, free): message the CallMeBot number once to get an API
#     key, then set CALLMEBOT_APIKEY. https://www.callmebot.com/blog/free-api-whatsapp-messages/
#   • WhatsApp Cloud API (official, Meta): set WHATSAPP_TOKEN + WHATSAPP_PHONE_ID.
OWNER_WHATSAPP = os.environ.get("OWNER_WHATSAPP", CONTACT_WHATSAPP)
CALLMEBOT_APIKEY = os.environ.get("CALLMEBOT_APIKEY", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
WHATSAPP_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v21.0")
# Webhook verify token you invent and paste into Meta's webhook config; gates the
# WhatsApp <-> site chat two-way bridge (RECEIVE side). Bridge is inert until the
# token + WHATSAPP_TOKEN + WHATSAPP_PHONE_ID are all set.
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")

# --- Misc ---------------------------------------------------------------------
CURRENCY = os.environ.get("CURRENCY", "$")
CURRENCY_CODE = os.environ.get("CURRENCY_CODE", "usd").lower()   # ISO code for Stripe
# Comma-separated allowed origins for the browser API (use your domains in prod).
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()] or ["*"]

# --- Stripe (OPTIONAL) --------------------------------------------------------
# Card payments stay OFF until you set STRIPE_SECRET_KEY (no cost / no footprint
# until then). Add the key later + `pip install stripe` to switch it on.
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
# Used to build Stripe success/cancel redirect URLs (e.g. https://smarnb.onrender.com).
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")

# --- Safepay (OPTIONAL — Pakistan card/wallet gateway) ------------------------
# Safepay ("the Stripe of Pakistan") settles card + wallet payments into YOUR bank
# account. It stays completely OFF (no external calls, no UI) until SAFEPAY_API_KEY
# is set — the flow is a hosted redirect (the buyer pays on getsafepay.com), so our
# strict first-party CSP is untouched (no third-party script runs on our origin).
# Sign up at getsafepay.com, complete KYC, and paste the API key here (as a Render
# env secret). Your bank details go in Safepay's own dashboard, never in this app.
SAFEPAY_API_KEY = os.environ.get("SAFEPAY_API_KEY", "")          # public/client key ("sec_…")
SAFEPAY_WEBHOOK_SECRET = os.environ.get("SAFEPAY_WEBHOOK_SECRET", "")  # optional, for signed webhooks
# Merchant SECRET key (Safepay dashboard → Developer → API → "Secret key").
# OPTIONAL: unlocks the EMBEDDED checkout — the payment form renders inside our own
# page (an iframe of Safepay's /embedded app; card data still never touches us).
# It authenticates the server-side TBT (passport) call. Without it the flow simply
# stays a hosted redirect.
# ⚠ Keys come as a PAIR: regenerating ("Update key") rotates BOTH halves. Always
# copy the Public key into SAFEPAY_API_KEY and the Secret key here from the SAME
# dashboard page at the same time — a mixed pair makes the embedded app fail with
# "cannot find tracker … using keys" (checkout then auto-falls back to hosted).
SAFEPAY_SECRET_KEY = os.environ.get("SAFEPAY_SECRET_KEY", "")
SAFEPAY_ENVIRONMENT = (os.environ.get("SAFEPAY_ENVIRONMENT", "sandbox") or "sandbox").lower()  # sandbox | production
SAFEPAY_CURRENCY = os.environ.get("SAFEPAY_CURRENCY", "PKR").upper()   # Safepay settles in PKR
# Safepay's /order/v1/init takes the amount in the major unit (rupees) — the
# reference integration sends e.g. 1000.00 for PKR 1,000. If a sandbox test charge
# comes through at the wrong scale, set this to 100 (paisa) — no code change needed.
# ALWAYS verify with a sandbox test charge before going live.
SAFEPAY_AMOUNT_MULTIPLIER = int(os.environ.get("SAFEPAY_AMOUNT_MULTIPLIER", "1") or "1")
# The store prices in USD (CURRENCY_CODE) but Safepay charges PKR, so totals are
# converted server-side before charging. SAFEPAY_FX_RATE pins the rate manually
# (e.g. 280); 0 = use a live rate (open.er-api.com, cached 6h). If no rate can be
# determined, card checkout fails with a clear error — it never charges 1:1.
# SAFEPAY_FX_MARGIN_PCT adds an optional % buffer against rate movement (e.g. 2).
SAFEPAY_FX_RATE = float(os.environ.get("SAFEPAY_FX_RATE", "0") or "0")
SAFEPAY_FX_MARGIN_PCT = float(os.environ.get("SAFEPAY_FX_MARGIN_PCT", "0") or "0")
# API + hosted-checkout hosts. Defaults follow Safepay's sandbox/production split;
# override only if Safepay changes them (so we never need a code edit).
_sfpy_sandbox = SAFEPAY_ENVIRONMENT != "production"
SAFEPAY_API_BASE = (os.environ.get("SAFEPAY_API_BASE", "")
                    or ("https://sandbox.api.getsafepay.com" if _sfpy_sandbox
                        else "https://api.getsafepay.com")).rstrip("/")
# The hosted-checkout base includes the full /checkout/pay path (per Safepay's
# official SDK: sandbox.api.getsafepay.com/checkout/pay | getsafepay.com/checkout/pay).
# NB: the older community "/components" host 301s to the marketing site — don't use it.
SAFEPAY_CHECKOUT_BASE = (os.environ.get("SAFEPAY_CHECKOUT_BASE", "")
                         or ("https://sandbox.api.getsafepay.com/checkout/pay" if _sfpy_sandbox
                             else "https://getsafepay.com/checkout/pay")).rstrip("/")
# The embeddable checkout app (rendered in an iframe on OUR page when the secret
# key is set). Per Safepay's PHP SDK: {host}/embedded?environment&tracker&tbt&….
SAFEPAY_EMBED_BASE = (os.environ.get("SAFEPAY_EMBED_BASE", "")
                      or ("https://sandbox.api.getsafepay.com/embedded" if _sfpy_sandbox
                          else "https://getsafepay.com/embedded")).rstrip("/")

# --- Email (SendGrid, OPTIONAL) — powers account/email verification ----------
# Verification + security emails go over SendGrid's HTTPS API because Render blocks
# outbound SMTP ports on every plan. UNTIL SENDGRID_API_KEY + EMAIL_FROM are set,
# email verification stays INACTIVE and the site behaves exactly as before (no new
# gating) so nothing breaks. EMAIL_FROM must be a SendGrid-verified sender.
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", ADMIN_NAME or "SMARNB")
EMAIL_VERIFY_TTL_MIN = int(os.environ.get("EMAIL_VERIFY_TTL_MIN", "15"))
EMAIL_VERIFY_MAX_ATTEMPTS = int(os.environ.get("EMAIL_VERIFY_MAX_ATTEMPTS", "6"))

# --- Two-factor auth (TOTP) ---------------------------------------------------
# Optional for clients (opt-in), required for the admin. Works with Google
# Authenticator, Microsoft Authenticator, Authy, etc. (standard RFC-6238).
TOTP_ISSUER = os.environ.get("TOTP_ISSUER", "SMARNB")
ADMIN_2FA_REQUIRED = (os.environ.get("ADMIN_2FA_REQUIRED", "1") or "1").lower() not in ("0", "false", "no")
