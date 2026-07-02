"""Time-based one-time passwords (RFC 6238) — the standard behind Google
Authenticator, Microsoft Authenticator, Authy, 1Password, etc.

Pure stdlib (hmac/hashlib/struct/base64) so there's no third-party dependency for
the crypto. A QR code (for scanning the setup URI) is rendered with `segno` when
available; if it isn't, the caller still gets the secret + otpauth URI to enter
manually.
"""
import base64
import hmac
import hashlib
import os
import struct
import time
from urllib.parse import quote, urlencode

from . import config

_STEP = 30       # seconds per code
_DIGITS = 6


def generate_secret() -> str:
    """A fresh base32 secret (no padding) to store against the user."""
    return base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")


def _hotp(secret_b32: str, counter: int) -> str:
    pad = "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(secret_b32.upper() + pad, casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** _DIGITS)
    return str(code).zfill(_DIGITS)


def verify(secret: str, code: str, window: int = 1, at: float = None) -> bool:
    """Check a user-entered code against the secret, tolerating ±`window` steps of
    clock drift. Constant-time compare per candidate."""
    if not (secret and code):
        return False
    code = str(code).strip().replace(" ", "")
    if not (code.isdigit() and len(code) == _DIGITS):
        return False
    counter = int((at if at is not None else time.time()) // _STEP)
    for w in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret, counter + w), code):
            return True
    return False


def provisioning_uri(secret: str, account: str, issuer: str = None) -> str:
    """The otpauth:// URI an authenticator app scans."""
    issuer = issuer or config.TOTP_ISSUER
    label = quote("%s:%s" % (issuer, account))
    params = urlencode({
        "secret": secret, "issuer": issuer,
        "algorithm": "SHA1", "digits": _DIGITS, "period": _STEP,
    })
    return "otpauth://totp/%s?%s" % (label, params)


def qr_svg(uri: str) -> str:
    """An inline SVG QR for the URI, or '' if segno isn't installed (the frontend
    then shows the secret + URI for manual entry)."""
    try:
        import segno
    except Exception:
        return ""
    try:
        import io
        buf = io.BytesIO()
        segno.make(uri, error="m").save(buf, kind="svg", scale=5, border=2, dark="#0f172a")
        return buf.getvalue().decode("utf-8")
    except Exception:
        return ""
