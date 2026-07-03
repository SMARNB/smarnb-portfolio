"""Database operations (encryption-aware)."""
import datetime as dt
import json
import random
import re
import secrets

from sqlalchemy import func

from . import blog_render, config, crypto, models, security


# --- Users --------------------------------------------------------------------
def get_user_by_email(db, email):
    if not email:
        return None
    return db.query(models.User).filter(models.User.email_bidx == crypto.blind_index(email)).first()


def create_user(db, email, password, name="", whatsapp="", role="client", email_verified=False):
    user = models.User(
        email=email, email_bidx=crypto.blind_index(email),
        name=name, whatsapp=whatsapp, role=role,
        hashed_password=security.hash_password(password),
        email_verified=email_verified,
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


# --- Email verification (anti-spam) -------------------------------------------
def set_verification_code(db, user):
    """Generate a fresh 6-digit code, store its hash + a short expiry, reset the
    attempt counter. Returns the plaintext code (to email — never stored plain)."""
    code = "".join(secrets.choice("0123456789") for _ in range(6))
    now = models.utcnow()
    user.verify_code_hash = security.hash_token(code)
    user.verify_sent_at = now
    user.verify_expires = now + dt.timedelta(minutes=config.EMAIL_VERIFY_TTL_MIN)
    user.verify_attempts = 0
    db.commit()
    return code


def check_verification_code(db, user, code):
    """Validate a submitted code. Returns (ok: bool, error_message: str)."""
    if user.email_verified:
        return True, ""
    if not (user.verify_code_hash and user.verify_expires):
        return False, "Please request a new verification code."
    if models.utcnow() > user.verify_expires:
        return False, "That code has expired — request a new one."
    if (user.verify_attempts or 0) >= config.EMAIL_VERIFY_MAX_ATTEMPTS:
        return False, "Too many attempts. Please request a new code."
    user.verify_attempts = (user.verify_attempts or 0) + 1
    db.commit()
    if security.token_matches(str(code).strip(), user.verify_code_hash):
        user.email_verified = True
        user.verify_code_hash = ""
        user.verify_expires = None
        db.commit()
        return True, ""
    return False, "That code isn't right. Please check it and try again."


def seconds_since_last_code(user):
    if not user.verify_sent_at:
        return 10 ** 9
    return (models.utcnow() - user.verify_sent_at).total_seconds()


# --- Two-factor auth (TOTP) ---------------------------------------------------
def set_totp_secret(db, user, secret):
    """Stage a new (not-yet-enabled) TOTP secret during setup."""
    user.totp_secret = secret
    user.totp_enabled = False
    db.commit()
    return user


def enable_totp(db, user):
    user.totp_enabled = True
    db.commit()
    return user


def disable_totp(db, user):
    user.totp_secret = ""
    user.totp_enabled = False
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
    seed_milestones(db, order)
    add_update(db, order, "Order received. I'll confirm the details with you shortly.",
               status="received", progress=0)
    return order


# --- Milestones (automatic project tracking) ----------------------------------
def seed_milestones(db, order, commit=True):
    """Give a fresh order the default pipeline so tracking works out of the box.
    Returns the created rows (don't rely on order.milestones here — the relationship
    may already be cached as empty and won't reflect the inserts until a refresh)."""
    created = []
    for i, (status_key, title) in enumerate(models.DEFAULT_MILESTONES):
        m = models.OrderMilestone(order_id=order.id, title=title,
                                  status_key=status_key, sort_order=i)
        db.add(m)
        created.append(m)
    if commit:
        db.commit()
        db.refresh(order)
    else:
        db.flush()
    return created


def recompute_order(db, order, commit=True):
    """Derive status + progress from completed milestones. Cancelled orders are
    left untouched. This is what makes tracking automatic: nobody sets a % by hand."""
    if order.status == "cancelled":
        if commit:
            db.commit()
        return order
    ms = list(order.milestones)
    total = len(ms)
    done = [m for m in ms if m.done]
    order.progress = round(len(done) / total * 100) if total else 0
    reached = 0  # index of "received"
    for m in done:
        if m.status_key in models.STATUS_FLOW:
            reached = max(reached, models.STATUS_FLOW.index(m.status_key))
    order.status = models.STATUS_FLOW[reached]
    if total and len(done) == total:
        order.status = "delivered"
        order.progress = 100
    if commit:
        db.commit()
        db.refresh(order)
    return order


def next_step(order):
    """The next not-yet-done milestone title (what the client is waiting on)."""
    if order.status == "cancelled":
        return None
    for m in order.milestones:
        if not m.done:
            return m.title
    return None


def get_milestone(db, mid):
    return db.get(models.OrderMilestone, mid)


def add_milestone(db, order, title, status_key=""):
    nxt = max([m.sort_order for m in order.milestones], default=-1) + 1
    m = models.OrderMilestone(order_id=order.id, title=(title or "").strip()[:200],
                              status_key=status_key, sort_order=nxt)
    db.add(m)
    db.commit()
    recompute_order(db, order)
    return m


def set_milestone(db, order, m, done):
    """Mark a milestone done/undone, then auto-update status, progress and the
    client-visible timeline in one go."""
    done = bool(done)
    if m.done == done:
        return m
    m.done = done
    m.done_at = models.utcnow() if done else None
    db.commit()
    recompute_order(db, order)
    msg = ("✓ " + m.title) if done else ("Reopened: " + m.title)
    add_update(db, order, msg, status=order.status, progress=order.progress)
    db.refresh(order)
    return m


def rename_milestone(db, m, title):
    m.title = (title or "").strip()[:200]
    db.commit()
    return m


def delete_milestone(db, order, m):
    db.delete(m)
    db.commit()
    db.refresh(order)
    recompute_order(db, order)
    return order


def complete_milestone_by_status(db, order, status_key, note=None):
    """Auto-complete the pipeline milestone for a given stage (e.g. mark 'confirmed'
    done when payment lands). No-op if already done or missing."""
    for m in order.milestones:
        if m.status_key == status_key and not m.done:
            m.done = True
            m.done_at = models.utcnow()
            db.commit()
            recompute_order(db, order)
            add_update(db, order, note or ("✓ " + m.title),
                       status=order.status, progress=order.progress)
            db.refresh(order)
            return m
    return None


def backfill_milestones(db):
    """Give pre-existing orders (created before tracking shipped) a pipeline, with
    milestones up to their current stage already ticked. Run once at startup."""
    for order in db.query(models.Order).all():
        if order.milestones:
            continue
        created = seed_milestones(db, order, commit=False)
        if order.status in models.STATUS_FLOW:
            idx = models.STATUS_FLOW.index(order.status)
            for m in created:
                if m.status_key in models.STATUS_FLOW and models.STATUS_FLOW.index(m.status_key) <= idx:
                    m.done = True
                    m.done_at = order.updated_at or models.utcnow()
        db.commit()


def get_order(db, public_id):
    return db.query(models.Order).filter_by(public_id=public_id).first()


def get_order_by_payment_ref(db, ref):
    """Find an order by a gateway tracker/session id we stored on it (Safepay).
    payment_ref may hold several |-joined refs (embedded session + hosted tracker),
    so match by containment — the ids are UUID-based, no false positives."""
    if not ref:
        return None
    return db.query(models.Order).filter(models.Order.payment_ref.contains(ref)).first()


def mark_paid(db, order, note="Payment received."):
    """Flag an order paid and log a client-visible update (used by the payment
    gateways' verify/webhook paths and the admin dashboard)."""
    if order.payment_status != "paid":
        order.payment_status = "paid"
        add_update(db, order, note, status=order.status, progress=order.progress)
        db.commit()
        db.refresh(order)
        # Paying confirms the brief — auto-advance the tracker so the client sees it move.
        complete_milestone_by_status(db, order, "confirmed",
                                     note="✓ Requirements confirmed (payment received)")
        # Ping the owner on WhatsApp so they know money landed without watching the
        # dashboard (fire-and-forget; inert until a sender is configured in notify.py).
        from . import notify
        try:
            notify.notify_owner("💰 PAID: order %s — %s%s. %s"
                                % (order.public_id, config.CURRENCY,
                                   format(order.total or 0, ",.2f"), note))
        except Exception:
            pass
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
        "milestones": [
            {"id": m.id, "title": m.title, "status_key": m.status_key,
             "done": m.done, "done_at": m.done_at, "sort_order": m.sort_order}
            for m in order.milestones
        ],
        "next_step": next_step(order),
        "proofs": [
            {"id": p.id, "filename": p.filename, "ref": p.ref or "", "created_at": p.created_at}
            for p in order.proofs
        ],
    }


