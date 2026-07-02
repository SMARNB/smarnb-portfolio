import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import config, crud, email_guard, email_send, schemas, security, totp
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Simple in-memory brute-force throttle (per IP). Resets on success.
_attempts = {}
_RESEND_COOLDOWN = 60  # seconds between verification-code emails


def _check_rate(ip):
    now = time.time()
    fails = [t for t in _attempts.get(ip, []) if now - t < config.LOGIN_WINDOW_SECONDS]
    _attempts[ip] = fails
    if len(fails) >= config.LOGIN_MAX_ATTEMPTS:
        raise HTTPException(429, "Too many attempts. Please wait a few minutes and try again.")


def _record_fail(ip):
    _attempts.setdefault(ip, []).append(time.time())


def _verification_active() -> bool:
    """Email verification is enforced only once SendGrid is configured, so the site
    keeps working (no new gating) until the owner sets it up."""
    return email_send.enabled()


def _send_code(email: str, code: str) -> bool:
    ttl = config.EMAIL_VERIFY_TTL_MIN
    brand = config.TOTP_ISSUER
    html = (
        '<div style="font-family:Inter,Segoe UI,Arial,sans-serif;max-width:480px;margin:auto;'
        'padding:28px;border:1px solid #e6e8ee;border-radius:14px;color:#0f172a">'
        '<h2 style="margin:0 0 6px">Verify your email</h2>'
        '<p style="color:#475569;margin:0 0 18px">Enter this code to confirm your email for '
        + brand + ".</p>"
        '<div style="font-size:34px;font-weight:800;letter-spacing:8px;background:#f1f5f9;'
        'border-radius:12px;padding:16px;text-align:center">' + code + "</div>"
        '<p style="color:#94a3b8;font-size:13px;margin:18px 0 0">This code expires in '
        + str(ttl) + " minutes. If you didn't request it, you can ignore this email.</p></div>"
    )
    text = "Your %s verification code is %s (valid %d minutes)." % (brand, code, ttl)
    return email_send.send_email(email, "Your %s verification code" % brand, html, text)


# --- Registration + email verification ---------------------------------------
@router.post("/register", response_model=schemas.Token)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, data.email):
        raise HTTPException(400, "An account with this email already exists — try logging in.")
    # Reject throwaway / non-deliverable addresses before creating anything.
    err = email_guard.check(data.email)
    if err:
        raise HTTPException(400, err)

    active = _verification_active()
    # If verification is on, the account starts unverified and must confirm a code.
    user = crud.create_user(db, data.email, data.password, data.name, data.whatsapp,
                            role="client", email_verified=(not active))
    if active:
        code = crud.set_verification_code(db, user)
        _send_code(data.email, code)  # best-effort; user can hit "resend"

    token = security.create_access_token(user.id, {"role": user.role})
    return {"access_token": token, "user": user,
            "verification_required": active and not user.email_verified}


@router.post("/verify", response_model=schemas.UserOut)
def verify_email(data: schemas.VerifyEmailIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ok, err = crud.check_verification_code(db, user, data.code)
    if not ok:
        raise HTTPException(400, err)
    return user


@router.post("/resend", response_model=schemas.UserOut)
def resend_code(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.email_verified:
        return user
    if not _verification_active():
        raise HTTPException(503, "Email verification isn't enabled yet.")
    if crud.seconds_since_last_code(user) < _RESEND_COOLDOWN:
        raise HTTPException(429, "Please wait a moment before requesting another code.")
    code = crud.set_verification_code(db, user)
    _send_code(user.email, code)
    return user


# --- Login (with optional second factor) -------------------------------------
@router.post("/login", response_model=schemas.LoginResult)
def login(data: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "?"
    _check_rate(ip)
    user = crud.get_user_by_email(db, data.email)
    if not user or not security.verify_password(data.password, user.hashed_password):
        _record_fail(ip)
        raise HTTPException(401, "Wrong email or password.")

    # Second factor, when the account has it enabled.
    if user.totp_enabled:
        if not data.totp_code:
            return {"totp_required": True}
        if not totp.verify(user.totp_secret, data.totp_code):
            _record_fail(ip)
            raise HTTPException(401, "Invalid authentication code.")

    _attempts.pop(ip, None)  # success → clear failures
    token = security.create_access_token(user.id, {"role": user.role})
    must_setup = (user.role == "admin" and config.ADMIN_2FA_REQUIRED and not user.totp_enabled)
    return {"access_token": token, "user": user, "must_setup_2fa": must_setup}


@router.get("/me", response_model=schemas.UserOut)
def me(user=Depends(get_current_user)):
    return user


# --- Two-factor auth setup ----------------------------------------------------
@router.post("/2fa/setup")
def totp_setup(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Stage a new secret and return the QR + otpauth URI to add to an authenticator
    app. 2FA isn't active until the user confirms a code via /2fa/enable."""
    secret = totp.generate_secret()
    crud.set_totp_secret(db, user, secret)
    uri = totp.provisioning_uri(secret, user.email)
    return {"secret": secret, "otpauth_uri": uri, "qr_svg": totp.qr_svg(uri)}


@router.post("/2fa/enable", response_model=schemas.UserOut)
def totp_enable(data: schemas.TotpEnableIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.totp_secret:
        raise HTTPException(400, "Start 2FA setup first.")
    if not totp.verify(user.totp_secret, data.code):
        raise HTTPException(400, "That code isn't right — check your authenticator app and try again.")
    crud.enable_totp(db, user)
    return user


@router.post("/2fa/disable", response_model=schemas.UserOut)
def totp_disable(data: schemas.TotpDisableIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "admin" and config.ADMIN_2FA_REQUIRED:
        raise HTTPException(403, "Two-factor authentication is required for the admin account.")
    # Confirm identity with either a current code or the account password.
    ok = (data.code and totp.verify(user.totp_secret, data.code)) or \
         (data.password and security.verify_password(data.password, user.hashed_password))
    if not ok:
        raise HTTPException(400, "Enter a current 6-digit code or your password to turn off 2FA.")
    crud.disable_totp(db, user)
    return user
