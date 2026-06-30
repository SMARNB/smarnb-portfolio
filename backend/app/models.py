"""Database models. PII fields use the Encrypted column (encrypted at rest);
emails also get a blind-index column so we can still look them up."""
import datetime as dt
import json

from sqlalchemy import (Boolean, Column, Date, DateTime, Float, ForeignKey,
                        Integer, LargeBinary, String, Text)
from sqlalchemy.orm import relationship

from .crypto import Encrypted
from .database import Base

STATUS_FLOW = ["received", "confirmed", "in_progress", "in_review", "delivered"]
STATUS_LABELS = {
    "received": "Received", "confirmed": "Confirmed", "in_progress": "In Progress",
    "in_review": "In Review", "delivered": "Delivered", "cancelled": "Cancelled",
}

# The automatic project pipeline. Every new order is seeded with these milestones;
# ticking them off auto-derives the order's status + progress (see crud.recompute_order).
# Each entry maps a milestone to the STATUS_FLOW stage it represents.
DEFAULT_MILESTONES = [
    ("confirmed", "Requirements confirmed"),
    ("in_progress", "Build in progress"),
    ("in_review", "Ready for your review"),
    ("delivered", "Delivered"),
]


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
    milestones = relationship("OrderMilestone", back_populates="order",
                              cascade="all, delete-orphan",
                              order_by="OrderMilestone.sort_order, OrderMilestone.id")

    @property
    def items(self):
        try:
            return json.loads(self.items_json or "[]")
        except Exception:
            return []

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)


class OrderMilestone(Base):
    """A single step in an order's automatic tracking pipeline. Completing the
    milestones drives the order's status + progress, so the developer never has to
    set a percentage by hand and the client always sees an accurate, live tracker.
    `status_key` links pipeline milestones to a STATUS_FLOW stage; custom milestones
    added by the developer leave it blank and only contribute to progress."""
    __tablename__ = "order_milestones"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    title = Column(String(200), default="")
    status_key = Column(String(20), default="")   # one of STATUS_FLOW, or "" for custom steps
    done = Column(Boolean, default=False)
    done_at = Column(DateTime, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    order = relationship("Order", back_populates="milestones")


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
    deliverables_json = Column(Text, default="[]")     # "what you get" bullets
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

    @property
    def deliverables(self):
        return self._json(self.deliverables_json)


class Setting(Base):
    """Tiny key/value store for site-level flags (e.g. whether the services
    catalog has been imported into the DB and is now authoritative)."""
    __tablename__ = "settings"
    key = Column(String(60), primary_key=True)
    value = Column(Text, default="")


class SeoSetting(Base):
    """Key/value store for the SEO control centre. The whole SEO document (global
    settings + per-route meta + editable FAQ) is persisted here as JSON so the
    developer can manage every search-engine-facing tag from the dashboard without
    ever editing the codebase. The SPA-serving handler reads this to inject the
    correct <head> + JSON-LD per route before sending HTML to crawlers."""
    __tablename__ = "seo_settings"
    key = Column(String(60), primary_key=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Testimonial(Base):
    """Client reviews. Submitted from the site as 'pending' and shown publicly
    only once the developer approves them in the dashboard."""
    __tablename__ = "testimonials"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), default="")             # public by nature
    role = Column(String(120), default="")
    location = Column(String(120), default="")
    rating = Column(Integer, default=5)
    text = Column(Text, default="")
    email = Column(Encrypted, default="")              # optional, for verification only
    status = Column(String(20), default="pending", index=True)  # pending|approved|rejected
    created_at = Column(DateTime, default=utcnow)


