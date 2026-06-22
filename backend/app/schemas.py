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
