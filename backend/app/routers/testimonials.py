"""Client testimonials: public submission (held for moderation) + public list of
approved reviews + admin moderation."""
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..deps import get_current_admin

router = APIRouter(prefix="/api", tags=["testimonials"])

# Light per-IP throttle so the form can't be spammed.
_recent = {}
_MAX_PER_HOUR = 5


def _throttle(ip):
    now = time.time()
    hits = [t for t in _recent.get(ip, []) if now - t < 3600]
    if len(hits) >= _MAX_PER_HOUR:
        raise HTTPException(429, "You've submitted a few already — please try again later.")
    hits.append(now)
    _recent[ip] = hits


@router.get("/testimonials", response_model=List[schemas.TestimonialOut])
def public_testimonials(db: Session = Depends(get_db)):
    return crud.list_testimonials(db, status="approved")


@router.post("/testimonials", response_model=dict)
def submit_testimonial(data: schemas.TestimonialIn, request: Request, db: Session = Depends(get_db)):
    if data.company.strip():            # honeypot tripped → silently accept, save nothing
        return {"ok": True, "message": "Thanks for your review!"}
    _throttle(request.client.host if request.client else "?")
    crud.create_testimonial(db, data)
    return {"ok": True, "message": "Thank you! Your review was submitted and will appear once approved."}


# ---- Admin moderation --------------------------------------------------------
@router.get("/admin/testimonials", response_model=List[schemas.TestimonialAdminOut],
            dependencies=[Depends(get_current_admin)])
def admin_list(db: Session = Depends(get_db)):
    return crud.list_testimonials(db)


@router.patch("/admin/testimonials/{tid}", response_model=schemas.TestimonialAdminOut,
              dependencies=[Depends(get_current_admin)])
def admin_set_status(tid: int, data: schemas.TestimonialPatch, db: Session = Depends(get_db)):
    t = crud.get_testimonial(db, tid)
    if not t:
        raise HTTPException(404, "Review not found.")
    if data.status not in ("pending", "approved", "rejected"):
        raise HTTPException(400, "Unknown status.")
    return crud.set_testimonial_status(db, t, data.status)


@router.delete("/admin/testimonials/{tid}", response_model=dict,
               dependencies=[Depends(get_current_admin)])
def admin_delete(tid: int, db: Session = Depends(get_db)):
    t = crud.get_testimonial(db, tid)
    if not t:
        raise HTTPException(404, "Review not found.")
    crud.delete_testimonial(db, t)
    return {"ok": True}