class Conversation(Base):
    """A chat thread between a visitor/client and the bot (and, when present, the
    developer). Anonymous visitors are authorised by a per-thread secret stored in
    their browser; logged-in clients are linked by client_id."""
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    public_id = Column(String(24), unique=True, index=True, nullable=False)
    secret = Column(String(64), nullable=False)        # bearer-style handle for the visitor
    client_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Channel the thread came in on: "web" (site chat) or "whatsapp" (Cloud API
    # bridge). For WhatsApp threads, wa_id is the visitor's phone number (digits).
    channel = Column(String(20), default="web", index=True)
    wa_id = Column(String(40), default="", index=True)

    customer_name = Column(Encrypted, default="")
    customer_email = Column(Encrypted, default="")
    customer_email_bidx = Column(String(64), index=True, default="")

    status = Column(String(20), default="open", index=True)   # open|closed
    human_takeover = Column(Boolean, default=False)    # dev replied → bot stops auto-answering
    needs_human = Column(Boolean, default=False)       # visitor asked for a human
    bot_state = Column(Text, default="{}")             # small JSON state machine

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    last_message_at = Column(DateTime, default=utcnow)
    admin_read_at = Column(DateTime, nullable=True)    # for unread badges
    client_read_at = Column(DateTime, nullable=True)

    messages = relationship("ChatMessage", back_populates="conversation",
                            cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def state(self):
        try:
            return json.loads(self.bot_state or "{}")
        except Exception:
            return {}


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String(10), default="client")      # client | bot | dev
    body = Column(Encrypted, default="")               # may contain PII → encrypted
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    attachment = relationship("ChatAttachment", back_populates="message",
                              uselist=False, cascade="all, delete-orphan")


class BotKnowledge(Base):
    """A curated Q&A the assistant can answer from. The developer adds these in the
    dashboard (often by 'teaching' the bot an answer to a previously unanswered
    question) — this is how the bot 'learns' without any third-party/LLM service."""
    __tablename__ = "bot_knowledge"
    id = Column(Integer, primary_key=True)
    question = Column(Text, default="")      # the canonical question / trigger phrase
    answer = Column(Text, default="")        # what the bot replies
    keywords = Column(Text, default="")      # optional extra comma-separated triggers
    enabled = Column(Boolean, default=True)
    hits = Column(Integer, default=0)        # how often it has matched (popularity)
    created_at = Column(DateTime, default=utcnow)


class BotUnanswered(Base):
    """Questions the bot couldn't confidently answer, deduped by normalized text.
    The developer reviews these and teaches the bot a reply (→ BotKnowledge)."""
    __tablename__ = "bot_unanswered"
    id = Column(Integer, primary_key=True)
    norm = Column(String(300), index=True, default="")   # normalized text for dedup
    question = Column(Text, default="")                   # the last raw phrasing seen
    count = Column(Integer, default=1)
    resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utcnow)
    last_seen = Column(DateTime, default=utcnow)


class ChatAttachment(Base):
    """A file (image or PDF) shared in a chat. Bytes live in the DB so they persist
    on free Postgres tiers; served only to the thread's participants + admin."""
    __tablename__ = "chat_attachments"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)
    filename = Column(String(255), default="file")
    content_type = Column(String(100), default="application/octet-stream")
    size = Column(Integer, default=0)
    data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    message = relationship("ChatMessage", back_populates="attachment")


# Blog categories the developer can file a post under (kept small + on-brand).
BLOG_CATEGORIES = ["Tech", "Tech News", "Services"]


class BlogPost(Base):
    """An admin-authored blog post. Authored in markdown; the HTML is rendered
    server-side once on save (cached in ``body_html``) so crawlers get the full
    article injected into the SPA shell for ``/blog/<slug>`` without running JS.
    Created automatically via create_all — no migration needed."""
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    title = Column(String(200), default="")
    excerpt = Column(Text, default="")
    body_md = Column(Text, default="")
    body_html = Column(Text, default="")           # cached server-rendered HTML
    cover_image = Column(String(500), default="")  # URL or /api/blog/images/<id>
    category = Column(String(60), default="Tech")  # one of BLOG_CATEGORIES
    tags_json = Column(Text, default="[]")
    # Optional catalog services the developer attaches to a post (by slug) — shown
    # as a "Related services" sidebar on the post, a contextual cross-sell.
    related_services_json = Column(Text, default="[]")
    status = Column(String(20), default="draft", index=True)  # draft | published
    reading_minutes = Column(Integer, default=1)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    @property
    def tags(self):
        try:
            return json.loads(self.tags_json or "[]")
        except Exception:
            return []

    @property
    def related_services(self):
        try:
            return json.loads(self.related_services_json or "[]")
        except Exception:
            return []


class BlogImage(Base):
    """A cover/inline image uploaded for the blog. Bytes live in the DB so they
    persist on free Postgres tiers (mirrors ChatAttachment); served publicly since
    they are part of published content."""
    __tablename__ = "blog_images"
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), default="image")
    content_type = Column(String(100), default="application/octet-stream")
    size = Column(Integer, default=0)
    data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=utcnow)
