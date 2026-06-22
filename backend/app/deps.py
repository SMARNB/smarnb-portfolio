"""Auth dependencies."""
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from . import models, security
from .database import get_db


def _user_from_token(token: str, db: Session):
    try:
        payload = security.decode_token(token)
        uid = int(payload.get("sub"))
    except Exception:
        return None
    return db.get(models.User, uid)


def _bearer(authorization: Optional[str]):
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    token = _bearer(authorization)
    if not token:
        raise HTTPException(401, "Not authenticated")
    user = _user_from_token(token, db)
    if not user:
        raise HTTPException(401, "Invalid or expired session. Please log in again.")
    return user


def get_optional_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    token = _bearer(authorization)
    return _user_from_token(token, db) if token else None


def get_current_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admins only.")
    return user
