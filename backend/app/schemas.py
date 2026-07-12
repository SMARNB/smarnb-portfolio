"""Pydantic request/response schemas."""
import datetime as dt
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Auth ---------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(default="", max_length=120)
    whatsapp: str = Field(default="", max_length=40)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: str = Field(default="", max_length=10)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    whatsapp: str = ""
    created_at: dt.datetime
    email_verified: bool = True
    totp_enabled: bool = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    # True right after signup while email verification is pending; the UI then shows
    # the "enter your code" screen. Also flags an admin who must still set up 2FA.
    verification_required: bool = False
    must_setup_2fa: bool = False


class LoginResult(BaseModel):
    """Login can either succeed (token) or ask for a second factor (totp_required)."""
    access_token: str = ""
    token_type: str = "bearer"
    user: Optional[UserOut] = None
    totp_required: bool = False
    must_setup_2fa: bool = False


class UserAdminOut(BaseModel):
    """A registered client account, as seen by the admin (Clients tab). `email` is
    a plain str (not EmailStr) so a legacy/undecryptable value can still be listed
    instead of crashing the endpoint."""
    id: int
    email: str
    name: str = ""
    whatsapp: str = ""
    role: str
    created_at: dt.datetime
    email_verified: bool = False
    totp_enabled: bool = False
    orders: int = 0


class AdminPasswordSet(BaseModel):
    password: str = Field(min_length=6, max_length=200)


class VerifyEmailIn(BaseModel):
    code: str = Field(min_length=4, max_length=10)


class TotpEnableIn(BaseModel):
    code: str = Field(min_length=6, max_length=10)


class TotpDisableIn(BaseModel):
    code: str = Field(default="", max_length=10)
    password: str = Field(default="", max_length=128)


# --- Orders -------------------------------------------------------------------
class OrderItem(BaseModel):
    service: str = ""
    tier: str = ""
    price: float = 0
    qty: int = Field(default=1, ge=1, le=99)
    # Work-scope snapshot captured at checkout so invoices/emails describe exactly
    # what was sold (the package's summary + "what you get" bullets + delivery),
    # independent of any later catalogue edits. Optional & capped for safety.
    summary: str = Field(default="", max_length=300)
    delivery: str = Field(default="", max_length=60)
    scope: List[str] = Field(default_factory=list)

    @field_validator("scope")
    @classmethod
    def _cap_scope(cls, v):
        return [str(x).strip()[:140] for x in (v or []) if str(x).strip()][:20]


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


class PaymentProofOut(BaseModel):
    id: int
    filename: str = ""
    ref: str = ""
    created_at: dt.datetime


class MilestoneIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class MilestonePatch(BaseModel):
    done: Optional[bool] = None
    title: Optional[str] = Field(default=None, max_length=200)


class OrderInvoiceOut(BaseModel):
    number: str
    status: str
    sent_at: Optional[dt.datetime] = None


class OrderOut(BaseModel):
    public_id: str
    customer_name: str
    customer_email: str
    customer_whatsapp: str = ""
    invoice: Optional[OrderInvoiceOut] = None
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
    proofs: List[PaymentProofOut] = []

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


# --- Billing: invoices / email / inventory -------------------------------------
class InvoicePatch(BaseModel):
    status: Optional[str] = None      # void | draft (un-void)
    notes: Optional[str] = Field(default=None, max_length=1000)


class EmailSettingsIn(BaseModel):
    from_name: Optional[str] = Field(default=None, max_length=120)
    from_email: Optional[str] = Field(default=None, max_length=200)
    reply_to: Optional[str] = Field(default=None, max_length=200)
    bcc_owner: Optional[bool] = None
    invoice_footer: Optional[str] = Field(default=None, max_length=600)
    promo_footer: Optional[str] = Field(default=None, max_length=600)


class CampaignIn(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body_md: str = Field(min_length=1, max_length=20000)
    test_only: bool = False           # send just to the owner as a preview


class InventoryItemIn(BaseModel):
    sku: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=200)
    kind: str = Field(default="product", max_length=20)
    stock: Optional[int] = Field(default=None, ge=0)   # None = untracked
    low_stock_threshold: int = Field(default=1, ge=0)
    notes: str = Field(default="", max_length=600)


class InventoryItemPatch(BaseModel):
    sku: Optional[str] = Field(default=None, min_length=1, max_length=60)
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    kind: Optional[str] = Field(default=None, max_length=20)
    stock: Optional[int] = Field(default=None, ge=0)
    untrack: bool = False             # true → set stock to None (stop tracking)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0)
    active: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=600)


