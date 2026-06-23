"""Database operations (encryption-aware)."""
import json
import random
import re

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
    svc.active = data.active
    svc.sort_order = data.sort_order
    db.commit()
    db.refresh(svc)
    return svc


def delete_service(db, svc):
    db.delete(svc)
    db.commit()
