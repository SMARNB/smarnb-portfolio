"""Unified outbound email — invoices, receipts and promotional campaigns.

Reusable by design (this module + models.EmailLog + the Setting row can be lifted
into any project): a single ``send()`` with HTML + attachments, two transports,
a DB-overridable sender identity, and per-send logging.

Transports (first configured one wins):
  • SendGrid HTTPS API — the one that works on Render (Render blocks outbound
    SMTP ports 25/465/587 on every plan, so raw SMTP can't leave the instance).
  • Generic SMTP (stdlib smtplib) — for local runs and hosts that allow SMTP;
    supports tls/ssl/none via SMTP_SECURITY.

INERT until a transport + a from-address exist — send() just returns False and
the app behaves as before. The sender identity (from name / from email /
reply-to / owner-copy toggle / invoice footer) can be overridden from the admin
dashboard (stored in the ``settings`` table under EMAIL_SETTINGS_KEY) so the
owner can move to their own domain later without a code change; secrets (API
key / SMTP password) stay in environment variables only.

Best-effort: never raises to callers. Fire-and-forget by default; synchronous
when ``background=False`` (and always synchronous under the test capture hook).
"""
import base64
import json
import re
import asyncio
import httpx
import threading

from . import config, models

EMAIL_SETTINGS_KEY = "email_doc"

# Tests set this to a callable(dict) to capture sends synchronously (no network).
_test_capture = None

_last_error = ""


def last_error() -> str:
    return _last_error


# --- Dashboard-editable sender settings (merged over env defaults) -------------

def default_settings() -> dict:
    return {
        "from_name": config.EMAIL_FROM_NAME or "SMARNB",
        "from_email": config.EMAIL_FROM or "",
        "reply_to": config.EMAIL_REPLY_TO or "",
        "bcc_owner": True,          # send the owner a copy of every invoice
        "invoice_footer": ("Pay via Raast / SadaPay: 0324 2225073 · JazzCash: MC815133. "
                           "Questions? Just reply to this email."),
        "promo_footer": "You're receiving this because you have an account at smarnb.onrender.com.",
    }


def get_settings(db) -> dict:
    doc = default_settings()
    row = db.get(models.Setting, EMAIL_SETTINGS_KEY)
    if row and row.value:
        try:
            stored = json.loads(row.value)
            if isinstance(stored, dict):
                doc.update({k: v for k, v in stored.items() if k in doc})
        except Exception:
            pass
    return doc


def save_settings(db, data: dict) -> dict:
    doc = get_settings(db)
    doc.update({k: v for k, v in (data or {}).items() if k in doc})
    row = db.get(models.Setting, EMAIL_SETTINGS_KEY)
    if not row:
        row = models.Setting(key=EMAIL_SETTINGS_KEY, value="{}")
        db.add(row)
    row.value = json.dumps(doc)
    db.commit()
    return doc


# --- Transport state ------------------------------------------------------------

def transport() -> str:
    """Which transport would be used: 'test' | 'sendgrid' | 'brevo' | ''(off)."""
    if _test_capture:
        return "test"
    if config.SENDGRID_API_KEY:
        return "sendgrid"
    if config.BREVO_API_KEY:
        return "brevo"
    return ""


def enabled(db=None) -> bool:
    """True once a transport AND a from-address exist (env or dashboard)."""
    if _test_capture:
        return True
    if not transport():
        return False
    if config.EMAIL_FROM:
        return True
    if db is not None:
        return bool(get_settings(db).get("from_email"))
    return False


def status(db) -> dict:
    """For the admin Email tab: what's configured, without leaking secrets."""
    doc = get_settings(db)
    return {
        "enabled": enabled(db),
        "transport": transport() or "none",
        "sendgrid_configured": bool(config.SENDGRID_API_KEY),
        "brevo_configured": bool(config.BREVO_API_KEY),
        "env_from": config.EMAIL_FROM or "",
        "settings": doc,
        "note": ("Render blocks outbound SMTP ports, so on the live site use the "
                 "SendGrid or Brevo transport (SENDGRID_API_KEY/BREVO_API_KEY + EMAIL_FROM env vars)."),
    }


# --- Sending ---------------------------------------------------------------------

