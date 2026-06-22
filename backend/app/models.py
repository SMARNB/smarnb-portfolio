"""Database models: User, Order, OrderUpdate."""
import datetime as dt
import json

from sqlalchemy import (Column, Integer, String, Float, Text, DateTime, Date, ForeignKey)
from sqlalchemy.orm import relationship

from .database import Base

# Order lifecycle. "cancelled" is terminal but off the happy path.
STATUS_FLOW = ["received", "confirmed", "in_progress", "in_review", "delivered"]
STATUS_LABELS = {
    "received": "Received",
    "confirmed": "Confirmed",
    "in_progress": "In Progress",
    "in_review": "In Review",
    "delivered": "Delivered",
    "cancelled": "Cancelled",
}


def utcnow():
    return dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(160), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False, default="")
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="client")  # "client" | "admin"
    whatsapp = Column(String(40), default="")
    created_at = Column(DateTime, default=utcnow)

    orders = relationship("Order", back_populates="client")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    public_id = Column(String(20), unique=True, index=True, nullable=False)   # ALR-XXXXXX
    client_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    customer_name = Column(String(120), default="")
    customer_email = Column(String(160), index=True, default="")
    customer_whatsapp = Column(String(40), default="")

    items_json = Column(Text, default="[]")
    total = Column(Float, default=0)

    status = Column(String(20), default="received", index=True)
    progress = Column(Integer, default=0)         # 0..100
    due_date = Column(Date, nullable=True)
    notes = Column(Text, default="")
    payment_method = Column(String(40), default="")        # client's chosen method
    payment_status = Column(String(20), default="unpaid")  # unpaid | paid | refunded

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    client = relationship("User", back_populates="orders")
    updates = relationship(
        "OrderUpdate", back_populates="order",
        cascade="all, delete-orphan", order_by="OrderUpdate.created_at",
    )

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
    message = Column(Text, default="")
    status = Column(String(20), nullable=True)
    progress = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    order = relationship("Order", back_populates="updates")