# --- Payment proofs (manual transfers) -----------------------------------------
def add_payment_proof(db, order, filename, content_type, size, data, ref=""):
    """Attach a buyer's payment screenshot to an order, log it on the timeline and
    ping the owner so it can be reviewed + marked paid from the admin dashboard."""
    proof = models.PaymentProof(order_id=order.id, filename=filename,
                                content_type=content_type, size=size, data=data,
                                ref=(ref or "")[:200])
    db.add(proof)
    add_update(db, order, "📎 Payment proof uploaded — I'll verify and confirm shortly.",
               status=order.status, progress=order.progress)
    db.commit()
    db.refresh(proof)
    from . import notify
    try:
        notify.notify_owner("📎 Payment proof uploaded for order %s (%s%s). Review it in /admin."
                            % (order.public_id, config.CURRENCY, format(order.total or 0, ",.2f")))
    except Exception:
        pass
    return proof


def get_payment_proof(db, proof_id):
    return db.get(models.PaymentProof, proof_id)


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


def get_conversation_by_wa_id(db, wa_id):
    """The most recent conversation bridged to a given WhatsApp number, if any."""
    if not wa_id:
        return None
    return (db.query(models.Conversation)
            .filter(models.Conversation.wa_id == wa_id)
            .order_by(models.Conversation.id.desc()).first())


