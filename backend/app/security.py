"""Password hashing (stdlib PBKDF2 — no native deps) and JWT helpers."""
import base64
import datetime as dt
import hashlib
import hmac
import os

import jwt  # PyJWT

from . import config

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        _ITERATIONS, base64.b64encode(salt).decode(), base64.b64encode(dk).decode()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_b64, hash_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iters))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def create_access_token(subject, extra: dict = None) -> str:
    now = dt.datetime.utcnow()
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + dt.timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])


def hash_token(value: str) -> str:
    """Keyed hash for short-lived secrets (email verification codes) so they're never
    stored in the clear. HMAC-SHA256 with the app secret; compared constant-time."""
    return hmac.new(config.SECRET_KEY.encode("utf-8"), (value or "").encode("utf-8"),
                    hashlib.sha256).hexdigest()


def token_matches(value: str, stored_hash: str) -> bool:
    if not (value and stored_hash):
        return False
    return hmac.compare_digest(hash_token(value), stored_hash)
