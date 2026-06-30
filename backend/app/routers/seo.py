"""SEO endpoints: public read of the SEO document, admin save, the dynamic
sitemap.xml + robots.txt (which replace the old static files), and the first-party
/marketing.js analytics loader."""
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from .. import schemas, seo
from ..database import get_db
from ..deps import get_current_admin

router = APIRouter(tags=["seo"])


@router.get("/api/seo")
def public_seo(db: Session = Depends(get_db)):
    """The current SEO document (read-only). Everything here is public by nature —
    it is what gets injected into the HTML <head> for crawlers."""
    return seo.get_doc(db)


@router.get("/api/admin/seo", dependencies=[Depends(get_current_admin)])
def admin_get_seo(db: Session = Depends(get_db)):
    return seo.get_doc(db)


@router.put("/api/admin/seo", dependencies=[Depends(get_current_admin)])
def admin_save_seo(doc: schemas.SeoDoc, db: Session = Depends(get_db)):
    """Replace the SEO document. Stored JSON is deep-merged onto the defaults, so
    any field left unset keeps a sensible value, and the rendered-head cache is
    cleared so changes show on the very next request."""
    saved = seo.save_doc(db, doc.model_dump())
    return saved


@router.get("/sitemap.xml")
def sitemap(db: Session = Depends(get_db)):
    xml = seo.build_sitemap(db)
    return Response(content=xml, media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.get("/robots.txt")
def robots(db: Session = Depends(get_db)):
    txt = seo.build_robots(db)
    return PlainTextResponse(content=txt,
                             headers={"Cache-Control": "public, max-age=3600"})


@router.get("/marketing.js")
def marketing_js(db: Session = Depends(get_db)):
    """First-party analytics/marketing loader, generated from the dashboard SEO
    settings. Served same-origin so script-src stays 'self' (no inline scripts).
    Returns a harmless comment when no marketing ids are configured."""
    js = seo.cached_marketing_js(db)
    return Response(content=js, media_type="application/javascript",
                    headers={"Cache-Control": "public, max-age=300"})
