"""Transactional email via SendGrid's HTTPS API.

Render blocks outbound SMTP ports (25/465/587) on every plan, so verification and
security emails must go over an HTTPS API. This module is INERT until both
SENDGRID_API_KEY and EMAIL_FROM (a SendGrid-verified sender) are set — enabled()
is the single switch the rest of the app checks before enforcing verification.

Best-effort and never raises to the caller; a failure just returns False.
"""
import json
import re
import urllib.request

from . import config

_ENDPOINT = "https://api.sendgrid.com/v3/mail/send"
_TIMEOUT = 15
_last_error = ""


def last_error() -> str:
    return _last_error


def enabled() -> bool:
    """True once SendGrid is configured. Until then, email verification is off and
    the site keeps its previous (no-verification) behaviour so nothing breaks."""
    return bool(config.SENDGRID_API_KEY and config.EMAIL_FROM)


def _text_from_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def send_email(to: str, subject: str, html: str, text: str = "") -> bool:
    """Send one transactional email. Returns True on a 2xx from SendGrid."""
    global _last_error
    _last_error = ""
    if not enabled():
        _last_error = "email not configured (SENDGRID_API_KEY / EMAIL_FROM missing)"
        return False
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": config.EMAIL_FROM, "name": config.EMAIL_FROM_NAME},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text or _text_from_html(html)},
            {"type": "text/html", "value": html},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _ENDPOINT, data=data, method="POST",
        headers={"Authorization": "Bearer " + config.SENDGRID_API_KEY,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except Exception as e:  # HTTPError (4xx/5xx), URLError, timeout…
        snippet = ""
        try:
            snippet = e.read().decode("utf-8", "replace")[:200]  # type: ignore[attr-defined]
        except Exception:
            pass
        _last_error = "SendGrid error: %s%s" % (e, (" — " + snippet) if snippet else "")
        return False
