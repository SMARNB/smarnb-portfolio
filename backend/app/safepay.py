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
import urllib.error
import urllib.request

from . import config

# Safepay's /order/v1/init takes the amount in the major unit (rupees) — the
# reference integration sends e.g. amount: 1000.00 for PKR 1,000. If a sandbox
# test charge comes through at the wrong scale, set SAFEPAY_AMOUNT_MULTIPLIER
# (see config) — no code change needed.
_MULTIPLIER = int(getattr(config, "SAFEPAY_AMOUNT_MULTIPLIER", 1) or 1)
_TIMEOUT = 15
# A real User-Agent — some gateways/WAFs reject the default "Python-urllib/x.y".
_UA = "SMARNB-Portfolio/1.0 (+https://smarnb.onrender.com)"

# Human-readable reason the last create_tracker/verify failed (for the 502 detail
# and dashboard diagnostics). Never contains our API key — only Safepay's response.
_last_error = ""


def last_error() -> str:
    return _last_error


def enabled() -> bool:
    """True once the merchant API key is configured. The single on/off switch."""
    return bool(config.SAFEPAY_API_KEY)


def minor_amount(total) -> int:
    """The order total in Safepay's expected unit (paisa by default)."""
    try:
        return int(round(float(total) * _MULTIPLIER))
    except (TypeError, ValueError):
        return 0


def _headers(extra=None):
    h = {"Accept": "application/json", "User-Agent": _UA}
    if extra:
        h.update(extra)
    return h


def _post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers=_headers({"Content-Type": "application/json"}))
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def _get_json(url):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def _describe_error(url, exc) -> str:
    """A short, key-free reason string from a failed HTTP call."""
    if isinstance(exc, urllib.error.HTTPError):
        snippet = ""
        try:
            snippet = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        return "Safepay returned HTTP %s at %s%s" % (exc.code, url, (" — " + snippet) if snippet else "")
    return "request to %s failed: %s" % (url, exc)


def create_tracker(amount_total, currency=None):
    """Create a Safepay tracker for ``amount_total`` (major unit, e.g. rupees).
    Returns the tracker/token string, or None on any failure (see last_error())."""
    global _last_error
    _last_error = ""
    if not enabled():
        _last_error = "Safepay is not enabled (SAFEPAY_API_KEY missing)."
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
    except Exception as e:
        _last_error = _describe_error(url, e)
        return None
    data = body.get("data") if isinstance(body, dict) else None
    token = (data.get("token") or data.get("tracker")) if isinstance(data, dict) else None
    if not token:
        _last_error = "Safepay response had no tracker token: %s" % (str(body)[:200])
    return token


def checkout_url(tracker, redirect_url, cancel_url="", order_id=""):
    """The hosted checkout URL the buyer is sent to (they pay on getsafepay.com).
    SAFEPAY_CHECKOUT_BASE already includes the full /checkout/pay path (config);
    params mirror Safepay's official SDK (beacon/env/source/order_id/redirect/cancel,
    plus webhooks=true when webhook delivery is configured)."""
    from urllib.parse import urlencode
    params = {
        "env": config.SAFEPAY_ENVIRONMENT,
        "beacon": tracker,
        "source": "custom",
        "redirect_url": redirect_url,
    }
    if cancel_url:
        params["cancel_url"] = cancel_url
    if order_id:
        params["order_id"] = order_id
    if config.SAFEPAY_WEBHOOK_SECRET:
        params["webhooks"] = "true"
    return config.SAFEPAY_CHECKOUT_BASE + "?" + urlencode(params)


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