class StockAdjust(BaseModel):
    delta: int = Field(ge=-100000, le=100000)
    reason: str = Field(default="manual", max_length=30)
    note: str = Field(default="", max_length=300)


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
    channel: str = "web"
    is_client: bool = False   # True = signed-up account; False = guest (show its id)


class ClientChatSummary(BaseModel):
    """A signed-in client's own thread, for the 'past conversations' picker."""
    public_id: str
    status: str = "open"
    last_message: str = ""
    last_message_at: dt.datetime
    messages: int = 0


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


# --- Blog ---------------------------------------------------------------------
class BlogPostIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(default="", max_length=200)
    excerpt: str = Field(default="", max_length=400)
    body_md: str = Field(default="", max_length=200000)
    cover_image: str = Field(default="", max_length=500)
    category: str = Field(default="Tech", max_length=60)
    tags: List[str] = []
    related_services: List[str] = []   # catalog service slugs to feature on the post
    status: str = Field(default="draft", max_length=20)  # draft | published


class BlogPreviewIn(BaseModel):
    body_md: str = Field(default="", max_length=200000)


# --- SEO control centre -------------------------------------------------------
class SeoCrumb(BaseModel):
    name: str = ""
    path: str = "/"


class SeoRouteMeta(BaseModel):
    title: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=500)
    canonical: str = Field(default="", max_length=500)
    robots: str = Field(default="", max_length=120)
    keywords: str = Field(default="", max_length=600)
    og_title: str = Field(default="", max_length=300)
    og_description: str = Field(default="", max_length=500)
    og_image: str = Field(default="", max_length=500)
    twitter_title: str = Field(default="", max_length=300)
    twitter_description: str = Field(default="", max_length=500)
    twitter_image: str = Field(default="", max_length=500)
    breadcrumb: List[SeoCrumb] = []


class SeoJsonLd(BaseModel):
    person: bool = True
    services: bool = True
    reviews: bool = True
    faq: bool = True
    breadcrumb: bool = True
    website: bool = True
    search_action: bool = False


class SeoGeneral(BaseModel):
    site_name: str = Field(default="", max_length=120)
    brand_name: str = Field(default="", max_length=120)
    base_url: str = Field(default="", max_length=300)
    title_template: str = Field(default="%s", max_length=160)
    default_title: str = Field(default="", max_length=300)
    default_description: str = Field(default="", max_length=500)
    default_keywords: str = Field(default="", max_length=600)
    author: str = Field(default="", max_length=120)
    locale: str = Field(default="en_US", max_length=20)
    language: str = Field(default="en", max_length=20)
    default_og_image: str = Field(default="", max_length=500)
    og_type: str = Field(default="website", max_length=40)
    twitter_card: str = Field(default="summary_large_image", max_length=40)
    twitter_site: str = Field(default="", max_length=60)
    twitter_creator: str = Field(default="", max_length=60)
    theme_color: str = Field(default="#0a0d14", max_length=40)
    robots_default: str = Field(default="index, follow", max_length=120)
    google_verification: str = Field(default="", max_length=200)
    bing_verification: str = Field(default="", max_length=200)
    yandex_verification: str = Field(default="", max_length=200)
    # Marketing & analytics ids (empty => off; site stays first-party).
    ga4_id: str = Field(default="", max_length=40)
    gtm_id: str = Field(default="", max_length=40)
    google_ads_id: str = Field(default="", max_length=40)
    meta_pixel_id: str = Field(default="", max_length=60)
    meta_domain_verification: str = Field(default="", max_length=200)
    person_name: str = Field(default="", max_length=120)
    job_title: str = Field(default="", max_length=160)
    org_type: str = Field(default="ProfessionalService", max_length=60)
    email: str = Field(default="", max_length=200)
    telephone: str = Field(default="", max_length=60)
    whatsapp: str = Field(default="", max_length=60)
    area_served: str = Field(default="", max_length=160)
    price_range: str = Field(default="", max_length=20)
    logo: str = Field(default="", max_length=500)
    image: str = Field(default="", max_length=500)
    same_as: List[str] = []
    favicon: str = Field(default="", max_length=300)
    manifest: str = Field(default="", max_length=300)
    jsonld: SeoJsonLd = SeoJsonLd()
    robots_txt: str = Field(default="", max_length=4000)
    sitemap_changefreq: str = Field(default="weekly", max_length=20)
    target_keywords: str = Field(default="", max_length=1000)


class SeoFaqItem(BaseModel):
    q: str = Field(default="", max_length=300)
    a: str = Field(default="", max_length=1500)


class SeoDoc(BaseModel):
    general: SeoGeneral = SeoGeneral()
    routes: Dict[str, SeoRouteMeta] = {}
    faq: List[SeoFaqItem] = []
