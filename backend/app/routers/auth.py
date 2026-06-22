from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, security
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, data.email):
        raise HTTPException(400, "An account with this email already exists — try logging in.")
    user = crud.create_user(db, data.email, data.password, data.name, data.whatsapp, role="client")
    token = security.create_access_token(user.id, {"role": user.role})
    return {"access_token": token, "user": user}


@router.post("/login", response_model=schemas.Token)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, data.email)
    if not user or not security.verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Wrong email or password.")
    token = security.create_access_token(user.id, {"role": user.role})
    return {"access_token": token, "user": user}


@router.get("/me", response_model=schemas.UserOut)
def me(user=Depends(get_current_user)):
    return user
