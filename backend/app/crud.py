"""Database operations (encryption-aware)."""
import datetime as dt
import json
import random
import re
import secrets

from sqlalchemy import func

from . import crypto, models, security


# --- Users --------------------------------------------------------------------
def get_user_by_email(db, email):
    if not email:
        return None
    return db.query(models.User).filter(models.User.email_bidx == crypto.blind_index(email)).first()


def create_user(db, email, password, name="", whatsapp="", role="client"):
    user = models.User(
        email=email, email_bidx=crypto.blind_index(email),
        name=name, whatsapp=whatsapp, role=role,
        hashed_password=security.hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Link any guest orders placed with this email to the new account.
    db.query(models.Order).filter(
        models.Order.client_id.is_(None),
        models.Order.customer_email_bidx == crypto.blind_index(email),
    ).update({"client_id": user.id}, synchronize_session=False)
    db.commit()
    return user


# --- Orders -------------------------------------------------------------------
_ID_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def gen_public_id(db):
    while True:
        pid = "ALR-" + "".join(random.choice(_ID_CHARS) for _ in range(6))
        if not db.query(models.Order).filter_by(public_id=pid).first():
            return pid


def add_update(db, order, message, status=None, progress=None, commit=True):
    upd = models.OrderUpdate(order_id=order.id, message=message, status=status, progress=progress)
    db.add(upd)
    if status:
        order.status = status
    if progress is not None:
        order.progress = progress
    if commit:
        db.commit()
        db.refresh(order)
    return upd


def create_order(db, data, client=None):
    items = [i.model_dump() for i in data.items]
    total = round(sum((i.get("price", 0) or 0) * (i.get("qty", 1) or 1) for i in items), 2)

    client_id = client.id if client else None
    if client_id is None:
        existing = get_user_by_email(db, data.customer_email)
        if existing and existing.role == "client":
            client_id = existing.id

    order = models.Order(
        public_id=gen_public_id(db),
        client_id=client_id,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        customer_email_bidx=crypto.blind_index(data.customer_email),
        customer_whatsapp=data.customer_whatsapp,
        items_json=json.dumps(items),
        total=total,
        status="received",
        progress=0,
        notes=data.notes,
        payment_method=getattr(data, "payment_method", "") or "",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    add_update(db, order, "Order received. I'll confirm the details with you shortly.",
               status="received", progress=0)
    return order


def get_order(db, public_id):
    return db.query(models.Order).filter_by(public_id=public_id).first()


def mark_paid(db, order, note="Payment received."):
    """Flag an order paid and log a client-visible update (used by the Stripe webhook)."""
    if order.payment_status != "paid":
        order.payment_status = "paid"
        add_update(db, order, note, status=order.status, progress=order.progress)
        db.commit()
        db.refresh(order)
    return order


def orders_for_user(db, user):
    bidx = crypto.blind_index(user.email)
    return (
        db.query(models.Order)
        .filter((models.Order.client_id == user.id) | (models.Order.customer_email_bidx == bidx))
        .order_by(models.Order.created_at.desc())
        .all()
    )


def all_orders(db):
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()


def serialize_order(order, reveal_final=False):
    """Build an OrderOut dict. Deliverable final_url is hidden unless the order is
    paid (reveal_final=True for the admin, who always sees it)."""
    paid = (order.payment_status == "paid")
    deliverables = []
    for d in order.deliverables:
        unlocked = paid or reveal_final
        deliverables.append({
            "id": d.id, "title": d.title, "preview_url": d.preview_url,
            "final_url": (d.final_url if unlocked else None),
            "locked": (not paid), "note": d.note, "created_at": d.created_at,
        })
    return {
        "public_id": order.public_id,
        "customer_name": order.customer_name or "",
        "customer_email": order.customer_email or "",
        "customer_whatsapp": order.customer_whatsapp or "",
        "items": order.items,
        "total": order.total,
        "status": order.status,
        "status_label": order.status_label,
        "progress": order.progress,
        "due_date": order.due_date,
        "notes": order.notes or "",
        "payment_method": order.payment_method or "",
        "payment_status": order.payment_status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "updates": [
            {"message": u.message, "status": u.status, "progress": u.progress, "created_at": u.created_at}
            for u in order.updates
        ],
        "deliverables": deliverables,
    }


# --- Stats --------------------------------------------------------------------
def stats(db):
    total = db.query(func.count(models.Order.id)).scalar() or 0
    delivered = db.query(func.count(models.Order.id)).filter(models.Order.status == "delivered").scalar() or 0
    cancelled = db.query(func.count(models.Order.id)).filter(models.Order.status == "cancelled").scalar() or 0
    active = total - delivered - cancelled
    revenue = (db.query(func.coalesce(func.sum(models.Order.total), 0))
               .filter(models.Order.payment_status == "paid").scalar() or 0)
    clients = db.query(func.count(models.User.id)).filter(models.User.role == "client").scalar() or 0
    by_status = {s: c for s, c in
                 db.query(models.Order.status, func.count(models.Order.id)).group_by(models.Order.status).all()}
    return {"total_orders": total, "active_orders": active, "delivered_orders": delivered,
            "revenue": round(float(revenue), 2), "clients": clients, "by_status": by_status}


# --- Deliverables -------------------------------------------------------------
def add_deliverable(db, order, data):
    d = models.Deliverable(order_id=order.id, title=data.title, preview_url=data.preview_url,
                           final_url=data.final_url, note=data.note)
    db.add(d)
    db.commit()
    db.refresh(order)
    return d


def get_deliverable(db, did):
    return db.get(models.Deliverable, did)


def delete_deliverable(db, d):
    db.delete(d)
    db.commit()


# --- Services -----------------------------------------------------------------
def _slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "service"


def list_services(db, active_only=True):
    q = db.query(models.Service)
    if active_only:
        q = q.filter(models.Service.active.is_(True))
    return q.order_by(models.Service.sort_order, models.Service.id).all()


def get_service(db, sid):
    return db.get(models.Service, sid)


def create_service(db, data):
    slug = _slugify(data.slug or data.title)
    base, n = slug, 2
    while db.query(models.Service).filter_by(slug=slug).first():
        slug = "{}-{}".format(base, n)
        n += 1
    svc = models.Service(
        slug=slug, title=data.title, category=data.category, icon=data.icon, short=data.short,
        tags_json=json.dumps(data.tags),
        packages_json=json.dumps([p.model_dump() for p in data.packages]),
        deliverables_json=json.dumps(data.deliverables),
        active=data.active, sort_order=data.sort_order,
    )
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


def update_service(db, svc, data):
    svc.title = data.title
    svc.category = data.category
    svc.icon = data.icon
    svc.short = data.short
    svc.tags_json = json.dumps(data.tags)
    svc.packages_json = json.dumps([p.model_dump() for p in data.packages])
    svc.deliverables_json = json.dumps(data.deliverables)
    svc.active = data.active
    svc.sort_order = data.sort_order
    db.commit()
    db.refresh(svc)
    return svc


def delete_service(db, svc):
    db.delete(svc)
    db.commit()


def get_setting(db, key, default=None):
    s = db.get(models.Setting, key)
    return s.value if s else default


def set_setting(db, key, value):
    s = db.get(models.Setting, key)
    if s:
        s.value = value
    else:
        s = models.Setting(key=key, value=value)
        db.add(s)
    db.commit()
    return s


def catalog_for_bot(db):
    """Active services as plain dicts for the chat assistant."""
    out = []
    for s in list_services(db, active_only=True):
        out.append({"slug": s.slug, "title": s.title, "short": s.short,
                    "category": s.category, "tags": s.tags, "packages": s.packages,
                    "deliverables": s.deliverables})
    return out


# --- Testimonials -------------------------------------------------------------
def create_testimonial(db, data):
    t = models.Testimonial(
        name=data.name.strip(), role=(data.role or "").strip(),
        location=(data.location or "").strip(), rating=max(1, min(5, data.rating)),
        text=data.text.strip(), email=(data.email or "").strip(), status="pending",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def list_testimonials(db, status=None):
    q = db.query(models.Testimonial)
    if status:
        q = q.filter(models.Testimonial.status == status)
    return q.order_by(models.Testimonial.created_at.desc()).all()


def get_testimonial(db, tid):
    return db.get(models.Testimonial, tid)


def set_testimonial_status(db, t, status):
    t.status = status
    db.commit()
    db.refresh(t)
    return t


def delete_testimonial(db, t):
    db.delete(t)
    db.commit()


# --- Chat ---------------------------------------------------------------------
def gen_conversation_id(db):
    while True:
        pid = "C-" + "".join(random.choice(_ID_CHARS) for _ in range(8))
        if not db.query(models.Conversation).filter_by(public_id=pid).first():
            return pid


def create_conversation(db, name="", email="", client=None):
    conv = models.Conversation(
        public_id=gen_conversation_id(db),
        secret=secrets.token_urlsafe(24),
        client_id=client.id if client else None,
        customer_name=(client.name if client else name) or "",
        customer_email=(client.email if client else email) or "",
        customer_email_bidx=crypto.blind_index((client.email if client else email) or "") or "",
        bot_state="{}",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db, public_id):
    return db.query(models.Conversation).filter_by(public_id=public_id).first()


def add_message(db, conv, sender, body, commit=True):
    msg = models.ChatMessage(conversation_id=conv.id, sender=sender, body=body or "")
    db.add(msg)
    conv.last_message_at = models.utcnow()
    if commit:
        db.commit()
        db.refresh(msg)
    return msg


def add_attachment(db, conv, message, filename, content_type, size, data):
    att = models.ChatAttachment(
        message_id=message.id, conversation_id=conv.id, filename=filename,
        content_type=content_type, size=size, data=data,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


def list_conversations(db):
    return (db.query(models.Conversation)
            .order_by(models.Conversation.last_message_at.desc()).all())


def conversation_unread(conv, since_field="admin_read_at", from_senders=("client",)):
    since = getattr(conv, since_field)
    n = 0
    for m in conv.messages:
        if m.sender in from_senders and (since is None or m.created_at > since):
            n += 1
    return n


def save_state(db, conv, state):
    conv.bot_state = json.dumps(state or {})
    conv.needs_human = bool((state or {}).get("needs_human")) or conv.needs_human
    db.commit()


# --- Bot knowledge base (curated "learning") ----------------------------------
def _norm_q(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())[:300]


def knowledge_for_bot(db):
    """Enabled curated Q&A as plain dicts for the assistant."""
    rows = (db.query(models.BotKnowledge)
            .filter(models.BotKnowledge.enabled.is_(True))
            .order_by(models.BotKnowledge.id).all())
    return [{"id": r.id, "question": r.question or "", "answer": r.answer or "",
             "keywords": r.keywords or ""} for r in rows]


def list_bot_knowledge(db):
    return db.query(models.BotKnowledge).order_by(models.BotKnowledge.id.desc()).all()


def create_bot_knowledge(db, question, answer, keywords="", enabled=True):
    kn = models.BotKnowledge(question=(question or "").strip(), answer=(answer or "").strip(),
                             keywords=(keywords or "").strip(), enabled=bool(enabled))
    db.add(kn)
    db.commit()
    db.refresh(kn)
    return kn


def update_bot_knowledge(db, kn, question=None, answer=None, keywords=None, enabled=None):
    if question is not None:
        kn.question = question.strip()
    if answer is not None:
        kn.answer = answer.strip()
    if keywords is not None:
        kn.keywords = keywords.strip()
    if enabled is not None:
        kn.enabled = bool(enabled)
    db.commit()
    db.refresh(kn)
    return kn


def delete_bot_knowledge(db, kn):
    db.delete(kn)
    db.commit()


def bump_knowledge_hit(db, kid):
    kn = db.get(models.BotKnowledge, kid)
    if kn:
        kn.hits = (kn.hits or 0) + 1
        db.commit()
    return kn


def log_unanswered(db, question):
    """Record a question the bot couldn't answer, deduped by normalized text."""
    norm = _norm_q(question)
    if not norm:
        return None
    row = (db.query(models.BotUnanswered)
           .filter(models.BotUnanswered.norm == norm,
                   models.BotUnanswered.resolved.is_(False)).first())
    if row:
        row.count = (row.count or 0) + 1
        row.question = (question or "").strip()[:2000]
        row.last_seen = models.utcnow()
    else:
        row = models.BotUnanswered(norm=norm, question=(question or "").strip()[:2000], count=1)
        db.add(row)
    db.commit()
    return row


def list_unanswered(db, include_resolved=False):
    q = db.query(models.BotUnanswered)
    if not include_resolved:
        q = q.filter(models.BotUnanswered.resolved.is_(False))
    return q.order_by(models.BotUnanswered.count.desc(),
                      models.BotUnanswered.last_seen.desc()).all()


def resolve_unanswered(db, uid):
    row = db.get(models.BotUnanswered, uid)
    if row:
        row.resolved = True
        db.commit()
    return row


def delete_unanswered(db, row):
    db.delete(row)
    db.commit()