def _text_from_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def _send_sendgrid(msg: dict) -> bool:
    import urllib.request
    personalization = {"to": [{"email": msg["to"]}]}
    if msg.get("bcc") and msg["bcc"].lower() != msg["to"].lower():
        personalization["bcc"] = [{"email": msg["bcc"]}]
    payload = {
        "personalizations": [personalization],
        "from": {"email": msg["from_email"], "name": msg["from_name"]},
        "subject": msg["subject"],
        "content": [
            {"type": "text/plain", "value": msg["text"]},
            {"type": "text/html", "value": msg["html"]},
        ],
    }
    if msg.get("reply_to"):
        payload["reply_to"] = {"email": msg["reply_to"]}
    if msg.get("attachments"):
        payload["attachments"] = [
            {"content": base64.b64encode(blob).decode("ascii"),
             "filename": name, "type": mime, "disposition": "attachment"}
            for (name, blob, mime) in msg["attachments"]
        ]
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + config.SENDGRID_API_KEY,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return 200 <= getattr(resp, "status", 200) < 300


async def _send_brevo(msg: dict) -> bool:
    import email.utils
    parsed_name, parsed_email = email.utils.parseaddr(msg["from_email"])
    sender_email = parsed_email if parsed_email else msg["from_email"]
    sender_name = parsed_name if parsed_name else msg["from_name"]

    payload = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": [{"email": msg["to"]}],
        "subject": msg["subject"],
        "htmlContent": msg["html"],
        "textContent": msg["text"],
    }
    if msg.get("bcc") and msg["bcc"].lower() != msg["to"].lower():
        payload["bcc"] = [{"email": msg["bcc"]}]
    if msg.get("reply_to"):
        payload["replyTo"] = {"email": msg["reply_to"]}
    if msg.get("attachments"):
        payload["attachment"] = [
            {"content": base64.b64encode(blob).decode("ascii"), "name": name}
            for (name, blob, mime) in msg["attachments"]
        ]
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={
                "api-key": config.BREVO_API_KEY,
                "accept": "application/json",
                "content-type": "application/json"
            },
            timeout=20.0
        )
        resp.raise_for_status()
        return True


def _log(db, kind: str, to: str, subject: str, ok: bool, error: str = ""):
    if db is None:
        return
    try:
        db.add(models.EmailLog(kind=kind, to_email=to, subject=subject[:300],
                               ok=ok, error=(error or "")[:300]))
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def _deliver(msg: dict) -> bool:
    global _last_error
    _last_error = ""
    try:
        if _test_capture:
            _test_capture(msg)
            return True
        t = transport()
        if t == "sendgrid":
            return _send_sendgrid(msg)
        if t == "brevo":
            return asyncio.run(_send_brevo(msg))
        _last_error = "no email transport configured"
        return False
    except Exception as e:
        _last_error = str(e)[:300]
        return False


def send(db, to: str, subject: str, html: str, *, text: str = "",
         attachments=None, kind: str = "other", bcc_owner: bool = False,
         background: bool = True) -> bool:
    """Send one email. Returns False (never raises) when email is off or fails.
    `db` is used for sender settings + the EmailLog row; sends run in a daemon
    thread unless background=False (the test capture is always synchronous)."""
    if not to:
        return False
    doc = get_settings(db) if db is not None else default_settings()
    from_email = doc.get("from_email") or config.EMAIL_FROM
    if not (_test_capture or (transport() and from_email)):
        return False
    msg = {
        "to": to,
        "subject": subject,
        "html": html,
        "text": text or _text_from_html(html),
        "from_email": from_email,
        "from_name": doc.get("from_name") or config.EMAIL_FROM_NAME,
        "reply_to": doc.get("reply_to") or "",
        "bcc": (config.OWNER_EMAIL if (bcc_owner and doc.get("bcc_owner", True)) else ""),
        "attachments": attachments or [],
        "kind": kind,
    }
    if _test_capture or not background:
        ok = _deliver(msg)
        _log(db, kind, to, subject, ok, "" if ok else _last_error)
        return ok

    def _bg():
        ok = _deliver(msg)
        # Background sends get their own session for the log row.
        try:
            from .database import SessionLocal
            bg_db = SessionLocal()
            try:
                _log(bg_db, kind, to, subject, ok, "" if ok else _last_error)
            finally:
                bg_db.close()
        except Exception:
            pass

    threading.Thread(target=_bg, daemon=True).start()
    return True
