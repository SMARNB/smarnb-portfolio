import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import config, crud, schemas, security
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Simple in-memory brute-force throttle (per IP). Resets on success.
_attempts = {}


def _check_rate(ip):
    now = time.time()
    fails = [t for t in _attempts.get(ip, []) if now - t < config.LOGIN_WINDOW_SECONDS]
    _attempts[ip] = fails
    if len(fails) >= config.LOGIN_MAX_ATTEMPTS:
        raise HTTPException(429, "Too many attempts. Please wait a few minutes and try again.")


def _record_fail(ip):
    _attempts.setdefault(ip, []).append(time.time())


@router.post("/register", response_model=schemas.Token)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, data.email):
        raise HTTPException(400, "An account with this email already exists — try logging in.")
    user = crud.create_user(db, data.email, data.password, data.name, data.whatsapp, role="client")
    token = security.create_access_token(user.id, {"role": user.role})
    return {"access_token": token, "user": user}


@router.post("/login", response_model=schemas.Token)
def login(data: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "?"
    _check_rate(ip)
    user = crud.get_user_by_email(db, data.email)
    if not user or not security.verify_password(data.password, user.hashed_password):
        _record_fail(ip)
        raise HTTPException(401, "Wrong email or password.")
    _attempts.pop(ip, None)  # success → clear failures
    token = security.create_access_token(user.id, {"role": user.role})
    return {"access_token": token, "user": user}


@router.get("/me", response_model=schemas.UserOut)
def me(user=Depends(get_current_user)):
    return user
