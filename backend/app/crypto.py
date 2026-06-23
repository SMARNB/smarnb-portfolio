"""Application-level encryption at rest for PII.

- Sensitive fields (names, emails, WhatsApp, notes) are encrypted with Fernet
  (AES-128-CBC + HMAC) before they touch the database, and decrypted on read.
- A *blind index* (keyed HMAC) lets us still look rows up by email without
  storing the email in the clear.

Keys are derived from ENCRYPTION_KEY (or SECRET_KEY) which live in the
environment — never in the database. A DB dump therefore shows only ciphertext.

NOTE: we never store card numbers — payment gateways (Stripe/JazzCash) handle
those. This protects contact details + the chosen payment method.
"""
import base64
import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TypeDecorator, Text

from . import config


def _fernet():
    raw = (getattr(config, "ENCRYPTION_KEY", "") or "").strip()
    if raw:
        try:                       # accept a ready-made Fernet key as-is
            return Fernet(raw.encode())
        except Exception:
            base = raw             # otherwise treat it as a passphrase
    else:
        base = config.SECRET_KEY
    key = base64.urlsafe_b64encode(hashlib.sha256(("fernet:" + base).encode()).digest())
    return Fernet(key)


_FERNET = _fernet()
_BIDX_KEY = hashlib.sha256(("blind-index:" + config.SECRET_KEY).encode()).digest()


def encrypt(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    return _FERNET.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(token):
    if token is None:
        return None
    try:
        return _FERNET.decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, Exception):
        return token  # tolerate legacy plaintext / unreadable data instead of crashing


def blind_index(value):
    """Deterministic, keyed lookup token for an email (case-insensitive)."""
    if value is None:
        return None
    norm = str(value).strip().lower().encode("utf-8")
    return hmac.new(_BIDX_KEY, norm, hashlib.sha256).hexdigest()


class Encrypted(TypeDecorator):
    """A Text column that is transparently encrypted at rest."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return decrypt(value) if value is not None else None
