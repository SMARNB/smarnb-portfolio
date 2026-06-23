from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=List[schemas.ServiceOut])
def public_services(db: Session = Depends(get_db)):
    """Active services added from the dashboard. The site merges these with the
    built-in catalog in assets/js/data.js."""
    return crud.list_services(db, active_only=True)
