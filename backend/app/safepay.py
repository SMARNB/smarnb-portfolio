"""Safepay (Pakistan) card/wallet gateway — hosted-redirect flow.

Completely INERT until ``SAFEPAY_API_KEY`` is set: no imports fire, no network
calls happen, and the frontend never shows the button. When enabled, the flow is:

  1. server creates a *tracker* (``create_tracker``) via Safepay's order API,
  2. the buyer is redirected to Safepay's own hosted checkout page
     (``checkout_url``) — so no third-party script runs on our origin and the
     strict first-party CSP is untouched,
  3. on return / via webhook the server re-verifies the tracker with Safepay
     (``verify_tracker`` → state ``TRACKER_ENDED`` and the client id matches ours)
     before the order is ever marked paid — the browser can't fake a payment.

Endpoints + the amount unit are configurable (config.SAFEPAY_*) so Safepay can
change them without a code edit. Everything is best-effort and never raises to the
caller; failures just mean "not verified / not paid".
"""
import hashlib
import hmac
import json
import urllib.request

from . import config

# Safepay's order API expects the amount in the minor unit (paisa) — same
# convention as the Stripe scaffold in this repo (unit_amount = price * 100).
# If a sandbox test charge comes through the wrong scale, set
# SAFEPAY_AMOUNT_MULTIPLIER (see config) — no code change needed.
_MULTIPLIER = int(getattr(config, "SAFEPAY_AMOUNT_MULTIPLIER", 100) or 100)
_TIMEOUT = 15


def enabled() -> bool:
    """True once the merchant API key is configured. The single on/off switch."""
    return bool(config.SAFEPAY_API_KEY)


def minor_amount(total) -> int:
    """The order total in Safepay's expected unit (paisa by default)."""
    try:
        return int(round(float(total) * _MULTIPLIER))
    except (TypeError, ValueError):
        return 0


def _post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def _get_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def create_tracker(amount_total, currency=None):
    """Create a Safepay tracker for ``amount_total`` (major unit, e.g. rupees).
    Returns the tracker/token string, or None on any failure."""
    if not enabled():
        return None
    url = config.SAFEPAY_API_BASE + "/order/v1/init"
    payload = {
        "client": config.SAFEPAY_API_KEY,
        "amount": minor_amount(amount_total),
        "currency": (currency or config.SAFEPAY_CURRENCY),
        "environment": config.SAFEPAY_ENVIRONMENT,
    }
    try:
        body = _post_json(url, payload)
    except Exception:
        return None
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        return None
    # Different Safepay versions name it token / tracker.
    return data.get("token") or data.get("tracker") or None


def checkout_url(tracker, redirect_url, cancel_url="", order_id=""):
    """The hosted checkout URL the buyer is sent to (they pay on getsafepay.com)."""
    from urllib.parse import urlencode
    params = {
        "beacon": tracker,
        "env": config.SAFEPAY_ENVIRONMENT,
        "source": "custom",
        "redirect_url": redirect_url,
    }
    if cancel_url:
        params["cancel_url"] = cancel_url
    if order_id:
        params["order_id"] = order_id
    return config.SAFEPAY_CHECKOUT_BASE + "/checkout/pay?" + urlencode(params)


def _extract(node, key):
    """Pull ``key`` from a Safepay report payload, tolerating a couple of shapes."""
    if not isinstance(node, dict):
        return None
    if key in node:
        return node[key]
    for nested in ("tracker", "order", "payment"):
        sub = node.get(nested)
        if isinstance(sub, dict) and key in sub:
            return sub[key]
    return None


def verify_tracker(tracker) -> bool:
    """Ask Safepay whether ``tracker`` is a completed payment that belongs to us.
    Mirrors the official plugin: state must be TRACKER_ENDED and the client id on
    the record must equal our API key. Returns False on any doubt/error."""
    if not (enabled() and tracker):
        return False
    url = config.SAFEPAY_API_BASE + "/order/v1/" + str(tracker)
    try:
        body = _get_json(url)
    except Exception:
        return False
    data = body.get("data") if isinstance(body, dict) else None
    state = _extract(data, "state")
    client = _extract(data, "client")
    return state == "TRACKER_ENDED" and client == config.SAFEPAY_API_KEY


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """Constant-time check of a signed webhook. If no webhook secret is configured
    this returns False (the caller then falls back to server-side tracker
    verification, which is the real source of truth anyway)."""
    secret = config.SAFEPAY_WEBHOOK_SECRET
    if not (secret and signature):
        return False
    mac = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(mac, signature.strip())
    except Exception:
        return False
