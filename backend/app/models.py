"""Database models. PII fields use the Encrypted column (encrypted at rest);
emails also get a blind-index column so we can still look them up."""
import datetime as dt
import json

from sqlalchemy import (Boolean, Column, Date, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship

from .crypto import Encrypted
from .database import Base

STATUS_FLOW = ["received", "confirmed", "in_progress", "in_review", "delivered"]
STATUS_LABELS = {
    "received": "Received", "confirmed": "Confirmed", "in_progress": "In Progress",
    "in_review": "In Review", "delivered": "Delivered", "cancelled": "Cancelled",
}


def utcnow():
    return dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(Encrypted, nullable=False)                 # encrypted at rest
    email_bidx = Column(String(64), unique=True, index=True, nullable=False)  # lookup token
    name = Column(Encrypted, default="")
    hashed_password = Column(String(255), nullable=False)      # one-way (PBKDF2)
    role = Column(String(20), nullable=False, default="client")
    whatsapp = Column(Encrypted, default="")
    created_at = Column(DateTime, default=utcnow)

    orders = relationship("Order", back_populates="client")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    public_id = Column(String(20), unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    customer_name = Column(Encrypted, default="")
    customer_email = Column(Encrypted, default="")
    customer_email_bidx = Column(String(64), index=True, default="")
    customer_whatsapp = Column(Encrypted, default="")

    items_json = Column(Text, default="[]")                   # not PII
    total = Column(Float, default=0)

    status = Column(String(20), default="received", index=True)
    progress = Column(Integer, default=0)
    due_date = Column(Date, nullable=True)
    notes = Column(Encrypted, default="")                     # may contain PII
    payment_method = Column(String(60), default="")
    payment_status = Column(String(20), default="unpaid")     # unpaid | paid | refunded

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    client = relationship("User", back_populates="orders")
    updates = relationship("OrderUpdate", back_populates="order",
                           cascade="all, delete-orphan", order_by="OrderUpdate.created_at")
    deliverables = relationship("Deliverable", back_populates="order",
                                cascade="all, delete-orphan", order_by="Deliverable.created_at")

    @property
    def items(self):
        try:
            return json.loads(self.items_json or "[]")
        except Exception:
            return []

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)


class OrderUpdate(Base):
    __tablename__ = "order_updates"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    message = Column(Encrypted, default="")
    status = Column(String(20), nullable=True)
    progress = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    order = relationship("Order", back_populates="updates")


class Deliverable(Base):
    """A file/link delivered for an order. preview_url is always visible to the
    client; final_url is only revealed once payment_status == 'paid'."""
    __tablename__ = "deliverables"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    title = Column(String(200), default="")
    preview_url = Column(Text, default="")     # watermarked/low-res/demo — always shown
    final_url = Column(Text, default="")       # the real product — gated by payment
    note = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    order = relationship("Order", back_populates="deliverables")


class Service(Base):
    """Admin-managed services (added from the developer dashboard). The site
    merges these with the built-in catalog in assets/js/data.js."""
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    slug = Column(String(80), unique=True, index=True, nullable=False)
    title = Column(String(160), default="")
    category = Column(String(60), default="Development")
    icon = Column(String(30), default="spark")
    short = Column(Text, default="")
    tags_json = Column(Text, default="[]")
    packages_json = Column(Text, default="[]")
    sort_order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    def _json(self, raw):
        try:
            return json.loads(raw or "[]")
        except Exception:
            return []

    @property
    def tags(self):
        return self._json(self.tags_json)

    @property
    def packages(self):
        return self._json(self.packages_json)
