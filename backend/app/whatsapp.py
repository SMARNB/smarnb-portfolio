"""WhatsApp Business (Meta Cloud API) <-> site-chat bridge.

First-party and server-to-server — no page script, nothing third-party loads in the
browser. Inbound WhatsApp messages arrive on a webhook and are written into the same
Conversation/ChatMessage model the website chat uses; the developer's Inbox replies
(and the bot's auto-replies) are pushed back to WhatsApp via the Graph API.

INERT BY DEFAULT: every function below no-ops unless the credentials are set
(WHATSAPP_TOKEN + WHATSAPP_PHONE_ID to send, WHATSAPP_VERIFY_TOKEN to accept the
webhook). With them unset the bridge does nothing and the webhook rejects callers.
"""
import json
import re
import threading
import urllib.request

from . import config


def enabled():
    """True if we can SEND on WhatsApp (token + phone-number id present)."""
    return bool(config.WHATSAPP_TOKEN and config.WHATSAPP_PHONE_ID)


def webhook_ready():
    """True if the RECEIVE side is fully configured (send creds + a verify token)."""
    return bool(enabled() and config.WHATSAPP_VERIFY_TOKEN)


def _digits(s):
    return re.sub(r"\D", "", s or "")


def verify(mode, token, challenge):
    """Meta's GET webhook handshake: echo the challenge iff the verify token matches.
    Returns the challenge string to send back, or None to reject (403)."""
    vt = config.WHATSAPP_VERIFY_TOKEN
    if mode == "subscribe" and vt and token and token == vt:
        return challenge
    return None


def send_text(to, body):
    """Send a plain-text WhatsApp message to `to` (any phone format; digits are
    extracted). Returns True if dispatched. No-op (False) when not configured."""
    to = _digits(to)
    body = (body or "").strip()
    if not (enabled() and to and body):
        return False
    url = "https://graph.facebook.com/{}/{}/messages".format(
        config.WHATSAPP_API_VERSION, config.WHATSAPP_PHONE_ID)
    payload = json.dumps({
        "messaging_product": "whatsapp", "to": to,
        "type": "text", "text": {"body": body[:4000]},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": "Bearer " + config.WHATSAPP_TOKEN,
        "Content-Type": "application/json",
    })
    urllib.request.urlopen(req, timeout=8).read()
    return True


def send_text_async(to, body):
    """Fire-and-forget send so a webhook/Inbox request never blocks on Meta's API.
    Never raises into the caller. No-op when not configured."""
    if not enabled():
        return False

    def _run():
        try:
            send_text(to, body)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
    return True


def parse_messages(payload):
    """Pull inbound messages out of a webhook POST body. Returns a list of
    (wa_id, profile_name, text) tuples — one per user message. Non-text messages
    (image/audio/…) become a short placeholder so the developer still sees them and
    can reply. Status callbacks (delivered/read) and malformed entries are ignored."""
    out = []
    try:
        for entry in payload.get("entry", []) or []:
            for change in entry.get("changes", []) or []:
                value = change.get("value", {}) or {}
                names = {}
                for c in value.get("contacts", []) or []:
                    names[c.get("wa_id")] = ((c.get("profile") or {}).get("name") or "")
                for m in value.get("messages", []) or []:
                    wa = m.get("from")
                    if not wa:
                        continue
                    mtype = m.get("type")
                    if mtype == "text":
                        text = ((m.get("text") or {}).get("body") or "").strip()
                    else:
                        text = "[Sent a {} on WhatsApp]".format(mtype or "message")
                    if text:
                        out.append((wa, names.get(wa, ""), text))
    except Exception:
        pass
    return out
