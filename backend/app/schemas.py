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
    active: bool
    sort_order: int

    class Config:
        from_attributes = True
