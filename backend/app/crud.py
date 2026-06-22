"""Database operations."""
import json
import random

from sqlalchemy import func

from . import models, security


# --- Users --------------------------------------------------------------------
def get_user_by_email(db, email):
    return (
        db.query(models.User)
        .filter(func.lower(models.User.email) == email.lower())
        .first()
    )


def create_user(db, email, password, name="", whatsapp="", role="client"):
    user = models.User(
        email=email, name=name, whatsapp=whatsapp, role=role,
        hashed_password=security.hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Link any guest orders that used this email so the new account sees them.
    (
        db.query(models.Order)
        .filter(models.Order.client_id.is_(None),
                func.lower(models.Order.customer_email) == email.lower())
        .update({"client_id": user.id}, synchronize_session=False)
    )
    db.commit()
    return user


# --- Orders -------------------------------------------------------------------
_ID_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no ambiguous chars


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
    if client_id is None:  # link to an existing client account by email if present
        existing = get_user_by_email(db, data.customer_email)
        if existing and existing.role == "client":
            client_id = existing.id

    order = models.Order(
        public_id=gen_public_id(db),
        client_id=client_id,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
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
    return (
        db.query(models.Order)
        .filter((models.Order.client_id == user.id)
                | (func.lower(models.Order.customer_email) == user.email.lower()))
        .order_by(models.Order.created_at.desc())
        .all()
    )


def all_orders(db):
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()


# --- Stats --------------------------------------------------------------------
def stats(db):
    total = db.query(func.count(models.Order.id)).scalar() or 0
    delivered = db.query(func.count(models.Order.id)).filter(models.Order.status == "delivered").scalar() or 0
    cancelled = db.query(func.count(models.Order.id)).filter(models.Order.status == "cancelled").scalar() or 0
    active = total - delivered - cancelled
    revenue = (
        db.query(func.coalesce(func.sum(models.Order.total), 0))
        .filter(models.Order.status == "delivered").scalar() or 0
    )
    clients = db.query(func.count(models.User.id)).filter(models.User.role == "client").scalar() or 0
    by_status = {s: c for s, c in
                 db.query(models.Order.status, func.count(models.Order.id))
                 .group_by(models.Order.status).all()}
    return {
        "total_orders": total, "active_orders": active, "delivered_orders": delivered,
        "revenue": round(float(revenue), 2), "clients": clients, "by_status": by_status,
    }
