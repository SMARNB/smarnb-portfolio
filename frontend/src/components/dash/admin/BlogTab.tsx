/* Admin "Blog" tab — list posts, and a markdown editor with live (server-rendered)
   preview, cover + inline image upload, category/tags, and a draft/publish toggle.
   Posts are rendered to HTML server-side on save; the public /blog/<slug> page is
   server-rendered for crawlers. */
import { useCallback, useEffect, useRef, useState } from "react";
import { API } from "../../../lib/api";
import type { ApiError, BlogImageUpload, BlogPost, BlogPreview, PublicCatalog, ServiceOut } from "../../../lib/types";
import { csv, fmtDay } from "../../../lib/format";

const CATEGORIES = ["Tech", "Tech News", "Services"];

interface Draft {
  id?: number;
  title: string;
  slug: string;
  excerpt: string;
  body_md: string;
  cover_image: string;
  category: string;
  tags: string; // comma-separated in the editor
  related_services: string[]; // attached catalog service slugs
  status: string; // draft | published
}

const BLANK: Draft = {
  title: "",
  slug: "",
  excerpt: "",
  body_md: "",
  cover_image: "",
  category: "Tech",
  tags: "",
  related_services: [],
  status: "draft",
};

function toDraft(p: BlogPost): Draft {
  return {
    id: p.id,
    title: p.title,
    slug: p.slug,
    excerpt: p.excerpt,
    body_md: p.body_md || "",
    cover_image: p.cover_image,
    category: p.category,
    tags: (p.tags || []).join(", "),
    related_services: p.related_services || [],
    status: p.status,
  };
}

