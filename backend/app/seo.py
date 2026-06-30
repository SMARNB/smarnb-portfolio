"""SEO control centre.

Everything a crawler sees is generated here from a single JSON document stored in
the DB (table ``seo_settings``) and edited entirely from the developer dashboard —
never by touching the codebase. This module:

* defines the default SEO document (sensible, brand-accurate starting values),
* loads/saves the document (deep-merged onto the defaults so it stays
  forward-compatible as new fields are added),
* builds JSON-LD (Person/ProfessionalService, Service per catalog item,
  AggregateRating + Review from approved testimonials, FAQPage, BreadcrumbList,
  WebSite + optional SearchAction) from *real* data,
* renders the per-route ``<head>`` block (title, meta, canonical, robots, Open
  Graph, Twitter cards, verification tags, theme-color, icons, manifest, JSON-LD)
  that ``main.py`` injects into the SPA shell before serving it, and
* builds the dynamic ``sitemap.xml`` and ``robots.txt``.

It is first-party only: no third-party scripts are emitted — verification meta
tags and JSON-LD data blocks are inert and CSP-safe.
"""
import copy
import html
import json
import time

from . import config, crud, models

# --- Defaults -----------------------------------------------------------------
_BASE_URL = (config.PUBLIC_BASE_URL or "https://smarnb.onrender.com").rstrip("/")

