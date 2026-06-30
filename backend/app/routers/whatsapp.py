"""WhatsApp Business (Meta Cloud API) webhook — the RECEIVE side of the bridge.

  GET  /api/whatsapp/webhook   Meta's verification handshake (echoes hub.challenge).
  POST /api/whatsapp/webhook   Inbound messages → written to the chat model; the bot
                               auto-replies (forwarded to WhatsApp) unless a human has
                               taken the thread over, in which case the owner is pinged.

INERT until WHATSAPP_TOKEN + WHATSAPP_PHONE_ID + WHATSAPP_VERIFY_TOKEN are set: the
GET handshake rejects everyone, and POSTs are acknowledged (200, as Meta requires) but
do nothing. No browser/page involvement — this is pure server-to-server.
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .. import crud, notify, whatsapp
from ..database import get_db
from ..routers.chat import _run_bot

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query("", alias="hub.mode"),
    hub_verify_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
):
    """Meta calls this once when you save the webhook. We echo the challenge only if
    the verify token matches the one you configured (and the bridge is set up)."""
    challenge = whatsapp.verify(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        return PlainTextResponse("Verification failed", status_code=403)
    return PlainTextResponse(challenge)


@router.post("/webhook")
async def inbound_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive WhatsApp message events. Always returns 200 quickly so Meta doesn't
    retry/disable the webhook; processing is best-effort and never raises."""
    if not whatsapp.webhook_ready():
        return {"status": "ignored"}  # bridge not configured
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}

    for wa_id, name, text in whatsapp.parse_messages(payload):
        try:
            conv, created = crud.get_or_create_whatsapp_conversation(db, wa_id, name)
            crud.add_message(db, conv, "client", text)
            if created:
                notify.notify_owner(
                    "📱 New WhatsApp chat on SMARNB.\n"
                    "Chat id: {}\nFrom: {}\nThey said: \"{}\"".format(
                        conv.public_id, name or wa_id, text[:160]))
            if conv.human_takeover:
                # A human owns this thread — don't auto-reply, just nudge the owner.
                notify.notify_owner(
                    "📱 WhatsApp reply on chat {}: \"{}\"".format(conv.public_id, text[:160]))
            else:
                for line in _run_bot(db, conv, text):
                    whatsapp.send_text_async(wa_id, line)
        except Exception:
            db.rollback()  # one bad message must not drop the whole batch
            continue
    return {"status": "ok"}
