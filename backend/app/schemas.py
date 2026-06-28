"""Pydantic request/response schemas."""
import datetime as dt
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(default="", max_length=120)
    whatsapp: str = Field(default="", max_length=40)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    whatsapp: str = ""
    created_at: dt.datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Orders -------------------------------------------------------------------
class OrderItem(BaseModel):
    service: str = ""
    tier: str = ""
    price: float = 0
    qty: int = Field(default=1, ge=1, le=99)


class OrderCreate(BaseModel):
    customer_name: str = Field(default="", max_length=120)
    customer_email: EmailStr
    customer_whatsapp: str = Field(default="", max_length=40)
    notes: str = Field(default="", max_length=2000)
    payment_method: str = Field(default="", max_length=40)
    items: List[OrderItem] = []


class UpdateOut(BaseModel):
    message: str
    status: Optional[str] = None
    progress: Optional[int] = None
    created_at: dt.datetime

    class Config:
        from_attributes = True


class DeliverableIn(BaseModel):
    title: str = Field(default="", max_length=200)
    preview_url: str = Field(default="", max_length=2000)
    final_url: str = Field(default="", max_length=2000)
    note: str = Field(default="", max_length=1000)


class DeliverableOut(BaseModel):
    id: int
    title: str = ""
    preview_url: str = ""
    final_url: Optional[str] = None   # only present once the order is paid
    locked: bool = True
    note: str = ""
    created_at: dt.datetime


class MilestoneOut(BaseModel):
    id: int
    title: str = ""
    status_key: str = ""
    done: bool = False
    done_at: Optional[dt.datetime] = None
    sort_order: int = 0


class MilestoneIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class MilestonePatch(BaseModel):
    done: Optional[bool] = None
    title: Optional[str] = Field(default=None, max_length=200)


class OrderOut(BaseModel):
    public_id: str
    customer_name: str
    customer_email: str
    customer_whatsapp: str = ""
    items: List[Any] = []
    total: float
    status: str
    status_label: str
    progress: int
    due_date: Optional[dt.date] = None
    notes: str = ""
    payment_method: str = ""
    payment_status: str = "unpaid"
    created_at: dt.datetime
    updated_at: dt.datetime
    updates: List[UpdateOut] = []
    deliverables: List[DeliverableOut] = []
    milestones: List[MilestoneOut] = []
    next_step: Optional[str] = None

    class Config:
        from_attributes = True


# --- Admin --------------------------------------------------------------------
class OrderAdminPatch(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    due_date: Optional[dt.date] = None
    notes: Optional[str] = None
    payment_status: Optional[str] = None  # unpaid | paid | refunded


class UpdateCreate(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    status: Optional[str] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)


class Stats(BaseModel):
    total_orders: int
    active_orders: int
    delivered_orders: int
    revenue: float
    clients: int
    by_status: dict


# --- Services (admin-managed) -------------------------------------------------
class ServicePackage(BaseModel):
    tier: str = ""
    price: float = 0
    delivery: str = ""
    revisions: int = 0
    summary: str = ""
    features: List[str] = []
    popular: bool = False


class ServiceIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    category: str = Field(default="Development", max_length=60)
    icon: str = Field(default="spark", max_length=30)
    short: str = Field(default="", max_length=600)
    tags: List[str] = []
    packages: List[ServicePackage] = []
    deliverables: List[str] = []
    active: bool = True
    sort_order: int = 0
    slug: Optional[str] = None


class ServiceOut(BaseModel):
    id: int
    slug: str
    title: str
    category: str
    icon: str
    short: str
    tags: List[str] = []
    packages: List[Any] = []
    deliverables: List[str] = []
    active: bool
    sort_order: int

    class Config:
        from_attributes = True


class PublicCatalog(BaseModel):
    """Public services response. `managed=True` once the developer has imported the
    built-in catalog into the DB — the site then treats the DB as authoritative."""
    managed: bool = False
    services: List[ServiceOut] = []


class ServiceImport(BaseModel):
    services: List[ServiceIn] = []


# --- Testimonials -------------------------------------------------------------
class TestimonialIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    role: str = Field(default="", max_length=120)
    location: str = Field(default="", max_length=120)
    rating: int = Field(default=5, ge=1, le=5)
    text: str = Field(min_length=10, max_length=1000)
    email: str = Field(default="", max_length=200)
    company: str = Field(default="", max_length=200)   # honeypot: must stay empty


class TestimonialOut(BaseModel):
    id: int
    name: str
    role: str = ""
    location: str = ""
    rating: int
    text: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


class TestimonialAdminOut(TestimonialOut):
    status: str


class TestimonialPatch(BaseModel):
    status: str  # approved | rejected | pending


# --- Chat ---------------------------------------------------------------------
class ChatStartIn(BaseModel):
    name: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=200)


class ChatSendIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class AttachmentOut(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int

    class Config:
        from_attributes = True


class ChatMessageOut(BaseModel):
    id: int
    sender: str
    body: str
    created_at: dt.datetime
    attachment: Optional[AttachmentOut] = None

    class Config:
        from_attributes = True


class ChatThreadOut(BaseModel):
    public_id: str
    secret: Optional[str] = None          # only returned when the thread is created
    status: str
    human_takeover: bool = False
    needs_human: bool = False
    messages: List[ChatMessageOut] = []
    quick_replies: List[str] = []


class ConversationSummary(BaseModel):
    public_id: str
    customer_name: str = ""
    customer_email: str = ""
    last_message: str = ""
    last_message_at: dt.datetime
    unread: int = 0
    status: str = "open"
    needs_human: bool = False
    human_takeover: bool = False


class DevSendIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    let_bot_resume: bool = False


# --- Bot training (curated knowledge base) ------------------------------------
class BotKnowledgeIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1, max_length=2000)
    keywords: str = Field(default="", max_length=500)
    enabled: bool = True


class BotKnowledgeOut(BaseModel):
    id: int
    question: str
    answer: str
    keywords: str = ""
    enabled: bool = True
    hits: int = 0
    created_at: dt.datetime


class BotUnansweredOut(BaseModel):
    id: int
    question: str
    count: int = 1
    resolved: bool = False
    created_at: dt.datetime
    last_seen: dt.datetime