DEFAULT_DOC = {
    "general": {
        "site_name": "SMARNB",
        "brand_name": "Muhammad Ali Raza",
        "base_url": _BASE_URL,
        # %s is replaced by the page title. Keep the brand on the right for SERP.
        "title_template": "%s · SMARNB",
        "default_title": "Full-Stack Developer, Automation & Design",
        "default_description": (
            "Freelance full-stack developer & designer — Python SaaS dashboards, "
            "Selenium & OCR automation, computer vision, Figma UI/UX and packaging."),
        "default_keywords": (
            "full-stack developer, python developer, saas dashboard, selenium automation, "
            "ocr, computer vision, figma ui ux, packaging design, freelance developer"),
        "author": "Muhammad Ali Raza",
        "locale": "en_US",
        "language": "en",
        "default_og_image": "/og-image.svg",
        "og_type": "website",
        "twitter_card": "summary_large_image",
        "twitter_site": "",
        "twitter_creator": "",
        "theme_color": "#0a0d14",
        "robots_default": "index, follow",
        # Search-engine ownership verification (paste the token only, not the tag).
        "google_verification": "",
        "bing_verification": "",
        "yandex_verification": "",
        # Structured-data identity (Person / ProfessionalService).
        "person_name": "Muhammad Ali Raza",
        "job_title": "Full-Stack Developer & Designer",
        "org_type": "ProfessionalService",
        "email": config.CONTACT_EMAIL or "shahjee975@gmail.com",
        "telephone": config.CONTACT_WHATSAPP or "",
        "whatsapp": config.CONTACT_WHATSAPP or "",
        "area_served": "Worldwide",
        "price_range": "$$",
        "logo": "/assets/img/profile.jpg",
        "image": "/assets/img/profile.jpg",
        "same_as": ["https://github.com/SMARNB"],
        # Icons / manifest.
        "favicon": "/favicon.svg",
        "manifest": "/manifest.webmanifest",
        # Which JSON-LD blocks to emit.
        "jsonld": {
            "person": True, "services": True, "reviews": True, "faq": True,
            "breadcrumb": True, "website": True, "search_action": False,
        },
        # robots.txt: blank => auto-generated. sitemap changefreq for content pages.
        "robots_txt": "",
        "sitemap_changefreq": "weekly",
        # Guidance only — where you want to rank.
        "target_keywords": (
            "freelance full-stack developer, python saas dashboard, selenium automation bot, "
            "ocr data extraction, computer vision developer, figma ui ux designer, "
            "product packaging design"),
    },
    "routes": {
        "default": {
            "title": "", "description": "", "canonical": "", "robots": "",
            "keywords": "", "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [],
        },
        "/": {
            "title": "Muhammad Ali Raza — Full-Stack Dev, Automation & Design",
            "description": (
                "Hire a multidisciplinary freelancer: Python SaaS dashboards, Selenium & "
                "OCR automation, computer vision, Figma UI/UX & packaging — on time."),
            "canonical": "", "robots": "", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [{"name": "Home", "path": "/"}],
        },
        "/store": {
            "title": "Store — Services, Packages & Pricing",
            "description": (
                "Browse services, fixed packages & transparent pricing — Python dashboards, "
                "automation bots, computer vision, UI/UX & packaging. Order in two clicks."),
            "canonical": "", "robots": "", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [{"name": "Home", "path": "/"}, {"name": "Store", "path": "/store"}],
        },
        "/services": {
            "title": "Services — Development, Automation & Design",
            "description": (
                "Full-service catalogue: Python SaaS dashboards, Selenium & OCR automation, "
                "computer vision, Figma UI/UX and packaging — with a clear, transparent "
                "process from brief to on-time delivery."),
            "canonical": "", "robots": "", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [{"name": "Home", "path": "/"}, {"name": "Services", "path": "/services"}],
        },
        "/work": {
            "title": "Selected Work & Client Results",
            "description": (
                "Recent client projects across development, design, automation and packaging "
                "— and what clients say about working with me."),
            "canonical": "", "robots": "", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [{"name": "Home", "path": "/"}, {"name": "Work", "path": "/work"}],
        },
        "/projects": {
            "title": "Projects — CodeWatch & Open-Source",
            "description": (
                "Personal & open-source engineering, including CodeWatch — a real-time "
                "multi-camera computer-vision surveillance & access-control system."),
            "canonical": "", "robots": "", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [{"name": "Home", "path": "/"}, {"name": "Projects", "path": "/projects"}],
        },
        "/about": {
            "title": "About — Muhammad Ali Raza",
            "description": (
                "Computer-vision & full-stack engineer based in Lahore, Pakistan — the "
                "background, experience and skills behind the work."),
            "canonical": "", "robots": "", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [{"name": "Home", "path": "/"}, {"name": "About", "path": "/about"}],
        },
        "/contact": {
            "title": "Contact & Custom Requests",
            "description": (
                "Start a project or ask a question — custom-request form, FAQ, and flexible "
                "local (Raast/SadaPay/JazzCash) & international payment options."),
            "canonical": "", "robots": "", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [{"name": "Home", "path": "/"}, {"name": "Contact", "path": "/contact"}],
        },
        # App + admin are tools, not content — keep them out of the index.
        "/app": {
            "title": "Client Area", "description": "Track your projects and orders.",
            "canonical": "", "robots": "noindex, nofollow", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [],
        },
        "/admin": {
            "title": "Developer", "description": "Private control room.",
            "canonical": "", "robots": "noindex, nofollow", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [],
        },
    },
    "faq": [
        {"q": "How do I start a project?",
         "a": "Pick a package and click Order to add it to your cart, then check out — your "
              "request comes straight to me. For anything custom, use the Custom Request form "
              "or message me on WhatsApp."},
        {"q": "What happens after I place an order?",
         "a": "You'll get an order ID you can use to track status here on the site, and I'll "
              "confirm details with you by email or WhatsApp before starting. Payment is "
              "arranged on confirmation."},
        {"q": "Can you handle custom or larger projects?",
         "a": "Absolutely. Most of my work is custom. Send me your scope through the Custom "
              "Request form and I'll reply with a tailored quote and timeline."},
        {"q": "Do I get the source files?",
         "a": "Yes — every package includes full source/working files and the rights to use "
              "them. You own what you pay for."},
        {"q": "How many revisions are included?",
         "a": "Each package lists its included revisions. Need more? We can always add them — "
              "I want you happy with the result."},
        {"q": "What are your payment terms?",
         "a": "Flexible. I work through Fiverr, direct invoice, or a simple milestone split "
              "for larger projects. We'll agree on terms before any work begins."},
    ],
}

# Routes that should never appear in the sitemap regardless of settings.
_NON_INDEX_ROUTES = {"default", "/app", "/admin"}


# --- Persistence (deep-merged onto defaults) ----------------------------------
def _deep_merge(base, over):
    """Recursively overlay ``over`` onto a copy of ``base`` (dicts merge; other
    values, including lists, are replaced)."""
    out = copy.deepcopy(base)
    if not isinstance(over, dict):
        return out
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def get_doc(db):
    """The current SEO document — stored JSON deep-merged onto the defaults so any
    field the developer hasn't set still has a sensible value."""
    row = db.get(models.SeoSetting, "doc")
    stored = {}
    if row and row.value:
        try:
            stored = json.loads(row.value)
        except Exception:
            stored = {}
    return _deep_merge(DEFAULT_DOC, stored)


