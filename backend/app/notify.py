"""Owner WhatsApp pings — best-effort, opt-in, no extra dependencies.

When a visitor asks for a human or places an order, the bot can notify YOU on
WhatsApp with the chat/client id so you can jump into the admin inbox. Sending is
OFF until a provider is configured (see config.py). Everything here is wrapped so
it can never block the chat request or raise into it.

Providers (first one that's configured wins):
  • WhatsApp Cloud API (Meta, official): WHATSAPP_TOKEN + WHATSAPP_PHONE_ID
  • CallMeBot (free, simplest for self-notifications): CALLMEBOT_APIKEY
Recipient: OWNER_WHATSAPP (defaults to CONTACT_WHATSAPP).
"""
import json
import re
import threading
import urllib.parse
import urllib.request

from . import config


def _digits(s):
    return re.sub(r"\D", "", s or "")


def _send_cloud(text):
    to = _digits(config.OWNER_WHATSAPP)
    if not (config.WHATSAPP_TOKEN and config.WHATSAPP_PHONE_ID and to):
        return False
    url = "https://graph.facebook.com/{}/{}/messages".format(
        config.WHATSAPP_API_VERSION, config.WHATSAPP_PHONE_ID)
    payload = json.dumps({
        "messaging_product": "whatsapp", "to": to,
        "type": "text", "text": {"body": text[:4000]},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": "Bearer " + config.WHATSAPP_TOKEN,
        "Content-Type": "application/json",
    })
    urllib.request.urlopen(req, timeout=6).read()
    return True


def _send_callmebot(text):
    to = _digits(config.OWNER_WHATSAPP)
    if not (config.CALLMEBOT_APIKEY and to):
        return False
    q = urllib.parse.urlencode({"phone": to, "text": text[:900],
                                "apikey": config.CALLMEBOT_APIKEY})
    urllib.request.urlopen("https://api.callmebot.com/whatsapp.php?" + q, timeout=8).read()
    return True


def _deliver(text):
    for fn in (_send_cloud, _send_callmebot):
        try:
            if fn(text):
                return
        except Exception:
            continue  # try the next provider, never raise


def notify_owner(text):
    """Fire-and-forget a WhatsApp ping to the owner. No-op if not configured."""
    if not (config.OWNER_WHATSAPP and (config.CALLMEBOT_APIKEY or
            (config.WHATSAPP_TOKEN and config.WHATSAPP_PHONE_ID))):
        return False
    threading.Thread(target=_deliver, args=(text,), daemon=True).start()
    return True