def get_or_create_whatsapp_conversation(db, wa_id, name=""):
    """Find (or open) the chat thread for a WhatsApp visitor. Returns (conv, created)."""
    conv = get_conversation_by_wa_id(db, wa_id)
    if conv:
        if name and not conv.customer_name:
            conv.customer_name = name
            db.commit()
        return conv, False
    conv = models.Conversation(
        public_id=gen_conversation_id(db),
        secret=secrets.token_urlsafe(24),
        customer_name=name or "",
        channel="whatsapp", wa_id=wa_id, bot_state="{}",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv, True


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


# --- Blog ---------------------------------------------------------------------
def _blog_slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s or "post")[:200]


def gen_blog_slug(db, title, slug=None, exclude_id=None):
    base = _blog_slugify(slug or title)
    cand, n = base, 2
    while True:
        row = db.query(models.BlogPost).filter_by(slug=cand).first()
        if not row or row.id == exclude_id:
            return cand
        cand = "{}-{}".format(base, n)
        n += 1


def _apply_blog_fields(db, post, data):
    """Populate a post from a BlogPostIn: (re)render markdown to cached HTML, derive
    the read-time + a fallback excerpt, and manage published_at on publish."""
    post.title = (data.title or "").strip()
    post.category = data.category if data.category in models.BLOG_CATEGORIES else "Tech"
    post.tags_json = json.dumps([t.strip() for t in (data.tags or []) if t.strip()][:12])
    post.related_services_json = json.dumps(
        [s.strip() for s in (getattr(data, "related_services", None) or []) if s.strip()][:6])
    post.cover_image = (data.cover_image or "").strip()
    post.body_md = data.body_md or ""
    post.body_html = blog_render.render_markdown(post.body_md)
    post.reading_minutes = blog_render.reading_minutes(post.body_md)
    post.excerpt = (data.excerpt or "").strip() or blog_render.plain_excerpt(post.body_md)
    new_status = "published" if data.status == "published" else "draft"
    if new_status == "published" and not post.published_at:
        post.published_at = models.utcnow()
    post.status = new_status
    return post


def create_blog_post(db, data):
    post = models.BlogPost(slug=gen_blog_slug(db, data.title, data.slug))
    _apply_blog_fields(db, post, data)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def update_blog_post(db, post, data):
    desired = data.slug or post.slug or data.title
    post.slug = gen_blog_slug(db, data.title, desired, exclude_id=post.id)
    _apply_blog_fields(db, post, data)
    db.commit()
    db.refresh(post)
    return post


def get_blog_post(db, slug):
    return db.query(models.BlogPost).filter_by(slug=slug).first()


def get_blog_post_by_id(db, pid):
    return db.get(models.BlogPost, pid)


def list_blog_posts(db, published_only=True, category=None):
    q = db.query(models.BlogPost)
    if published_only:
        q = q.filter(models.BlogPost.status == "published")
    if category:
        q = q.filter(models.BlogPost.category == category)
    if published_only:
        return q.order_by(models.BlogPost.published_at.desc(),
                          models.BlogPost.id.desc()).all()
    return q.order_by(models.BlogPost.created_at.desc()).all()


def delete_blog_post(db, post):
    db.delete(post)
    db.commit()


def serialize_blog_post(post, full=True):
    d = {
        "id": post.id, "slug": post.slug, "title": post.title or "",
        "excerpt": post.excerpt or "", "cover_image": post.cover_image or "",
        "category": post.category or "Tech", "tags": post.tags,
        "related_services": post.related_services,
        "status": post.status, "reading_minutes": post.reading_minutes or 1,
        "published_at": post.published_at, "created_at": post.created_at,
        "updated_at": post.updated_at,
    }
    if full:
        d["body_md"] = post.body_md or ""
        d["body_html"] = post.body_html or ""
    return d


def blog_related_services(db, post):
    """Resolve a post's attached service slugs to lightweight cards for the post's
    'Related services' sidebar (active services only, preserving the saved order)."""
    slugs = post.related_services
    if not slugs:
        return []
    by_slug = {s.slug: s for s in list_services(db, active_only=True)}
    out = []
    for slug in slugs:
        s = by_slug.get(slug)
        if not s:
            continue
        prices = [p.get("price") for p in (s.packages or [])
                  if isinstance(p, dict) and p.get("price")]
        out.append({
            "slug": s.slug, "title": s.title, "short": s.short or "",
            "category": s.category or "", "icon": s.icon or "spark",
            "min_price": min(prices) if prices else None,
        })
    return out


def add_blog_image(db, filename, content_type, size, data):
    img = models.BlogImage(filename=filename, content_type=content_type, size=size, data=data)
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


def get_blog_image(db, iid):
    return db.get(models.BlogImage, iid)