def save_doc(db, doc):
    """Persist the SEO document and invalidate the rendered-head cache."""
    row = db.get(models.SeoSetting, "doc")
    payload = json.dumps(doc)
    if row:
        row.value = payload
    else:
        row = models.SeoSetting(key="doc", value=payload)
        db.add(row)
    db.commit()
    clear_cache()
    return get_doc(db)


# --- Small helpers ------------------------------------------------------------
def _abs(base_url, url):
    """Make a possibly-relative URL absolute against base_url."""
    if not url:
        return ""
    if url.startswith(("http://", "https://", "//")):
        return url
    return base_url.rstrip("/") + "/" + url.lstrip("/")


def _esc(s):
    return html.escape(str(s or ""), quote=True)


def _meta(name, content, prop=False):
    if content in (None, ""):
        return ""
    attr = "property" if prop else "name"
    return '<meta {}="{}" content="{}">'.format(attr, _esc(name), _esc(content))


def _effective(doc, path):
    """Merge the per-route meta for ``path`` over the 'default' route entry."""
    routes = doc.get("routes", {})
    base = routes.get("default", {})
    merged = dict(base)
    if path in routes:
        merged.update({k: v for k, v in routes[path].items()})
    return merged


# --- JSON-LD builders ---------------------------------------------------------
def _ld_identity(g, base_url, db):
    """Person + ProfessionalService node, enriched with AggregateRating + Reviews
    built from approved testimonials when available."""
    org_type = g.get("org_type") or "ProfessionalService"
    node = {
        "@type": [org_type, "Person"] if org_type != "Person" else "Person",
        "@id": base_url + "/#identity",
        "name": g.get("person_name") or g.get("brand_name"),
        "url": base_url + "/",
        "jobTitle": g.get("job_title"),
        "description": g.get("default_description"),
    }
    if g.get("image"):
        node["image"] = _abs(base_url, g["image"])
    if g.get("logo"):
        node["logo"] = _abs(base_url, g["logo"])
    if g.get("email"):
        node["email"] = g["email"]
    if g.get("telephone"):
        node["telephone"] = g["telephone"]
    if g.get("area_served"):
        node["areaServed"] = g["area_served"]
    if g.get("price_range"):
        node["priceRange"] = g["price_range"]
    same = [s for s in (g.get("same_as") or []) if s]
    if same:
        node["sameAs"] = same
    if org_type != "Person":
        node["founder"] = {"@type": "Person", "name": g.get("person_name")}

    # AggregateRating + Review from approved testimonials (real data).
    if g.get("jsonld", {}).get("reviews", True):
        approved = crud.list_testimonials(db, status="approved")
        ratings = [t.rating for t in approved if t.rating]
        if ratings:
            node["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": round(sum(ratings) / len(ratings), 1),
                "reviewCount": len(ratings),
                "bestRating": 5, "worstRating": 1,
            }
            node["review"] = [{
                "@type": "Review",
                "author": {"@type": "Person", "name": t.name or "Client"},
                "reviewRating": {"@type": "Rating", "ratingValue": t.rating,
                                 "bestRating": 5, "worstRating": 1},
                "reviewBody": t.text or "",
            } for t in approved[:12]]
    return node


def _ld_services(g, base_url, db):
    """A Service node per active catalog service, with an Offer from its cheapest
    package."""
    out = []
    provider = {"@id": base_url + "/#identity"}
    for s in crud.list_services(db, active_only=True):
        node = {
            "@type": "Service",
            "name": s.title,
            "description": s.short or "",
            "serviceType": s.category or "",
            "provider": provider,
            "url": base_url + "/store#svc-" + s.slug,
        }
        prices = [p.get("price") for p in (s.packages or []) if isinstance(p, dict) and p.get("price")]
        if prices:
            node["offers"] = {
                "@type": "Offer",
                "price": min(prices),
                "priceCurrency": config.CURRENCY_CODE.upper() or "USD",
                "availability": "https://schema.org/InStock",
                "url": base_url + "/store#svc-" + s.slug,
            }
        out.append(node)
    return out


def _ld_faq(doc):
    items = [f for f in (doc.get("faq") or []) if f.get("q") and f.get("a")]
    if not items:
        return None
    return {
        "@type": "FAQPage",
        "mainEntity": [{
            "@type": "Question",
            "name": f["q"],
            "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
        } for f in items],
    }


