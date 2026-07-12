"""Transactional email (verification / security codes) via an HTTPS API.

Render blocks outbound SMTP ports (25/465/587) on every plan, so verification and
security emails must go over an HTTPS API. Two transports are supported — SendGrid
and Brevo — and the first configured one wins (same precedence as emailer.py).
This module is INERT until an API key and EMAIL_FROM (a sender verified with that
provider) are set — enabled() is the single switch the rest of the app checks
before enforcing verification.

Best-effort and never raises to the caller; a failure just returns False.
"""
import json
import re
import urllib.request

from . import config

_SENDGRID_ENDPOINT = "https://api.sendgrid.com/v3/mail/send"
_BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"
_TIMEOUT = 15
_last_error = ""


def last_error() -> str:
    return _last_error


def transport() -> str:
    """Which transport would be used: 'sendgrid' | 'brevo' | ''(off)."""
    if config.SENDGRID_API_KEY:
        return "sendgrid"
    if config.BREVO_API_KEY:
        return "brevo"
    return ""


def enabled() -> bool:
    """True once a transport is configured. Until then, email verification is off
    and the site keeps its previous (no-verification) behaviour so nothing breaks."""
    return bool(transport() and config.EMAIL_FROM)


def _text_from_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def _post(url: str, payload: dict, headers: dict) -> bool:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return 200 <= getattr(resp, "status", 200) < 300


def send_email(to: str, subject: str, html: str, text: str = "") -> bool:
    """Send one transactional email. Returns True on a 2xx from the provider."""
    global _last_error
    _last_error = ""
    t = transport()
    if not (t and config.EMAIL_FROM):
        _last_error = "email not configured (SENDGRID_API_KEY/BREVO_API_KEY / EMAIL_FROM missing)"
        return False
    text = text or _text_from_html(html)
    try:
        if t == "sendgrid":
            return _post(_SENDGRID_ENDPOINT, {
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": config.EMAIL_FROM, "name": config.EMAIL_FROM_NAME},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": text},
                    {"type": "text/html", "value": html},
                ],
            }, {"Authorization": "Bearer " + config.SENDGRID_API_KEY})
        return _post(_BREVO_ENDPOINT, {
            "sender": {"email": config.EMAIL_FROM, "name": config.EMAIL_FROM_NAME},
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html,
            "textContent": text,
        }, {"api-key": config.BREVO_API_KEY, "accept": "application/json"})
    except Exception as e:  # HTTPError (4xx/5xx), URLError, timeout…
        snippet = ""
        try:
            snippet = e.read().decode("utf-8", "replace")[:200]  # type: ignore[attr-defined]
        except Exception:
            pass
        _last_error = "%s error: %s%s" % (t, e, (" — " + snippet) if snippet else "")
        return False
