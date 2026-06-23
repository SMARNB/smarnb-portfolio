"""Chat: a rule-based assistant that can also be taken over live by the developer.

- Visitors start a thread and are authorised by a per-thread secret (stored in
  their browser). Logged-in clients are also matched by account.
- The bot auto-replies until the developer posts a message (human takeover).
- File sharing accepts images + PDFs only, validated by extension AND magic bytes,
  size-capped, stored in the DB, and served only to the thread's participants.
"""
import json
import re
import secrets as _secrets
import time
from typing import List, Optional

from fastapi import (APIRouter, Depends, File, Header, HTTPException, Request,
                     Response, UploadFile)
from sqlalchemy.orm import Session

from .. import bot, crud, crypto, models, schemas
from ..database import get_db
from ..deps import get_current_admin, get_optional_user

router = APIRouter(prefix="/api/chat", tags=["chat"])
admin_router = APIRouter(prefix="/api/admin/chat", tags=["chat-admin"],
                         dependencies=[Depends(get_current_admin)])

# ---- File upload limits ------------------------------------------------------
MAX_UPLOAD = 10 * 1024 * 1024          # 10 MB
# Allowed types -> (extension, magic-byte test). SVG is intentionally excluded.
_MAGIC = {
    "image/png":  (".png",  lambda b: b[:8] == b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": (".jpg",  lambda b: b[:3] == b"\xff\xd8\xff"),
    "image/gif":  (".gif",  lambda b: b[:6] in (b"GIF87a", b"GIF89a")),
    "image/webp": (".webp", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
    "application/pdf": (".pdf", lambda b: b[:5] == b"%PDF-"),
}

# ---- Simple per-thread send throttle ----------------------------------------
_sends = {}


def _throttle(public_id):
    now = time.time()
    hits = [t for t in _sends.get(public_id, []) if now - t < 60]
    if len(hits) >= 25:
        raise HTTPException(429, "You're sending messages very fast — give it a moment.")
    hits.append(now)
    _sends[public_id] = hits


def _detect_type(filename, raw):
    """Return a safe content-type only if the bytes truly match an allowed type."""
    for ctype, (_ext, test) in _MAGIC.items():
        try:
            if test(raw):
                return ctype
        except Exception:
            continue
    return None


def _safe_name(name, ctype):
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", (name or "file").rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
    base = base[:80] or "file"
    ext = _MAGIC[ctype][0]
    if not base.lower().endswith(ext):
        base = re.sub(r"\.[A-Za-z0-9]+$", "", base) + ext
    return base


def _msg_out(m):
    att = None
    if m.attachment:
        att = {"id": m.attachment.id, "filename": m.attachment.filename,
               "content_type": m.attachment.content_type, "size": m.attachment.size}
    return {"id": m.id, "sender": m.sender, "body": m.body or "",
            "created_at": m.created_at, "attachment": att}


def _thread(conv, include_secret=False):
    st = conv.state()
    return {
        "public_id": conv.public_id,
        "secret": conv.secret if include_secret else None,
        "status": conv.status,
        "human_takeover": conv.human_takeover,
        "needs_human": conv.needs_human,
        "messages": [_msg_out(m) for m in conv.messages],
        "quick_replies": st.get("_quick", []),
    }


def _authed_conv(db, public_id, secret, user):
    conv = crud.get_conversation(db, public_id)
    if not conv:
        raise HTTPException(404, "Conversation not found.")
    if user and conv.client_id == user.id:
        return conv
    if secret and conv.secret and _secrets.compare_digest(secret, conv.secret):
        return conv
    raise HTTPException(403, "Not allowed.")


def _run_bot(db, conv, text):
    state = conv.state()
    services = crud.catalog_for_bot(db)
    name = conv.customer_name or ""
    email = conv.customer_email or ""
    res = bot.respond(state, text, services, logged_in_name=name, logged_in_email=email)
    for line in res.get("messages", []):
        if line and line.strip():
            crud.add_message(db, conv, "bot", line)
    action = res.get("action")
    if action and action.get("type") == "create_order":
        _order_from_chat(db, conv, action)
    new_state = res.get("state", {}) or {}
    new_state["_quick"] = res.get("quick_replies", [])
    crud.save_state(db, conv, new_state)


def _order_from_chat(db, conv, action):
    try:
        item = schemas.OrderItem(service=action.get("service", ""), tier=action.get("tier", ""),
                                 price=float(action.get("price") or 0), qty=1)
        data = schemas.OrderCreate(
            customer_name=action.get("name", ""), customer_email=action.get("email", ""),
            customer_whatsapp="", notes=action.get("requirements", ""),
            payment_method="", items=[item])
    except Exception:
        crud.add_message(db, conv, "bot",
                         "I couldn't read that email — could you re-send a valid one so I can place the order?")
        return
    client = db.get(models.User, conv.client_id) if conv.client_id else None
    order = crud.create_order(db, data, client=client)
    if not conv.customer_email:
        conv.customer_name = action.get("name", "")
        conv.customer_email = action.get("email", "")
        conv.customer_email_bidx = crypto.blind_index(action.get("email", "")) or ""
        db.commit()
    crud.add_message(
        db, conv, "bot",
        ("🎉 All set! Your order is **{}**. You can track its progress anytime from the "
         "site (Track an order), and {} will confirm the details with you shortly.")
        .format(order.public_id, bot._dev()))


# ---- Public endpoints --------------------------------------------------------
@router.post("/start", response_model=schemas.ChatThreadOut)
def start(data: schemas.ChatStartIn, db: Session = Depends(get_db),
          user=Depends(get_optional_user)):
    conv = crud.create_conversation(db, name=data.name, email=data.email, client=user)
    crud.add_message(db, conv, "bot", bot._greeting())
    crud.save_state(db, conv, {"_quick": ["See services", "Get a quote", "Talk to a human"]})
    db.refresh(conv)
    return _thread(conv, include_secret=True)


@router.get("/{public_id}", response_model=schemas.ChatThreadOut)
def fetch(public_id: str, s: Optional[str] = None,
          x_chat_secret: Optional[str] = Header(None),
          db: Session = Depends(get_db), user=Depends(get_optional_user)):
    conv = _authed_conv(db, public_id, x_chat_secret or s, user)
    conv.client_read_at = models.utcnow()
    db.commit()
    return _thread(conv)


@router.post("/{public_id}/messages", response_model=schemas.ChatThreadOut)
def send(public_id: str, data: schemas.ChatSendIn,
         x_chat_secret: Optional[str] = Header(None),
         db: Session = Depends(get_db), user=Depends(get_optional_user)):
    conv = _authed_conv(db, public_id, x_chat_secret, user)
    if conv.status == "closed":
        conv.status = "open"
    _throttle(public_id)
    crud.add_message(db, conv, "client", data.body.strip())
    if not conv.human_takeover:
        _run_bot(db, conv, data.body.strip())
    else:
        # developer is handling this thread — just flag it for their attention
        st = conv.state(); st["_quick"] = []
        crud.save_state(db, conv, st)
    db.refresh(conv)
    return _thread(conv)


@router.post("/{public_id}/upload", response_model=schemas.ChatThreadOut)
async def upload(public_id: str, file: UploadFile = File(...),
                 x_chat_secret: Optional[str] = Header(None),
                 db: Session = Depends(get_db), user=Depends(get_optional_user)):
    conv = _authed_conv(db, public_id, x_chat_secret, user)
    _throttle(public_id)
    raw = await file.read(MAX_UPLOAD + 1)
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, "File is too large (max 10 MB).")
    if not raw:
        raise HTTPException(400, "Empty file.")
    ctype = _detect_type(file.filename, raw)
    if not ctype:
        raise HTTPException(415, "Only images (PNG, JPG, GIF, WEBP) and PDF files are allowed.")
    name = _safe_name(file.filename, ctype)
    msg = crud.add_message(db, conv, "client", "📎 " + name)
    crud.add_attachment(db, conv, msg, name, ctype, len(raw), raw)
    if not conv.human_takeover:
        crud.add_message(db, conv, "bot",
                         "Got your file — thanks! 📎 {} will review it. Anything else?".format(bot._dev()))
        st = conv.state(); st["_quick"] = ["See services", "Get a quote", "Talk to a human"]
        crud.save_state(db, conv, st)
    db.refresh(conv)
    return _thread(conv)


@router.get("/{public_id}/attachments/{att_id}")
def get_attachment(public_id: str, att_id: int, s: Optional[str] = None,
                   x_chat_secret: Optional[str] = Header(None),
                   db: Session = Depends(get_db), user=Depends(get_optional_user)):
    conv = _authed_conv(db, public_id, x_chat_secret or s, user)
    att = db.get(models.ChatAttachment, att_id)
    if not att or att.conversation_id != conv.id:
        raise HTTPException(404, "Not found.")
    disp = "inline" if att.content_type.startswith("image/") else "attachment"
    return Response(content=att.data, media_type=att.content_type, headers={
        "Content-Disposition": '{}; filename="{}"'.format(disp, att.filename),
        "Cache-Control": "private, max-age=3600",
        "X-Content-Type-Options": "nosniff",
    })


# ---- Admin (developer) inbox -------------------------------------------------
@admin_router.get("/conversations", response_model=List[schemas.ConversationSummary])
def admin_conversations(db: Session = Depends(get_db)):
    out = []
    for c in crud.list_conversations(db):
        last = c.messages[-1].body if c.messages else ""
        out.append({
            "public_id": c.public_id,
            "customer_name": c.customer_name or "",
            "customer_email": c.customer_email or "",
            "last_message": (last or "")[:80],
            "last_message_at": c.last_message_at,
            "unread": crud.conversation_unread(c, "admin_read_at", ("client",)),
            "status": c.status,
            "needs_human": c.needs_human,
            "human_takeover": c.human_takeover,
        })
    return out


@admin_router.get("/conversations/{public_id}")
def admin_thread(public_id: str, db: Session = Depends(get_db)):
    conv = crud.get_conversation(db, public_id)
    if not conv:
        raise HTTPException(404, "Conversation not found.")
    conv.admin_read_at = models.utcnow()
    db.commit()
    return {
        "public_id": conv.public_id,
        "customer_name": conv.customer_name or "",
        "customer_email": conv.customer_email or "",
        "status": conv.status,
        "human_takeover": conv.human_takeover,
        "needs_human": conv.needs_human,
        "messages": [_msg_out(m) for m in conv.messages],
    }


@admin_router.post("/conversations/{public_id}/messages")
def admin_reply(public_id: str, data: schemas.DevSendIn, db: Session = Depends(get_db)):
    conv = crud.get_conversation(db, public_id)
    if not conv:
        raise HTTPException(404, "Conversation not found.")
    crud.add_message(db, conv, "dev", data.body.strip())
    conv.human_takeover = not data.let_bot_resume
    conv.needs_human = False
    conv.admin_read_at = models.utcnow()
    if data.let_bot_resume:
        st = conv.state(); st["_quick"] = []
        conv.bot_state = json.dumps(st)
    db.commit()
    return {"ok": True, "human_takeover": conv.human_takeover,
            "messages": [_msg_out(m) for m in conv.messages]}


@admin_router.post("/conversations/{public_id}/bot")
def admin_toggle_bot(public_id: str, db: Session = Depends(get_db)):
    """Toggle whether the bot may auto-reply again on this thread."""
    conv = crud.get_conversation(db, public_id)
    if not conv:
        raise HTTPException(404, "Conversation not found.")
    conv.human_takeover = not conv.human_takeover
    db.commit()
    return {"ok": True, "human_takeover": conv.human_takeover}