def _ld_breadcrumb(meta, base_url):
    crumbs = meta.get("breadcrumb") or []
    if not crumbs:
        return None
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [{
            "@type": "ListItem",
            "position": i + 1,
            "name": c.get("name", ""),
            "item": _abs(base_url, c.get("path", "/")),
        } for i, c in enumerate(crumbs)],
    }


def _ld_website(g, base_url):
    node = {
        "@type": "WebSite",
        "@id": base_url + "/#website",
        "url": base_url + "/",
        "name": g.get("site_name") or g.get("brand_name"),
        "description": g.get("default_description"),
        "publisher": {"@id": base_url + "/#identity"},
        "inLanguage": g.get("language") or "en",
    }
    if g.get("jsonld", {}).get("search_action"):
        node["potentialAction"] = {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint",
                       "urlTemplate": base_url + "/store?q={search_term_string}"},
            "query-input": "required name=search_term_string",
        }
    return node


def build_jsonld(db, path, doc=None):
    """Return the @graph list of JSON-LD nodes appropriate for ``path``."""
    doc = doc or get_doc(db)
    g = doc["general"]
    base_url = (g.get("base_url") or _BASE_URL).rstrip("/")
    toggles = g.get("jsonld", {})
    meta = _effective(doc, path)
    graph = []
    if toggles.get("website", True):
        graph.append(_ld_website(g, base_url))
    if toggles.get("person", True):
        graph.append(_ld_identity(g, base_url, db))
    if toggles.get("breadcrumb", True):
        bc = _ld_breadcrumb(meta, base_url)
        if bc:
            graph.append(bc)
    # Service catalogue belongs on the home + services + store pages.
    if toggles.get("services", True) and path in ("/", "/services", "/store"):
        graph.extend(_ld_services(g, base_url, db))
    # FAQ lives on the contact page (where the FAQ section now renders).
    if toggles.get("faq", True) and path == "/contact":
        faq = _ld_faq(doc)
        if faq:
            graph.append(faq)
    return graph


# --- Head rendering (per route) ----------------------------------------------
def render_head(db, path, doc=None):
    """The managed ``<head>`` HTML fragment for ``path``: title, description,
    canonical, robots, Open Graph, Twitter cards, verification tags, theme-color,
    icons, manifest and a JSON-LD ``@graph`` script — all from the DB."""
    doc = doc or get_doc(db)
    g = doc["general"]
    base_url = (g.get("base_url") or _BASE_URL).rstrip("/")
    meta = _effective(doc, path)

    page_title = meta.get("title") or g.get("default_title")
    tmpl = g.get("title_template") or "%s"
    full_title = tmpl.replace("%s", page_title) if "%s" in tmpl else page_title
    # The home page title is usually already the full brand title.
    if path == "/" and meta.get("title"):
        full_title = meta["title"]

    desc = meta.get("description") or g.get("default_description")
    keywords = meta.get("keywords") or g.get("default_keywords")
    robots = meta.get("robots") or g.get("robots_default") or "index, follow"
    canonical = meta.get("canonical") or (base_url + (path if path != "default" else "/"))

    og_title = meta.get("og_title") or page_title
    og_desc = meta.get("og_description") or desc
    og_image = _abs(base_url, meta.get("og_image") or g.get("default_og_image"))
    tw_title = meta.get("twitter_title") or og_title
    tw_desc = meta.get("twitter_description") or og_desc
    tw_image = _abs(base_url, meta.get("twitter_image") or meta.get("og_image") or g.get("default_og_image"))

    parts = [
        "<title>{}</title>".format(_esc(full_title)),
        _meta("description", desc),
        _meta("keywords", keywords),
        _meta("author", g.get("author")),
        _meta("robots", robots),
        '<link rel="canonical" href="{}">'.format(_esc(canonical)),
        _meta("theme-color", g.get("theme_color")),
        # Open Graph
        _meta("og:type", g.get("og_type") or "website", prop=True),
        _meta("og:site_name", g.get("site_name") or g.get("brand_name"), prop=True),
        _meta("og:title", og_title, prop=True),
        _meta("og:description", og_desc, prop=True),
        _meta("og:url", canonical, prop=True),
        _meta("og:image", og_image, prop=True),
        _meta("og:locale", g.get("locale") or "en_US", prop=True),
        # Twitter
        _meta("twitter:card", g.get("twitter_card") or "summary_large_image"),
        _meta("twitter:title", tw_title),
        _meta("twitter:description", tw_desc),
        _meta("twitter:image", tw_image),
        _meta("twitter:site", g.get("twitter_site")),
        _meta("twitter:creator", g.get("twitter_creator")),
        # Search-engine verification
        _meta("google-site-verification", g.get("google_verification")),
        _meta("msvalidate.01", g.get("bing_verification")),
        _meta("yandex-verification", g.get("yandex_verification")),
        # Icons + manifest
        '<link rel="icon" href="{}" type="image/svg+xml">'.format(_esc(g.get("favicon"))) if g.get("favicon") else "",
        '<link rel="manifest" href="{}">'.format(_esc(g.get("manifest"))) if g.get("manifest") else "",
    ]

    graph = build_jsonld(db, path, doc=doc)
    if graph:
        ld = {"@context": "https://schema.org", "@graph": graph}
        # </ is escaped so the JSON can never close the <script> element early.
        payload = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
        parts.append('<script type="application/ld+json">{}</script>'.format(payload))

    return "\n  ".join(p for p in parts if p)


