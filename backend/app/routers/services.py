from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=schemas.PublicCatalog)
def public_services(db: Session = Depends(get_db)):
    """Active services. Before the built-ins are imported, the site merges these
    with assets/js/data.js; once `managed` is true, the DB is authoritative."""
    managed = crud.get_setting(db, "catalog_managed", "0") == "1"
    return {"managed": managed, "services": crud.list_services(db, active_only=True)}
