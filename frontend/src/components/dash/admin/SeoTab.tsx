/* SEO control centre — manage the COMPLETE SEO of the site for every search
   engine from the dashboard, never by editing code. Loads the SEO document
   (GET /api/seo), edits every facet in place, and saves it (PUT /api/admin/seo).
   The FastAPI server injects the resulting tags + JSON-LD into the HTML <head>
   per route before serving, so crawlers see them without running JS.

   Includes live guidance: Google SERP + social-card previews, title/description
   character counters with limits, a per-route "what's set / what's missing"
   checklist, plain-English help on every field, and step-by-step submission
   instructions. */
import { useCallback, useEffect, useMemo, useState } from "react";
import { API } from "../../../lib/api";
import type { ApiError, SeoDoc, SeoGeneral, SeoRouteMeta, SeoJsonLd } from "../../../lib/types";

const TITLE_LIMIT = 60;
const DESC_LIMIT = 160;
const ROUTE_ORDER = ["/", "/store", "default", "/app", "/admin"];
const ROUTE_LABEL: Record<string, string> = {
  "/": "Home (/)",
  "/store": "Store (/store)",
  default: "Default (fallback)",
  "/app": "Client area (/app)",
  "/admin": "Developer (/admin)",
};

/* ---------- small presentational helpers ---------------------------------- */
function Help({ children }: { children: React.ReactNode }) {
  return <p className="seo-help">{children}</p>;
}

function Counter({ value, limit }: { value: string; limit: number }) {
  const n = (value || "").length;
  const cls = n === 0 ? "warn" : n <= limit ? "ok" : n <= limit * 1.12 ? "near" : "over";
  return (
    <span className={`seo-counter ${cls}`}>
      {n}/{limit}
      {n > limit ? " · too long" : n === 0 ? " · empty" : ""}
    </span>
  );
}

function Field({
  label,
  help,
  children,
  counter,
}: {
  label: string;
  help?: React.ReactNode;
  children: React.ReactNode;
  counter?: React.ReactNode;
}) {
  return (
    <div className="field seo-field">
      <label className="seo-label">
        <span>{label}</span>
        {counter}
      </label>
      {children}
      {help && <Help>{help}</Help>}
    </div>
  );
}

function CheckRow({ ok, label, hint }: { ok: boolean; label: string; hint?: string }) {
  return (
    <li className={`seo-check ${ok ? "ok" : "bad"}`}>
      <span className="seo-check-dot">{ok ? "✓" : "!"}</span>
      <span>
        {label}
        {!ok && hint ? <em> — {hint}</em> : null}
      </span>
    </li>
  );
}

/* ---------- effective-value resolver (mirrors backend app/seo.py) --------- */
function effective(doc: SeoDoc, path: string) {
  const g = doc.general;
  const r = doc.routes[path] || doc.routes.default;
  const pageTitle = r.title || g.default_title;
  const tmpl = g.title_template || "%s";
  let fullTitle = tmpl.includes("%s") ? tmpl.replace("%s", pageTitle) : pageTitle;
  if (path === "/" && r.title) fullTitle = r.title;
  const base = (g.base_url || "").replace(/\/$/, "");
  const desc = r.description || g.default_description;
  const canonical = r.canonical || base + (path === "default" ? "/" : path);
  const robots = r.robots || g.robots_default || "index, follow";
  const ogTitle = r.og_title || pageTitle;
  const ogDesc = r.og_description || desc;
  const ogImage = r.og_image || g.default_og_image;
  return { pageTitle, fullTitle, desc, canonical, robots, ogTitle, ogDesc, ogImage, base };
}