# --- Per-path cache (rendered head HTML) --------------------------------------
_cache = {}
_TTL = 300  # seconds; JSON-LD reflects approved reviews/services, refreshed often enough


def clear_cache():
    _cache.clear()


def cached_head(db, path):
    """render_head with a short in-memory TTL so the SPA shell stays fast even
    though it embeds DB-derived JSON-LD. Cleared whenever settings are saved."""
    now = time.time()
    hit = _cache.get(path)
    if hit and hit[0] > now:
        return hit[1]
    htmlfrag = render_head(db, path)
    _cache[path] = (now + _TTL, htmlfrag)
    return htmlfrag


# --- sitemap.xml --------------------------------------------------------------
def build_sitemap(db, base_url=None, doc=None):
    doc = doc or get_doc(db)
    g = doc["general"]
    base_url = (base_url or g.get("base_url") or _BASE_URL).rstrip("/")
    changefreq = g.get("sitemap_changefreq") or "weekly"
    now = models.utcnow().date().isoformat()

    urls = []

    def add(loc, lastmod=now, freq=changefreq, priority="0.7"):
        urls.append((loc, lastmod, freq, priority))

    # Indexable content routes from the settings (skip app/admin/noindex).
    for path, meta in doc.get("routes", {}).items():
        if path in _NON_INDEX_ROUTES:
            continue
        if "noindex" in (meta.get("robots") or "").lower():
            continue
        priority = "1.0" if path == "/" else "0.9"
        add(base_url + (path if path != "/" else "/"), priority=priority)

    # A deep-link per active service + the products section (real, resolvable URLs).
    for s in crud.list_services(db, active_only=True):
        lm = s.created_at.date().isoformat() if getattr(s, "created_at", None) else now
        add(base_url + "/store#svc-" + s.slug, lastmod=lm, freq="monthly", priority="0.6")
    add(base_url + "/store#products", freq="monthly", priority="0.6")

    rows = "\n".join(
        "  <url>\n"
        "    <loc>{}</loc>\n"
        "    <lastmod>{}</lastmod>\n"
        "    <changefreq>{}</changefreq>\n"
        "    <priority>{}</priority>\n"
        "  </url>".format(_esc(loc), lastmod, freq, priority)
        for (loc, lastmod, freq, priority) in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + rows + "\n</urlset>\n")


# --- robots.txt ---------------------------------------------------------------
def build_robots(db, base_url=None, doc=None):
    doc = doc or get_doc(db)
    g = doc["general"]
    base_url = (base_url or g.get("base_url") or _BASE_URL).rstrip("/")
    custom = (g.get("robots_txt") or "").strip()
    sitemap_line = "Sitemap: {}/sitemap.xml".format(base_url)
    if custom:
        # Honour the developer's custom robots.txt, but guarantee the sitemap line.
        if "sitemap:" not in custom.lower():
            custom = custom + "\n\n" + sitemap_line
        return custom + "\n"
    # NB: Disallowing /api only tells *crawlers* not to index the JSON endpoints —
    # the website itself (browser fetch) is unaffected by robots.txt. Keeping it
    # disallowed avoids Google wasting crawl budget on / indexing raw API responses.
    return ("User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin\n"
            "Disallow: /app\n\n"
            + sitemap_line + "\n")