export function BlogTab({ onUnauth }: { onUnauth: () => void }) {
  const [list, setList] = useState<BlogPost[] | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState("");
  const [services, setServices] = useState<ServiceOut[]>([]);
  const bodyRef = useRef<HTMLTextAreaElement | null>(null);

  const fail = useCallback(
    (err: ApiError, fallback: string) => {
      if (err.status === 401 || err.status === 403) onUnauth();
      setStatus({ type: "err", msg: err.message || fallback });
    },
    [onUnauth],
  );

  const load = useCallback(() => {
    API.get<BlogPost[]>("/api/admin/blog")
      .then(setList)
      .catch((e: ApiError) => fail(e, "Couldn't load posts."));
  }, [fail]);

  useEffect(() => {
    load();
    // Catalog services to optionally attach to a post (shown in the post sidebar).
    API.get<PublicCatalog>("/api/services")
      .then((c) => setServices(c.services || []))
      .catch(() => {});
  }, [load]);

  /* Live preview — debounced server render so it matches production exactly. */
  useEffect(() => {
    if (!draft) return;
    const md = draft.body_md;
    const t = setTimeout(() => {
      API.post<BlogPreview>("/api/admin/blog/preview", { body_md: md })
        .then((r) => setPreview(r.body_html))
        .catch(() => {});
    }, 350);
    return () => clearTimeout(t);
  }, [draft]);

  function set<K extends keyof Draft>(k: K, v: Draft[K]) {
    setDraft((d) => (d ? { ...d, [k]: v } : d));
  }

  function toggleService(slug: string) {
    setDraft((d) =>
      d
        ? {
            ...d,
            related_services: d.related_services.includes(slug)
              ? d.related_services.filter((s) => s !== slug)
              : [...d.related_services, slug],
          }
        : d,
    );
  }

  function openNew() {
    setStatus(null);
    setPreview("");
    setDraft({ ...BLANK });
  }

  function openEdit(id: number) {
    setStatus(null);
    API.get<BlogPost>(`/api/admin/blog/${id}`)
      .then((p) => {
        setDraft(toDraft(p));
        setPreview(p.body_html || "");
      })
      .catch((e: ApiError) => fail(e, "Couldn't open that post."));
  }

  function save(publish?: boolean) {
    if (!draft) return;
    if (!draft.title.trim()) {
      setStatus({ type: "err", msg: "Give the post a title first." });
      return;
    }
    const payload = {
      title: draft.title.trim(),
      slug: draft.slug.trim(),
      excerpt: draft.excerpt.trim(),
      body_md: draft.body_md,
      cover_image: draft.cover_image.trim(),
      category: draft.category,
      tags: csv(draft.tags),
      related_services: draft.related_services,
      status: publish === undefined ? draft.status : publish ? "published" : "draft",
    };
    setSaving(true);
    setStatus({ type: "ok", msg: "Saving…" });
    const p = draft.id
      ? API.put<BlogPost>(`/api/admin/blog/${draft.id}`, payload)
      : API.post<BlogPost>("/api/admin/blog", payload);
    p.then((saved) => {
      setDraft(toDraft(saved));
      setStatus({
        type: "ok",
        msg: saved.status === "published" ? "Published — live on /blog now." : "Saved as draft.",
      });
      load();
    })
      .catch((e: ApiError) => fail(e, "Couldn't save."))
      .finally(() => setSaving(false));
  }

  function remove() {
    if (!draft?.id) {
      setDraft(null);
      return;
    }
    if (!window.confirm("Delete this post permanently?")) return;
    API.del(`/api/admin/blog/${draft.id}`)
      .then(() => {
        setDraft(null);
        setStatus({ type: "ok", msg: "Post deleted." });
        load();
      })
      .catch((e: ApiError) => fail(e, "Couldn't delete."));
  }

  function uploadCover(file: File) {
    API.upload<BlogImageUpload>("/api/admin/blog/images", file)
      .then((r) => set("cover_image", r.url))
      .catch((e: ApiError) => fail(e, "Image upload failed."));
  }

  function uploadInline(file: File) {
    API.upload<BlogImageUpload>("/api/admin/blog/images", file)
      .then((r) => {
        const snippet = `\n\n![${file.name.replace(/\.[^.]+$/, "")}](${r.url})\n\n`;
        setDraft((d) => (d ? { ...d, body_md: d.body_md + snippet } : d));
      })
      .catch((e: ApiError) => fail(e, "Image upload failed."));
  }

  /* ---- List view ---- */
  if (!draft) {
    return (
      <div className="card manage">
        <div className="blog-admin-head">
          <div>
            <h3 style={{ margin: 0 }}>Blog</h3>
            <p className="form-note" style={{ margin: ".2rem 0 0" }}>
              Write posts in markdown. Drafts stay private; published posts are server-rendered for
              search engines at <code>/blog/&lt;slug&gt;</code>.
            </p>
          </div>
          <button className="btn btn-primary" onClick={openNew}>
            + New post
          </button>
        </div>
        {status && <span className={`dash-status show ${status.type}`}>{status.msg}</span>}

        {!list && <p className="form-note">Loading…</p>}
        {list && list.length === 0 && <p className="form-note">No posts yet. Write your first one!</p>}

        <div className="blog-admin-list">
          {(list || []).map((p) => (
            <button key={p.id} className="blog-admin-row" onClick={() => openEdit(p.id)}>
              <span className={`blog-status ${p.status}`}>{p.status}</span>
              <span className="blog-admin-title">{p.title || "(untitled)"}</span>
              <span className="blog-admin-cat">{p.category}</span>
              <span className="blog-admin-date">
                {p.status === "published" ? fmtDay(p.published_at) : fmtDay(p.updated_at)}
              </span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  /* ---- Editor view ---- */
  return (
    <div className="card manage blog-editor">
      <div className="blog-admin-head">
        <button className="btn btn-outline btn-sm" onClick={() => setDraft(null)}>
          ← All posts
        </button>
        <div className="blog-editor-actions">
          {status && <span className={`dash-status show ${status.type}`}>{status.msg}</span>}
          <span className={`blog-status ${draft.status}`}>{draft.status}</span>
          <button className="btn btn-outline btn-sm" onClick={() => save(false)} disabled={saving}>
            Save draft
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => save(true)} disabled={saving}>
            {draft.status === "published" ? "Update" : "Publish"}
          </button>
        </div>
      </div>

      <div className="blog-editor-grid">
        {/* Left: fields + markdown */}
        <div className="blog-editor-main">
          <div className="field">
            <label>Title</label>
            <input
              className="input"
              value={draft.title}
              placeholder="An engaging, keyword-rich headline"
              onChange={(e) => set("title", e.target.value)}
            />
          </div>

          <div className="blog-editor-row">
            <div className="field">
              <label>Slug (URL)</label>
              <input
                className="input"
                value={draft.slug}
                placeholder="auto from title"
                onChange={(e) => set("slug", e.target.value)}
              />
            </div>
            <div className="field">
              <label>Category</label>
              <select className="input" value={draft.category} onChange={(e) => set("category", e.target.value)}>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="field">
            <label>Tags (comma-separated)</label>
            <input
              className="input"
              value={draft.tags}
              placeholder="python, automation, dashboards"
              onChange={(e) => set("tags", e.target.value)}
            />
          </div>

          <div className="field">
            <label>Excerpt (optional — auto-derived if blank)</label>
            <textarea
              className="textarea"
              rows={2}
              value={draft.excerpt}
              placeholder="A one or two sentence summary for cards & search snippets."
              onChange={(e) => set("excerpt", e.target.value)}
            />
          </div>

          <div className="field">
            <label>Cover image</label>
            <div className="blog-cover-row">
              <input
                className="input"
                value={draft.cover_image}
                placeholder="/api/blog/images/… or paste a URL"
                onChange={(e) => set("cover_image", e.target.value)}
              />
              <label className="btn btn-outline btn-sm file-btn">
                Upload
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/gif,image/webp"
                  hidden
                  onChange={(e) => e.target.files?.[0] && uploadCover(e.target.files[0])}
                />
              </label>
            </div>
            {draft.cover_image && <img className="blog-cover-preview" src={draft.cover_image} alt="" />}
          </div>

          <div className="field">
            <label>Related services (optional)</label>
            <p className="form-note" style={{ margin: "0 0 .5rem" }}>
              Attach services relevant to this post — they appear as a “Related services” sidebar on the
              article, turning readers into leads.
            </p>
            {services.length === 0 ? (
              <p className="form-note">No services yet — add them in the Services tab first.</p>
            ) : (
              <div className="blog-rel-picker">
                {services.map((s) => (
                  <label key={s.slug} className={`blog-rel-opt${draft.related_services.includes(s.slug) ? " on" : ""}`}>
                    <input
                      type="checkbox"
                      checked={draft.related_services.includes(s.slug)}
                      onChange={() => toggleService(s.slug)}
                    />
                    <span>{s.title}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="field">
            <label className="blog-body-label">
              <span>Body (markdown)</span>
              <label className="btn btn-outline btn-sm file-btn">
                Insert image
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/gif,image/webp"
                  hidden
                  onChange={(e) => e.target.files?.[0] && uploadInline(e.target.files[0])}
                />
              </label>
            </label>
            <textarea
              ref={bodyRef}
              className="textarea blog-md"
              rows={18}
              value={draft.body_md}
              placeholder={"# Heading\n\nWrite in **markdown** — headings, lists, links, `code`, tables and images all work."}
              onChange={(e) => set("body_md", e.target.value)}
            />
          </div>
        </div>

        {/* Right: live preview */}
        <div className="blog-editor-side">
          <div className="blog-preview-head">Live preview</div>
          <article className="post-body blog-preview" dangerouslySetInnerHTML={{ __html: preview }} />
          <button className="btn btn-ghost btn-sm blog-delete" onClick={remove}>
            {draft.id ? "Delete post" : "Discard"}
          </button>
        </div>
      </div>
    </div>
  );
}