function absUrl(base: string, url: string) {
  if (!url) return "";
  if (/^(https?:)?\/\//.test(url)) return url;
  return base.replace(/\/$/, "") + "/" + url.replace(/^\//, "");
}

/* ========================================================================== */
export function SeoTab({ onUnauth }: { onUnauth: () => void }) {
  const [doc, setDoc] = useState<SeoDoc | null>(null);
  const [route, setRoute] = useState<string>("/");
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    API.get<SeoDoc>("/api/seo")
      .then(setDoc)
      .catch((err: ApiError) => {
        if (err.status === 401 || err.status === 403) onUnauth();
      });
  }, [onUnauth]);

  useEffect(() => {
    load();
  }, [load]);

  /* ---- mutators ---- */
  const setG = (k: keyof SeoGeneral, v: unknown) =>
    setDoc((d) => (d ? { ...d, general: { ...d.general, [k]: v } } : d));
  const setJsonld = (k: keyof SeoJsonLd, v: boolean) =>
    setDoc((d) => (d ? { ...d, general: { ...d.general, jsonld: { ...d.general.jsonld, [k]: v } } } : d));
  const setR = (k: keyof SeoRouteMeta, v: unknown) =>
    setDoc((d) => {
      if (!d) return d;
      const cur = d.routes[route] || d.routes.default;
      return { ...d, routes: { ...d.routes, [route]: { ...cur, [k]: v } } };
    });

  function save() {
    if (!doc) return;
    setSaving(true);
    setStatus({ type: "ok", msg: "Saving…" });
    API.put<SeoDoc>("/api/admin/seo", doc)
      .then((saved) => {
        setDoc(saved);
        setStatus({ type: "ok", msg: "Saved. Crawlers see the new tags on the next request." });
      })
      .catch((err: ApiError) => {
        if (err.status === 401 || err.status === 403) onUnauth();
        setStatus({ type: "err", msg: err.message || "Could not save." });
      })
      .finally(() => setSaving(false));
  }

  const eff = useMemo(() => (doc ? effective(doc, route) : null), [doc, route]);

  if (!doc || !eff) return <div className="card manage"><p className="form-note">Loading SEO settings…</p></div>;

  const g = doc.general;
  const r = doc.routes[route] || doc.routes.default;
  const rIndexable = !/noindex/i.test(eff.robots);
  const robotsParts = eff.robots.toLowerCase();
  const indexSel = /noindex/.test(robotsParts) ? "noindex" : "index";
  const followSel = /nofollow/.test(robotsParts) ? "nofollow" : "follow";

  function setRobots(idx: string, fol: string) {
    setR("robots", `${idx}, ${fol}`);
  }

  return (
    <div className="seo-tab">
      {/* Sticky action bar */}
      <div className="seo-bar card">
        <div>
          <h3 style={{ margin: 0 }}>SEO control centre</h3>
          <p className="form-note" style={{ margin: ".2rem 0 0" }}>
            Manage every search-engine tag here — no code edits. The server injects them into the page
            for crawlers and serves a live sitemap &amp; robots.
          </p>
        </div>
        <div className="seo-bar-actions">
          {status && <span className={`dash-status show ${status.type}`}>{status.msg}</span>}
          <button className="btn btn-primary" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save SEO settings"}
          </button>
        </div>
      </div>

      {/* Route selector */}
      <div className="card manage">
        <h4 className="seo-h">1 · Choose a page to optimise</h4>
        <Help>
          On-page meta is set per route. Tune the <b>Home</b> and <b>Store</b> pages first — those are what
          you want ranking. <b>Default</b> is the fallback for any other path. The client/developer areas are
          intentionally <b>noindex</b> (private tools, not content).
        </Help>
        <div className="seo-route-tabs">
          {ROUTE_ORDER.filter((p) => doc.routes[p]).map((p) => (
            <button key={p} className={route === p ? "active" : ""} onClick={() => setRoute(p)}>
              {ROUTE_LABEL[p] || p}
            </button>
          ))}
        </div>
      </div>

      <div className="seo-cols">
        {/* LEFT: editors */}
        <div className="seo-col-main">
          {/* On-page meta */}
          <section className="card manage">
            <h4 className="seo-h">2 · On-page meta — {ROUTE_LABEL[route] || route}</h4>

            <Field
              label="Page title"
              counter={<Counter value={effective(doc, route).pageTitle} limit={TITLE_LIMIT} />}
              help={
                <>
                  The clickable headline in Google. Lead with your strongest keyword, keep it under ~
                  {TITLE_LIMIT} characters so it isn't cut off, and make each page's title unique. Site name is
                  appended automatically via the template below.
                </>
              }
            >
              <input
                className="input"
                value={r.title}
                placeholder={g.default_title}
                onChange={(e) => setR("title", e.target.value)}
              />
            </Field>

            <Field
              label="Meta description"
              counter={<Counter value={effective(doc, route).desc} limit={DESC_LIMIT} />}
              help={
                <>
                  The snippet under the title. It doesn't directly affect ranking but drives click-through —
                  write a compelling ~{DESC_LIMIT}-char summary with a benefit and a keyword. Leave blank to use
                  the site default.
                </>
              }
            >
              <textarea
                className="textarea"
                value={r.description}
                placeholder={g.default_description}
                onChange={(e) => setR("description", e.target.value)}
              />
            </Field>

            <div className="seo-2col">
              <Field
                label="Indexing"
                help="“index” lets this page appear in search; “noindex” hides it. Keep content pages indexed."
              >
                <select className="input" value={indexSel} onChange={(e) => setRobots(e.target.value, followSel)}>
                  <option value="index">index (show in search)</option>
                  <option value="noindex">noindex (hide from search)</option>
                </select>
              </Field>
              <Field
                label="Link following"
                help="“follow” passes ranking signals through this page's links. Usually keep “follow”."
              >
                <select className="input" value={followSel} onChange={(e) => setRobots(indexSel, e.target.value)}>
                  <option value="follow">follow links</option>
                  <option value="nofollow">nofollow links</option>
                </select>
              </Field>
            </div>

            <Field
              label="Canonical URL"
              help={
                <>
                  The single “official” URL for this page — prevents duplicate-content issues. Leave blank to
                  auto-use <code>{eff.canonical}</code>.
                </>
              }
            >
              <input
                className="input"
                value={r.canonical}
                placeholder={eff.canonical}
                onChange={(e) => setR("canonical", e.target.value)}
              />
            </Field>

            <Field
              label="Keywords (optional)"
              help="Google ignores this tag, but Bing/Yandex still read it lightly. A short, honest comma list won't hurt. Your real targeting happens in the title, headings & content."
            >
              <input
                className="input"
                value={r.keywords}
                placeholder={g.default_keywords}
                onChange={(e) => setR("keywords", e.target.value)}
              />
            </Field>
          </section>

          {/* Social cards */}
          <section className="card manage">
            <h4 className="seo-h">3 · Social sharing (Open Graph &amp; Twitter)</h4>
            <Help>
              Controls how a link to this page looks when shared on Facebook, LinkedIn, WhatsApp, X, etc. Blank
              fields fall back to the page title/description and the site's default image.
            </Help>
            <Field label="OG / Social title" help="Headline on the share card. Defaults to the page title.">
              <input className="input" value={r.og_title} placeholder={eff.ogTitle} onChange={(e) => setR("og_title", e.target.value)} />
            </Field>
            <Field label="OG / Social description" help="Share-card text. Defaults to the meta description.">
              <textarea className="textarea" value={r.og_description} placeholder={eff.ogDesc} onChange={(e) => setR("og_description", e.target.value)} />
            </Field>
            <Field
              label="Share image URL"
              help={
                <>
                  The big preview image (ideal 1200×630). Use a same-origin path like <code>/og-image.svg</code>{" "}
                  or an absolute URL. Defaults to the site image.
                </>
              }
            >
              <input className="input" value={r.og_image} placeholder={g.default_og_image} onChange={(e) => setR("og_image", e.target.value)} />
            </Field>
          </section>

          {/* FAQ editor */}
          <section className="card manage">
            <h4 className="seo-h">4 · FAQ (powers FAQ rich results)</h4>
            <Help>
              These questions render as a <b>FAQPage</b> structured-data block on the home page — Google can show
              them as expandable Q&amp;A directly in search results. Keep answers concise and genuinely useful.
            </Help>
            {doc.faq.map((f, i) => (
              <div className="seo-faq-row" key={i}>
                <input
                  className="input"
                  value={f.q}
                  placeholder="Question"
                  onChange={(e) =>
                    setDoc((d) => (d ? { ...d, faq: d.faq.map((x, j) => (j === i ? { ...x, q: e.target.value } : x)) } : d))
                  }
                />
                <textarea
                  className="textarea"
                  value={f.a}
                  placeholder="Answer"
                  onChange={(e) =>
                    setDoc((d) => (d ? { ...d, faq: d.faq.map((x, j) => (j === i ? { ...x, a: e.target.value } : x)) } : d))
                  }
                />
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => setDoc((d) => (d ? { ...d, faq: d.faq.filter((_, j) => j !== i) } : d))}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              className="btn btn-outline btn-sm"
              onClick={() => setDoc((d) => (d ? { ...d, faq: [...d.faq, { q: "", a: "" }] } : d))}
            >
              + Add FAQ
            </button>
          </section>
        </div>

        {/* RIGHT: live previews + health */}
        <div className="seo-col-side">
          <section className="card manage seo-sticky">
            <h4 className="seo-h">Google result preview</h4>
            <div className="serp-preview">
              <div className="serp-url">{eff.canonical.replace(/^https?:\/\//, "").replace(/\/$/, "")}</div>
              <div className="serp-title">{truncate(eff.fullTitle, 65)}</div>
              <div className="serp-desc">{truncate(eff.desc, 165)}</div>
            </div>

            <h4 className="seo-h" style={{ marginTop: "1.2rem" }}>Social card preview</h4>
            <div className="social-card">
              {absUrl(eff.base, eff.ogImage) ? (
                <img src={absUrl(eff.base, eff.ogImage)} alt="" className="social-img" />
              ) : (
                <div className="social-img social-img-empty">No share image</div>
              )}
              <div className="social-body">
                <div className="social-domain">{eff.base.replace(/^https?:\/\//, "")}</div>
                <div className="social-title">{truncate(eff.ogTitle, 70)}</div>
                <div className="social-desc">{truncate(eff.ogDesc, 110)}</div>
              </div>
            </div>

            <h4 className="seo-h" style={{ marginTop: "1.2rem" }}>Health check — {ROUTE_LABEL[route] || route}</h4>
            <ul className="seo-checklist">
              <CheckRow ok={!!r.title && effective(doc, route).pageTitle.length <= TITLE_LIMIT} label="Title set & ≤ 60 chars"
                hint={!r.title ? "add a unique title" : "shorten it"} />
              <CheckRow ok={eff.desc.length >= 50 && eff.desc.length <= DESC_LIMIT} label="Description 50–160 chars"
                hint="aim for ~150 chars" />
              <CheckRow ok={!!eff.canonical} label="Canonical URL present" />
              <CheckRow ok={rIndexable} label="Indexable (not noindex)"
                hint="this page is hidden from search" />
              <CheckRow ok={!!absUrl(eff.base, eff.ogImage)} label="Share image set" hint="add an OG image" />
            </ul>
            <ul className="seo-checklist">
              <CheckRow ok={!!g.google_verification} label="Google verification token" hint="add it below" />
              <CheckRow ok={(g.same_as || []).filter(Boolean).length > 0} label="Social profiles (sameAs)" hint="link your profiles" />
              <CheckRow ok={g.jsonld.reviews} label="Review rich-results on" />
              <CheckRow ok={!!g.target_keywords} label="Target keywords noted" />
            </ul>
          </section>
        </div>
      </div>

      {/* Global / site-wide settings (full width) */}
      <section className="card manage">
        <h4 className="seo-h">5 · Site-wide identity &amp; templates</h4>
        <div className="seo-2col">
          <Field label="Site name" help="Your brand, appended to page titles and used as og:site_name.">
            <input className="input" value={g.site_name} onChange={(e) => setG("site_name", e.target.value)} />
          </Field>
          <Field label="Title template" help={<>How titles are assembled. <code>%s</code> is the page title — e.g. <code>%s · SMARNB</code>.</>}>
            <input className="input" value={g.title_template} onChange={(e) => setG("title_template", e.target.value)} />
          </Field>
          <Field label="Base URL" help="Your canonical domain. Used to build absolute canonical/OG URLs, the sitemap and robots.">
            <input className="input" value={g.base_url} onChange={(e) => setG("base_url", e.target.value)} />
          </Field>
          <Field label="Author" help="Shown as the page author meta and JSON-LD founder.">
            <input className="input" value={g.author} onChange={(e) => setG("author", e.target.value)} />
          </Field>
          <Field label="Language / locale" help="e.g. language “en”, locale “en_US”. Helps engines serve the right audience.">
            <div style={{ display: "flex", gap: ".5rem" }}>
              <input className="input" value={g.language} onChange={(e) => setG("language", e.target.value)} placeholder="en" />
              <input className="input" value={g.locale} onChange={(e) => setG("locale", e.target.value)} placeholder="en_US" />
            </div>
          </Field>
          <Field label="Default share image" help="Fallback OG/Twitter image when a page doesn't set its own (1200×630 ideal).">
            <input className="input" value={g.default_og_image} onChange={(e) => setG("default_og_image", e.target.value)} />
          </Field>
        </div>
        <Field label="Default description" counter={<Counter value={g.default_description} limit={DESC_LIMIT} />}
          help="Used on any page without its own description.">
          <textarea className="textarea" value={g.default_description} onChange={(e) => setG("default_description", e.target.value)} />
        </Field>
        <div className="seo-2col">
          <Field label="Twitter card type" help="“summary_large_image” shows a big image; “summary” a small one.">
            <select className="input" value={g.twitter_card} onChange={(e) => setG("twitter_card", e.target.value)}>
              <option value="summary_large_image">summary_large_image</option>
              <option value="summary">summary</option>
            </select>
          </Field>
          <Field label="Twitter @site" help="Your brand's X/Twitter handle (with @). Optional.">
            <input className="input" value={g.twitter_site} onChange={(e) => setG("twitter_site", e.target.value)} placeholder="@yourhandle" />
          </Field>
          <Field label="Twitter @creator" help="The author's handle. Optional.">
            <input className="input" value={g.twitter_creator} onChange={(e) => setG("twitter_creator", e.target.value)} placeholder="@yourhandle" />
          </Field>
          <Field label="Theme color" help="Browser UI / address-bar tint on mobile and PWA.">
            <input className="input" value={g.theme_color} onChange={(e) => setG("theme_color", e.target.value)} placeholder="#0a0d14" />
          </Field>
          <Field label="Favicon" help="Tab icon path (SVG/PNG/ICO), same-origin.">
            <input className="input" value={g.favicon} onChange={(e) => setG("favicon", e.target.value)} />
          </Field>
          <Field label="Web app manifest" help="PWA manifest path (theme, icons, name).">
            <input className="input" value={g.manifest} onChange={(e) => setG("manifest", e.target.value)} />
          </Field>
        </div>
      </section>

      {/* Structured data identity */}
      <section className="card manage">
        <h4 className="seo-h">6 · Business identity (Person / ProfessionalService JSON-LD)</h4>
        <Help>
          This is the structured “knowledge graph” data engines use to understand who you are — it can power a
          rich business card in search. Built from real values below, plus your live services and approved
          reviews. Toggle individual blocks on the right.
        </Help>
        <div className="seo-2col">
          <Field label="Schema type" help="“ProfessionalService” suits a freelance service business; “Person” for a personal brand.">
            <select className="input" value={g.org_type} onChange={(e) => setG("org_type", e.target.value)}>
              <option value="ProfessionalService">ProfessionalService</option>
              <option value="Organization">Organization</option>
              <option value="Person">Person</option>
            </select>
          </Field>
          <Field label="Name" help="Your name or business name.">
            <input className="input" value={g.person_name} onChange={(e) => setG("person_name", e.target.value)} />
          </Field>
          <Field label="Job title" help="e.g. “Full-Stack Developer & Designer”.">
            <input className="input" value={g.job_title} onChange={(e) => setG("job_title", e.target.value)} />
          </Field>
          <Field label="Email" help="Public contact email for the business card.">
            <input className="input" value={g.email} onChange={(e) => setG("email", e.target.value)} />
          </Field>
          <Field label="Telephone / WhatsApp" help="Contact number in international format, e.g. +92 341 4527256.">
            <input className="input" value={g.telephone} onChange={(e) => setG("telephone", e.target.value)} />
          </Field>
          <Field label="Area served" help="Where you work, e.g. “Worldwide” or “Pakistan & remote”.">
            <input className="input" value={g.area_served} onChange={(e) => setG("area_served", e.target.value)} />
          </Field>
          <Field label="Price range" help="A rough indicator like “$$” or “$150–$1500”.">
            <input className="input" value={g.price_range} onChange={(e) => setG("price_range", e.target.value)} />
          </Field>
          <Field label="Logo" help="Logo/brand image path for the business card.">
            <input className="input" value={g.logo} onChange={(e) => setG("logo", e.target.value)} />
          </Field>
          <Field label="Image" help="A representative photo/image (e.g. your profile).">
            <input className="input" value={g.image} onChange={(e) => setG("image", e.target.value)} />
          </Field>
        </div>
        <Field
          label="Social profiles (sameAs) — one URL per line"
          help="Link every official profile (GitHub, LinkedIn, X, Instagram, Fiverr…). This is how engines connect your site to your identity — a strong trust signal."
        >
          <textarea
            className="textarea"
            rows={4}
            value={(g.same_as || []).join("\n")}
            placeholder={"https://github.com/SMARNB\nhttps://linkedin.com/in/…"}
            onChange={(e) => setG("same_as", e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))}
          />
        </Field>

        <div className="seo-toggles">
          <b style={{ width: "100%" }}>JSON-LD blocks to emit:</b>
          {([
            ["website", "WebSite"],
            ["person", "Person / Service"],
            ["services", "Service catalogue"],
            ["reviews", "Reviews + rating"],
            ["faq", "FAQ"],
            ["breadcrumb", "Breadcrumbs"],
            ["search_action", "Sitelinks search box"],
          ] as [keyof SeoJsonLd, string][]).map(([k, label]) => (
            <label key={k} className="seo-toggle">
              <input type="checkbox" checked={g.jsonld[k]} onChange={(e) => setJsonld(k, e.target.checked)} /> {label}
            </label>
          ))}
        </div>
        <Help>
          Reviews + rating build an <b>AggregateRating</b> and <b>Review</b> list from your <b>approved</b>{" "}
          testimonials only. The service catalogue emits a <b>Service</b> (with price <b>Offer</b>) per active
          service. Don't mark up reviews you can't substantiate — that violates Google's guidelines.
        </Help>
      </section>

      {/* Verification */}
      <section className="card manage">
        <h4 className="seo-h">7 · Search-engine verification</h4>
        <Help>
          To submit your sitemap and see search data, you must prove you own the site. Paste only the{" "}
          <b>content token</b> from each provider's “HTML tag” method (not the whole tag) — it's injected into
          the <code>&lt;head&gt;</code> on save.
        </Help>
        <div className="seo-2col">
          <Field label="Google Search Console" help="Search Console → Settings → Ownership → HTML tag → copy the content value.">
            <input className="input" value={g.google_verification} onChange={(e) => setG("google_verification", e.target.value)} placeholder="abc123…" />
          </Field>
          <Field label="Bing Webmaster Tools" help="Bing Webmaster → add site → “Add a meta tag” → copy the content value.">
            <input className="input" value={g.bing_verification} onChange={(e) => setG("bing_verification", e.target.value)} placeholder="ABCDEF…" />
          </Field>
          <Field label="Yandex Webmaster" help="Yandex Webmaster → add site → Meta tag → copy the content value.">
            <input className="input" value={g.yandex_verification} onChange={(e) => setG("yandex_verification", e.target.value)} placeholder="0123…" />
          </Field>
        </div>
      </section>

      {/* Sitemap + robots */}
      <section className="card manage">
        <h4 className="seo-h">8 · Sitemap &amp; robots</h4>
        <Help>
          Your <a href="/sitemap.xml" target="_blank" rel="noopener">sitemap.xml</a> and{" "}
          <a href="/robots.txt" target="_blank" rel="noopener">robots.txt</a> are generated live from your routes,
          services and products — no static files to maintain.
        </Help>
        <div className="seo-2col">
          <Field label="Sitemap change frequency" help="A hint to crawlers about how often content pages change.">
            <select className="input" value={g.sitemap_changefreq} onChange={(e) => setG("sitemap_changefreq", e.target.value)}>
              {["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"].map((f) => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
          </Field>
        </div>
        <Field
          label="Custom robots.txt (optional)"
          help="Leave blank for the recommended default (allow all; disallow /admin, /app, /api; reference the sitemap). If you customise it, the sitemap line is added automatically."
        >
          <textarea className="textarea" rows={5} value={g.robots_txt}
            placeholder={"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /app\nDisallow: /api/"}
            onChange={(e) => setG("robots_txt", e.target.value)} />
        </Field>
      </section>

      {/* Targeting + guidance */}
      <section className="card manage">
        <h4 className="seo-h">9 · Target keywords &amp; how to rank</h4>
        <Field
          label="Target keywords (what you want to rank for)"
          help="A note to yourself — comma-separated phrases your buyers actually search (e.g. “python saas dashboard developer”, “selenium automation freelancer”)."
        >
          <textarea className="textarea" rows={3} value={g.target_keywords} onChange={(e) => setG("target_keywords", e.target.value)} />
        </Field>
        <div className="seo-guide">
          <div>
            <b>Where to use each keyword</b>
            <ul>
              <li>In the <b>page title</b> (near the front) and the <b>meta description</b>.</li>
              <li>In one <b>H1</b> and a few <b>H2</b> headings, naturally.</li>
              <li>In the first 100 words of body copy and in image alt text.</li>
              <li>In the URL/anchor where possible. Don't stuff — write for humans first.</li>
            </ul>
          </div>
          <div>
            <b>Submit your sitemap (do this once)</b>
            <ol>
              <li>Add &amp; verify your site in <b>Google Search Console</b> (paste the token in section 7, save here, then click Verify there).</li>
              <li>In Search Console → <b>Sitemaps</b>, submit <code>sitemap.xml</code>.</li>
              <li>Repeat in <b>Bing Webmaster Tools</b> (you can import from Google).</li>
              <li>Request indexing for your Home &amp; Store URLs to speed things up.</li>
            </ol>
          </div>
          <div>
            <b>Performance &amp; mobile (Core Web Vitals)</b>
            <ul>
              <li>Speed is a ranking factor. Your Render free tier <b>sleeps</b> after ~15 min — first load can take 1–3 min, which hurts crawl &amp; UX. Keep it warm (see the keep-alive workflow).</li>
              <li>Compress hero/share images and prefer SVG where possible.</li>
              <li>The site is already mobile-responsive — verify with Google's Mobile-Friendly test after deploy.</li>
              <li>Check <b>PageSpeed Insights</b> for LCP/CLS/INP once warm.</li>
            </ul>
          </div>
        </div>
      </section>

      <div className="seo-bar card seo-bar-bottom">
        {status && <span className={`dash-status show ${status.type}`}>{status.msg}</span>}
        <button className="btn btn-primary" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save SEO settings"}
        </button>
      </div>
    </div>
  );
}

function truncate(s: string, n: number) {
  s = s || "";
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}
