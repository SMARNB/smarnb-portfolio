"""Security features: disposable-email blocking, email verification + order gating,
and TOTP two-factor auth (optional clients / required admin).

Email sending is monkeypatched (no real network); verification is toggled by
setting the SendGrid config at runtime, exactly as enabling it in production would.

Run:  .venv/Scripts/python test_security.py
"""
import os
import re
import tempfile
import time

_DB = os.path.join(tempfile.gettempdir(), "portfolio_security_test.db")
if os.path.exists(_DB):
    os.remove(_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _DB
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "test-admin-123"
# Neutralize any real email creds from backend/.env — config's dotenv setdefault
# would refill popped keys, so set them to empty instead.
for _var in ("SENDGRID_API_KEY", "BREVO_API_KEY", "SMTP_HOST", "EMAIL_FROM"):
    os.environ[_var] = ""

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app import config, email_send, seo as _seo, totp  # noqa: E402

_seo.STATIC_DIR = None  # don't touch the dev dist

# Capture verification emails instead of sending them.
_sent = []
email_send.send_email = lambda to, subject, html, text="": (_sent.append((to, subject, html, text)) or True)

ok = 0
fail = 0


def check(name, cond):
    global ok, fail
    ok += 1 if cond else 0
    fail += 0 if cond else 1
    print("  [PASS]" if cond else "  [FAIL]", name)


def code_from_last_email():
    return re.search(r"\b(\d{6})\b", _sent[-1][3]).group(1)


ORDER = {"customer_name": "Buyer", "customer_email": "buyer@example.com",
         "items": [{"service": "X", "tier": "Y", "price": 10, "qty": 1}]}

with TestClient(app) as c:
    print("== Disposable-email blocking (always on) ==")
    check("throwaway domain blocked at register",
          c.post("/api/auth/register", json={"email": "x@mailinator.com", "password": "secret123"}).status_code == 400)
    check("throwaway subdomain blocked",
          c.post("/api/auth/register", json={"email": "x@foo.guerrillamail.com", "password": "secret123"}).status_code == 400)
    check("disposable order email blocked",
          c.post("/api/orders", json={**ORDER, "customer_email": "z@10minutemail.com"}).status_code == 400)

    print("== Verification INACTIVE until email is configured (no breakage) ==")
    r = c.post("/api/auth/register", json={"email": "inert@example.com", "password": "secret123"}).json()
    check("no verification required when email off", r.get("verification_required") is False)
    check("account auto-verified when email off", r["user"]["email_verified"] is True)
    check("guest order allowed when verification off",
          c.post("/api/orders", json=ORDER).status_code == 200)

    print("== Turn email verification ON (as configuring SendGrid would) ==")
    config.SENDGRID_API_KEY = "test-key"
    config.EMAIL_FROM = "no-reply@smarnb.test"
    check("email now enabled", email_send.enabled() is True)

    _sent.clear()
    r = c.post("/api/auth/register", json={"email": "buyer@example.com", "password": "secret123", "name": "Buyer"})
    body = r.json()
    check("register ok", r.status_code == 200)
    check("verification required", body.get("verification_required") is True)
    check("user starts unverified", body["user"]["email_verified"] is False)
    H = {"Authorization": "Bearer " + body["access_token"]}
    check("a code email was sent to the user", len(_sent) == 1 and _sent[0][0] == "buyer@example.com")
    the_code = code_from_last_email()

    print("== Order gating on verification ==")
    check("unverified client can't order (403)", c.post("/api/orders", json=ORDER, headers=H).status_code == 403)
    check("guest can't order when verification on (401)", c.post("/api/orders", json=ORDER).status_code == 401)

    print("== Verify the email ==")
    check("wrong code rejected", c.post("/api/auth/verify", json={"code": "000000"}, headers=H).status_code == 400)
    rv = c.post("/api/auth/verify", json={"code": the_code}, headers=H)
    check("correct code verifies", rv.status_code == 200 and rv.json()["email_verified"] is True)
    check("verified client can now order", c.post("/api/orders", json=ORDER, headers=H).status_code == 200)

    print("== TOTP two-factor ==")
    _sent.clear()
    r2 = c.post("/api/auth/register", json={"email": "tfa@example.com", "password": "secret123"}).json()
    H2 = {"Authorization": "Bearer " + r2["access_token"]}
    c.post("/api/auth/verify", json={"code": code_from_last_email()}, headers=H2)

    s = c.post("/api/auth/2fa/setup", headers=H2).json()
    check("2fa setup returns secret + otpauth + QR",
          bool(s["secret"]) and s["otpauth_uri"].startswith("otpauth://totp/") and "<svg" in s["qr_svg"])
    secret = s["secret"]
    check("enable rejects a wrong code",
          c.post("/api/auth/2fa/enable", json={"code": "000000"}, headers=H2).status_code == 400)
    re2 = c.post("/api/auth/2fa/enable", json={"code": totp._hotp(secret, int(time.time() // 30))}, headers=H2)
    check("2fa enabled with a valid code", re2.status_code == 200 and re2.json()["totp_enabled"] is True)

    print("== Login now needs the second factor ==")
    l1 = c.post("/api/auth/login", json={"email": "tfa@example.com", "password": "secret123"}).json()
    check("login asks for the code", l1.get("totp_required") is True and not l1.get("access_token"))
    check("login rejects a wrong code",
          c.post("/api/auth/login", json={"email": "tfa@example.com", "password": "secret123", "totp_code": "000000"}).status_code == 401)
    l2 = c.post("/api/auth/login", json={"email": "tfa@example.com", "password": "secret123",
                                         "totp_code": totp._hotp(secret, int(time.time() // 30))})
    check("login succeeds with the code", l2.status_code == 200 and bool(l2.json().get("access_token")))
    check("client can turn 2fa off with password",
          c.post("/api/auth/2fa/disable", json={"password": "secret123"}, headers=H2).json()["totp_enabled"] is False)

    print("== Admin 2FA is required ==")
    la = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-admin-123"}).json()
    check("admin login flags must_setup_2fa", la.get("must_setup_2fa") is True)
    AH = {"Authorization": "Bearer " + la["access_token"]}
    sa = c.post("/api/auth/2fa/setup", headers=AH).json()
    c.post("/api/auth/2fa/enable", json={"code": totp._hotp(sa["secret"], int(time.time() // 30))}, headers=AH)
    check("admin cannot disable 2fa",
          c.post("/api/auth/2fa/disable", json={"password": "test-admin-123"}, headers=AH).status_code == 403)

print("\n==== RESULT: %d passed, %d failed ====" % (ok, fail))
if os.path.exists(_DB):
    try:
        os.remove(_DB)
    except Exception:
        pass
raise SystemExit(1 if fail else 0)
