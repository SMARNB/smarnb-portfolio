"""Blog: public read of published posts (+ images), and admin CRUD / uploads.

Posts are authored in markdown and rendered to HTML server-side on save (cached in
the DB). The SPA-serving handler in main.py injects the full article + per-post
meta/JSON-LD into the shell for /blog/<slug>, so crawlers get the whole post.
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from .. import blog_render, crud, models, schemas, seo
from ..database import get_db
from ..deps import get_current_admin

router = APIRouter(tags=["blog"])
admin_router = APIRouter(prefix="/api/admin/blog", tags=["blog-admin"],
                         dependencies=[Depends(get_current_admin)])

MAX_IMAGE = 6 * 1024 * 1024  # 6 MB
# Allowed image types -> (extension, magic-byte test). SVG excluded on purpose.
_IMG_MAGIC = {
    "image/png":  (".png",  lambda b: b[:8] == b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": (".jpg",  lambda b: b[:3] == b"\xff\xd8\xff"),
    "image/gif":  (".gif",  lambda b: b[:6] in (b"GIF87a", b"GIF89a")),
    "image/webp": (".webp", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
}


def _detect_image(raw):
    for ctype, (_ext, test) in _IMG_MAGIC.items():
        try:
            if test(raw):
                return ctype
        except Exception:
            continue
    return None


# ---- Public ------------------------------------------------------------------
@router.get("/api/blog")
def public_list(category: Optional[str] = None, db: Session = Depends(get_db)):
    cat = category if category in models.BLOG_CATEGORIES else None
    posts = crud.list_blog_posts(db, published_only=True, category=cat)
    return {"categories": models.BLOG_CATEGORIES,
            "posts": [crud.serialize_blog_post(p, full=False) for p in posts]}


@router.get("/api/blog/images/{iid}")
def public_image(iid: int, db: Session = Depends(get_db)):
    img = crud.get_blog_image(db, iid)
    if not img:
        raise HTTPException(404, "Not found.")
    return Response(content=img.data, media_type=img.content_type, headers={
        "Cache-Control": "public, max-age=604800",
        "X-Content-Type-Options": "nosniff",
    })


@router.get("/api/blog/{slug}")
def public_get(slug: str, db: Session = Depends(get_db)):
    post = crud.get_blog_post(db, slug)
    if not post or post.status != "published":
        raise HTTPException(404, "Post not found.")
    data = crud.serialize_blog_post(post, full=True)
    data["related"] = crud.blog_related_services(db, post)
    return data


# ---- Admin -------------------------------------------------------------------
@admin_router.get("")
def admin_list(db: Session = Depends(get_db)):
    return [crud.serialize_blog_post(p, full=False)
            for p in crud.list_blog_posts(db, published_only=False)]


@admin_router.post("")
def admin_create(data: schemas.BlogPostIn, db: Session = Depends(get_db)):
    post = crud.create_blog_post(db, data)
    seo.clear_cache()   # new post may now be in the sitemap + injected per-slug
    seo.write_seo_files(db)   # refresh the on-disk sitemap mirror
    return crud.serialize_blog_post(post, full=True)


@admin_router.post("/preview")
def admin_preview(data: schemas.BlogPreviewIn):
    """Render markdown to HTML without saving — powers the live editor preview, so
    it matches the production rendering exactly (same mistune pipeline)."""
    return {"body_html": blog_render.render_markdown(data.body_md),
            "reading_minutes": blog_render.reading_minutes(data.body_md),
            "excerpt": blog_render.plain_excerpt(data.body_md)}


@admin_router.get("/{pid}")
def admin_get(pid: int, db: Session = Depends(get_db)):
    post = crud.get_blog_post_by_id(db, pid)
    if not post:
        raise HTTPException(404, "Not found.")
    data = crud.serialize_blog_post(post, full=True)
    data["related"] = crud.blog_related_services(db, post)
    return data


@admin_router.put("/{pid}")
def admin_update(pid: int, data: schemas.BlogPostIn, db: Session = Depends(get_db)):
    post = crud.get_blog_post_by_id(db, pid)
    if not post:
        raise HTTPException(404, "Not found.")
    post = crud.update_blog_post(db, post, data)
    seo.clear_cache()
    seo.write_seo_files(db)
    return crud.serialize_blog_post(post, full=True)


@admin_router.delete("/{pid}")
def admin_delete(pid: int, db: Session = Depends(get_db)):
    post = crud.get_blog_post_by_id(db, pid)
    if not post:
        raise HTTPException(404, "Not found.")
    crud.delete_blog_post(db, post)
    seo.clear_cache()
    seo.write_seo_files(db)
    return {"ok": True}


@admin_router.post("/images")
async def admin_upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read(MAX_IMAGE + 1)
    if len(raw) > MAX_IMAGE:
        raise HTTPException(413, "Image is too large (max 6 MB).")
    if not raw:
        raise HTTPException(400, "Empty file.")
    ctype = _detect_image(raw)
    if not ctype:
        raise HTTPException(415, "Only PNG, JPG, GIF or WEBP images are allowed.")
    name = (re.sub(r"[^A-Za-z0-9._-]+", "_", (file.filename or "image").rsplit("/", 1)[-1])[:80]
            or "image")
    img = crud.add_blog_image(db, name, ctype, len(raw), raw)
    return {"id": img.id, "url": "/api/blog/images/{}".format(img.id),
            "filename": img.filename, "content_type": img.content_type, "size": img.size}
