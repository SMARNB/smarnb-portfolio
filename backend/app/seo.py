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
import os
import re
import time

from . import config, crud, models

# --- Defaults -----------------------------------------------------------------
_BASE_URL = (config.PUBLIC_BASE_URL or "https://smarnb.onrender.com").rstrip("/")

# The served static root (frontend/dist). main.py sets this at import so we can
# persist real sitemap.xml / robots.txt files there — a crawler reads a flat file
# with no database in the request path. None (e.g. in unit tests) disables writing.
STATIC_DIR = None

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
        # --- Marketing & analytics (OFF by default) ---------------------------
        # Empty => nothing loads and the site stays 100% first-party (the CSP is
        # byte-identical to the strict default). Set an ID and ONLY that vendor's
        # first-party loader (served from /marketing.js, so script-src stays 'self'
        # — no inline scripts) switches on, plus a minimal CSP allow-list for that
        # vendor's own domains. Pasting these later is how Google Ads / Analytics /
        # Meta promotion gets wired without ever weakening the baseline policy.
        "ga4_id": "",                   # Google Analytics 4 — "G-XXXXXXX"
        "gtm_id": "",                   # Google Tag Manager — "GTM-XXXXXXX"
        "google_ads_id": "",            # Google Ads (gtag) — "AW-XXXXXXXXX"
        "meta_pixel_id": "",            # Meta (Facebook) Pixel — numeric id
        "meta_domain_verification": "",  # Meta domain-verification token (inert meta)
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
        "/blog": {
            "title": "Blog — Notes on Code, Automation & Design",
            "description": (
                "Practical articles on full-stack development, Python automation, computer "
                "vision and design — written from real client and product work."),
            "canonical": "", "robots": "", "keywords": "",
            "og_title": "", "og_description": "", "og_image": "",
            "twitter_title": "", "twitter_description": "", "twitter_image": "",
            "breadcrumb": [{"name": "Home", "path": "/"}, {"name": "Blog", "path": "/blog"}],
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
    write_seo_files(db)   # refresh the on-disk sitemap.xml / robots.txt mirror
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
    # Blog index gets a Blog node listing recent published posts.
    if path == "/blog":
        posts = crud.list_blog_posts(db, published_only=True)
        if posts:
            graph.append({
                "@type": "Blog",
                "@id": base_url + "/blog#blog",
                "name": (g.get("site_name") or g.get("brand_name") or "") + " — Blog",
                "url": base_url + "/blog",
                "publisher": {"@id": base_url + "/#identity"},
                "blogPost": [{
                    "@type": "BlogPosting",
                    "headline": p.title or "",
                    "url": base_url + "/blog/" + p.slug,
                    **({"datePublished": p.published_at.isoformat()} if p.published_at else {}),
                } for p in posts[:20]],
            })
    return graph


# --- Marketing & analytics (opt-in, first-party loader + per-vendor CSP) ------
# Tag/pixel IDs are restricted to this safe alphabet so a value pulled from the DB
# can never break out of the JS string literals it's interpolated into, nor open
# the CSP for anything other than a legitimately-set id.
_ID_SAFE = re.compile(r"[^A-Za-z0-9_-]")


def _safe_id(v):
    return _ID_SAFE.sub("", str(v or "")).strip()


# Per-vendor CSP additions. When an id is set, exactly these hosts are appended to
# the matching directives — nothing else. With every id blank the CSP is unchanged.
_MARKETING_CSP = {
    "gtm_id": {
        "script-src": ["https://www.googletagmanager.com"],
        "img-src": ["https://www.googletagmanager.com", "https://www.google-analytics.com"],
        "connect-src": ["https://www.googletagmanager.com", "https://www.google-analytics.com",
                        "https://*.analytics.google.com"],
        "frame-src": ["https://www.googletagmanager.com"],
    },
    "ga4_id": {
        "script-src": ["https://www.googletagmanager.com"],
        "img-src": ["https://www.googletagmanager.com", "https://www.google-analytics.com",
                    "https://*.analytics.google.com"],
        "connect-src": ["https://www.googletagmanager.com", "https://www.google-analytics.com",
                        "https://*.analytics.google.com"],
    },
    "google_ads_id": {
        "script-src": ["https://www.googletagmanager.com", "https://www.googleadservices.com"],
        "img-src": ["https://www.googleadservices.com", "https://googleads.g.doubleclick.net"],
        "connect-src": ["https://www.google-analytics.com"],
        "frame-src": ["https://td.doubleclick.net", "https://googleads.g.doubleclick.net"],
    },
    "meta_pixel_id": {
        "script-src": ["https://connect.facebook.net"],
        "img-src": ["https://www.facebook.com"],
        "connect-src": ["https://www.facebook.com"],
        "frame-src": ["https://www.facebook.com"],
    },
}
_MARKETING_IDS = ("ga4_id", "gtm_id", "google_ads_id", "meta_pixel_id")


def marketing_enabled(g):
    """True if any analytics/marketing id is set (so a vendor loader should run)."""
    return any(_safe_id(g.get(k)) for k in _MARKETING_IDS)


def _marketing_head(g):
    """Head fragments for marketing: the inert Meta domain-verification meta (if set)
    and a single first-party <script src="/marketing.js"> loader (only when at least
    one id is set). Returns [] when the site is fully first-party."""
    out = []
    fb_verify = (g.get("meta_domain_verification") or "").strip()
    if fb_verify:
        out.append(_meta("facebook-domain-verification", fb_verify))
    if marketing_enabled(g):
        # The bootstrap lives in a same-origin file so script-src stays 'self' (no
        # inline scripts, no 'unsafe-inline'); it loads the vendor SDKs itself.
        out.append('<script src="/marketing.js" defer></script>')
    return out


def marketing_csp(doc):
    """{directive: [extra hosts]} to merge into the CSP for the set ids. Empty when
    the site is fully first-party."""
    g = (doc or {}).get("general", {})
    add = {}
    for key, groups in _MARKETING_CSP.items():
        if not _safe_id(g.get(key)):
            continue
        for directive, hosts in groups.items():
            bucket = add.setdefault(directive, [])
            for h in hosts:
                if h not in bucket:
                    bucket.append(h)
    return add


def csp_with_marketing(base_csp, doc):
    """The CSP for the current settings. Byte-identical to ``base_csp`` when no id is
    set; otherwise each set vendor's domains are appended to exactly its directives
    (script-src/img-src/connect-src/frame-src). A brand-new directive (frame-src) is
    seeded with 'self' so same-origin framing still behaves."""
    add = marketing_csp(doc)
    if not add:
        return base_csp
    order = []
    index = {}
    for part in base_csp.split(";"):
        part = part.strip()
        if not part:
            continue
        name, *tokens = part.split()
        index[name] = tokens
        order.append(name)
    for directive, hosts in add.items():
        if directive in index:
            for h in hosts:
                if h not in index[directive]:
                    index[directive].append(h)
        else:
            index[directive] = ["'self'"] + list(hosts)
            order.append(directive)
    return "; ".join(name + " " + " ".join(index[name]) for name in order)


def build_marketing_js(doc=None, db=None):
    """The first-party bootstrap JS served at /marketing.js, generated from the set
    ids. Loads gtag (GA4 + Google Ads), GTM and the Meta Pixel via their own SDKs.
    Returns a harmless comment when nothing is enabled."""
    if doc is None:
        doc = get_doc(db) if db is not None else {"general": {}}
    g = doc.get("general", {})
    ga4, ads = _safe_id(g.get("ga4_id")), _safe_id(g.get("google_ads_id"))
    gtm, pixel = _safe_id(g.get("gtm_id")), _safe_id(g.get("meta_pixel_id"))
    blocks = []
    gtag_ids = [i for i in (ga4, ads) if i]
    if gtag_ids:
        ids = ",".join("'" + i + "'" for i in gtag_ids)
        blocks.append(
            "(function(){var ids=[" + ids + "];var s=document.createElement('script');"
            "s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+ids[0];"
            "document.head.appendChild(s);window.dataLayer=window.dataLayer||[];"
            "window.gtag=function(){dataLayer.push(arguments);};gtag('js',new Date());"
            "ids.forEach(function(i){gtag('config',i);});})();")
    if gtm:
        blocks.append(
            "(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),"
            "event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),"
            "dl=l!='dataLayer'?'&l='+l:'';j.async=true;"
            "j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;"
            "f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','" + gtm + "');")
    if pixel:
        blocks.append(
            "!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
            "n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;"
            "n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;"
            "t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}"
            "(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
            "fbq('init','" + pixel + "');fbq('track','PageView');")
    if not blocks:
        return "/* Marketing analytics are off. Add IDs in the dashboard SEO tab to enable. */\n"
    return ("/* First-party marketing loader — generated from dashboard SEO settings. */\n"
            + "\n".join(blocks) + "\n")


# --- Head rendering (per route) ----------------------------------------------
def _resolve_meta(g, base_url, path, meta):
    """Resolve the final per-page values (title, description, canonical, robots,
    Open Graph + Twitter) from a route/post meta dict overlaid on the defaults."""
    page_title = meta.get("title") or g.get("default_title")
    tmpl = g.get("title_template") or "%s"
    full_title = tmpl.replace("%s", page_title) if "%s" in tmpl else page_title
    # The home page title is usually already the full brand title.
    if path == "/" and meta.get("title"):
        full_title = meta["title"]
    desc = meta.get("description") or g.get("default_description")
    og_image = _abs(base_url, meta.get("og_image") or g.get("default_og_image"))
    return {
        "full_title": full_title,
        "desc": desc,
        "keywords": meta.get("keywords") or g.get("default_keywords"),
        "robots": meta.get("robots") or g.get("robots_default") or "index, follow",
        "canonical": meta.get("canonical") or (base_url + (path if path != "default" else "/")),
        "og_type": meta.get("og_type") or g.get("og_type") or "website",
        "og_title": meta.get("og_title") or page_title,
        "og_desc": meta.get("og_description") or desc,
        "og_image": og_image,
        "tw_title": meta.get("twitter_title") or meta.get("og_title") or page_title,
        "tw_desc": meta.get("twitter_description") or meta.get("og_description") or desc,
        "tw_image": _abs(base_url, meta.get("twitter_image") or meta.get("og_image") or g.get("default_og_image")),
    }


def _emit_head(g, r, graph):
    """Build the managed <head> fragment from resolved values ``r`` + a JSON-LD
    ``graph`` list. Shared by the per-route and per-blog-post renderers."""
    parts = [
        "<title>{}</title>".format(_esc(r["full_title"])),
        _meta("description", r["desc"]),
        _meta("keywords", r["keywords"]),
        _meta("author", g.get("author")),
        _meta("robots", r["robots"]),
        '<link rel="canonical" href="{}">'.format(_esc(r["canonical"])),
        _meta("theme-color", g.get("theme_color")),
        # Open Graph
        _meta("og:type", r["og_type"], prop=True),
        _meta("og:site_name", g.get("site_name") or g.get("brand_name"), prop=True),
        _meta("og:title", r["og_title"], prop=True),
        _meta("og:description", r["og_desc"], prop=True),
        _meta("og:url", r["canonical"], prop=True),
        _meta("og:image", r["og_image"], prop=True),
        _meta("og:locale", g.get("locale") or "en_US", prop=True),
        # Twitter
        _meta("twitter:card", g.get("twitter_card") or "summary_large_image"),
        _meta("twitter:title", r["tw_title"]),
        _meta("twitter:description", r["tw_desc"]),
        _meta("twitter:image", r["tw_image"]),
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
    # Marketing/analytics loader + verification meta — only when ids are set.
    parts.extend(_marketing_head(g))
    if graph:
        ld = {"@context": "https://schema.org", "@graph": graph}
        # </ is escaped so the JSON can never close the <script> element early.
        payload = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
        parts.append('<script type="application/ld+json">{}</script>'.format(payload))
    return "\n  ".join(p for p in parts if p)


def render_head(db, path, doc=None):
    """The managed ``<head>`` HTML fragment for ``path``: title, description,
    canonical, robots, Open Graph, Twitter cards, verification tags, theme-color,
    icons, manifest and a JSON-LD ``@graph`` script — all from the DB."""
    doc = doc or get_doc(db)
    g = doc["general"]
    base_url = (g.get("base_url") or _BASE_URL).rstrip("/")
    r = _resolve_meta(g, base_url, path, _effective(doc, path))
    return _emit_head(g, r, build_jsonld(db, path, doc=doc))


# --- Blog posts (per-slug head + crawlable article) ---------------------------
def _ld_blogposting(post, g, base_url):
    url = base_url + "/blog/" + post.slug
    node = {
        "@type": "BlogPosting",
        "headline": post.title or "",
        "description": post.excerpt or "",
        "url": url,
        "mainEntityOfPage": url,
        "author": {"@id": base_url + "/#identity"},
        "publisher": {"@id": base_url + "/#identity"},
        "inLanguage": g.get("language") or "en",
        "dateModified": (post.updated_at or post.published_at or models.utcnow()).isoformat(),
    }
    if post.published_at:
        node["datePublished"] = post.published_at.isoformat()
    if post.cover_image:
        node["image"] = _abs(base_url, post.cover_image)
    if post.category:
        node["articleSection"] = post.category
    if post.tags:
        node["keywords"] = ", ".join(post.tags)
    return node


def render_blog_post_head(db, slug, doc=None):
    """The managed <head> for a published post at /blog/<slug>, or None if the slug
    is unknown / still a draft (caller falls back to the blog-index head)."""
    post = crud.get_blog_post(db, slug)
    if not post or post.status != "published":
        return None
    doc = doc or get_doc(db)
    g = doc["general"]
    base_url = (g.get("base_url") or _BASE_URL).rstrip("/")
    url = base_url + "/blog/" + post.slug
    cover = post.cover_image or g.get("default_og_image")
    meta = {
        "title": post.title, "description": post.excerpt or g.get("default_description"),
        "canonical": url, "robots": "index, follow",
        "keywords": ", ".join(post.tags) if post.tags else "",
        "og_title": post.title, "og_description": post.excerpt or "", "og_image": cover,
        "twitter_title": post.title, "twitter_description": post.excerpt or "", "twitter_image": cover,
        "og_type": "article",
        "breadcrumb": [{"name": "Home", "path": "/"}, {"name": "Blog", "path": "/blog"},
                       {"name": post.title, "path": "/blog/" + post.slug}],
    }
    r = _resolve_meta(g, base_url, "/blog/" + slug, meta)
    toggles = g.get("jsonld", {})
    graph = []
    if toggles.get("website", True):
        graph.append(_ld_website(g, base_url))
    if toggles.get("person", True):
        graph.append(_ld_identity(g, base_url, db))
    if toggles.get("breadcrumb", True):
        bc = _ld_breadcrumb(meta, base_url)
        if bc:
            graph.append(bc)
    graph.append(_ld_blogposting(post, g, base_url))
    return _emit_head(g, r, graph)


def blog_article_html(db, slug):
    """Server-rendered article HTML for a published post, injected into the SPA
    shell's #root so crawlers see the full post (React replaces it on mount).
    Returns "" for an unknown / draft slug."""
    post = crud.get_blog_post(db, slug)
    if not post or post.status != "published":
        return ""
    g = get_doc(db)["general"]
    base_url = (g.get("base_url") or _BASE_URL).rstrip("/")
    out = ['<article class="post-article">',
           '<p class="post-cat">{}</p>'.format(_esc(post.category)),
           "<h1>{}</h1>".format(_esc(post.title))]
    if post.excerpt:
        out.append('<p class="post-excerpt">{}</p>'.format(_esc(post.excerpt)))
    if post.cover_image:
        out.append('<img class="post-cover" src="{}" alt="{}">'.format(
            _esc(_abs(base_url, post.cover_image)), _esc(post.title)))
    # post.body_html is already escaped/safe (rendered with mistune escape=True).
    out.append('<div class="post-body">{}</div>'.format(post.body_html or ""))
    # Related services — real internal links (crawlable, strengthen site structure).
    related = crud.blog_related_services(db, post)
    if related:
        out.append('<aside class="post-related"><h2>Related services</h2><ul>')
        for s in related:
            out.append('<li><a href="{}">{}</a></li>'.format(
                _esc(base_url + "/store#svc-" + s["slug"]), _esc(s["title"])))
        out.append("</ul></aside>")
    out.append("</article>")
    return "".join(out)


# --- Per-path cache (rendered head HTML) --------------------------------------
_cache = {}
_csp_cache = {}      # base_csp -> computed CSP string (changes only on save)
_mkt_js_cache = {}   # "js" -> /marketing.js body (changes only on save)
_TTL = 300  # seconds; JSON-LD reflects approved reviews/services, refreshed often enough


def clear_cache():
    _cache.clear()
    _csp_cache.clear()
    _mkt_js_cache.clear()


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


def cached_blog_post_head(db, slug):
    """render_blog_post_head with the same short TTL as routes. Misses (unknown /
    draft slugs) are not cached so a freshly-published post appears immediately."""
    key = "blogpost:" + slug
    now = time.time()
    hit = _cache.get(key)
    if hit and hit[0] > now:
        return hit[1]
    frag = render_blog_post_head(db, slug)
    if frag is None:
        return None
    _cache[key] = (now + _TTL, frag)
    return frag


def cached_marketing_js(db):
    """The /marketing.js body, cached until the next SEO save."""
    hit = _mkt_js_cache.get("js")
    if hit is not None:
        return hit
    val = build_marketing_js(db=db)
    _mkt_js_cache["js"] = val
    return val


def cached_csp(base_csp):
    """The Content-Security-Policy for the current settings, cached until the next
    save. Opens its own short-lived DB session only on a cache miss; any failure
    falls back to the strict first-party ``base_csp`` (never weaker, never down)."""
    hit = _csp_cache.get(base_csp)
    if hit is not None:
        return hit
    try:
        from .database import SessionLocal
        db = SessionLocal()
        try:
            val = csp_with_marketing(base_csp, get_doc(db))
        finally:
            db.close()
    except Exception:
        return base_csp  # don't cache the fallback — retry next request
    _csp_cache[base_csp] = val
    return val


# --- sitemap.xml --------------------------------------------------------------
def build_sitemap(db, base_url=None, doc=None):
    # Crash-proof: a cold/suspended database (Neon free tier auto-suspends) must
    # never make the sitemap error or hang — Google fail-closes the whole site if
    # it can't read it. So the route pages always render from settings/defaults,
    # and only the DB-derived extras (service deep-links, blog posts) are best-effort.
    if doc is None:
        try:
            doc = get_doc(db)
        except Exception:
            doc = copy.deepcopy(DEFAULT_DOC)
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

    # The products section (static, always resolvable).
    add(base_url + "/store#products", freq="monthly", priority="0.6")

    try:
        # A deep-link per active service + every published blog post (real,
        # indexable URLs). Best-effort so a DB hiccup still yields the core routes.
        for s in crud.list_services(db, active_only=True):
            lm = s.created_at.date().isoformat() if getattr(s, "created_at", None) else now
            add(base_url + "/store#svc-" + s.slug, lastmod=lm, freq="monthly", priority="0.6")
        for p in crud.list_blog_posts(db, published_only=True):
            lm_dt = p.published_at or p.updated_at
            lm = lm_dt.date().isoformat() if lm_dt else now
            add(base_url + "/blog/" + p.slug, lastmod=lm, priority="0.7")
    except Exception:
        pass

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
    if doc is None:
        try:
            doc = get_doc(db)
        except Exception:
            doc = copy.deepcopy(DEFAULT_DOC)
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


# --- Physical file mirror -----------------------------------------------------
def write_seo_files(db):
    """Persist the current sitemap.xml + robots.txt as real files in the served
    static root (STATIC_DIR = frontend/dist). This is a first-party mirror of the
    live routes: a plain, valid file exists on disk that anyone (or Google) can read
    without touching the database, and it self-refreshes on boot and whenever SEO
    settings or blog posts change. Best-effort — a failure just leaves the previous
    copy (or the build-time committed baseline in frontend/public) in place, and the
    live routes still serve the freshly generated document regardless."""
    if not STATIC_DIR or not os.path.isdir(STATIC_DIR):
        return
    try:
        with open(os.path.join(STATIC_DIR, "sitemap.xml"), "w", encoding="utf-8") as fh:
            fh.write(build_sitemap(db))
        with open(os.path.join(STATIC_DIR, "robots.txt"), "w", encoding="utf-8") as fh:
            fh.write(build_robots(db))
    except Exception:
        pass
