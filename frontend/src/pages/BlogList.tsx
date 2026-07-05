/* Blog index (/blog) — a real, crawlable list of published posts with category
   filters. Eager-imported (lives inside the animated PublicLayout shell). */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { API } from "../lib/api";
import type { BlogListResponse, BlogPost as Post } from "../lib/types";
import { Reveal } from "../components/ui/Reveal";
import { TeaserHead } from "../components/ui/TeaserHead";
import { Icon } from "../lib/icons";
import { fmtDay } from "../lib/format";

export function BlogList({ home = false }: { home?: boolean }) {
  const [data, setData] = useState<BlogListResponse | null>(null);
  const [cat, setCat] = useState("All");
  const [error, setError] = useState("");

  useEffect(() => {
    API.get<BlogListResponse>("/api/blog")
      .then(setData)
      .catch(() => setError("Couldn't load posts right now — please try again in a moment."));
  }, []);

  const cats = useMemo(() => ["All", ...(data?.categories || [])], [data]);
  const posts = useMemo(() => {
    const all = data?.posts || [];
    return cat === "All" ? all : all.filter((p) => p.category === cat);
  }, [data, cat]);

  // Home preview: at most 3 recent posts + a link to the full blog. Renders
  // nothing until there is at least one published post.
  if (home) {
    if (!data || data.posts.length === 0) return null;
    return (
      <section id="blog">
        <div className="container">
          <TeaserHead eyebrow="Blog" title="From the blog" to="/blog" label="See all posts" />
          <div className="blog-grid">
            {data.posts.slice(0, 3).map((p, i) => (
              <BlogCard key={p.slug} p={p} i={i} />
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="blog">
      <div className="container">
        <Reveal className="section-head center">
          <span className="eyebrow">Blog</span>
          <h1 className="section-title">Notes on code, automation &amp; design</h1>
          <p className="lead" style={{ marginInline: "auto" }}>
            Practical write-ups from real client and product work — full-stack development, Python
            automation, computer vision and design.
          </p>
        </Reveal>

        {data && data.posts.length > 0 && (
          <div className="filter-row">
            {cats.map((c) => (
              <button
                key={c}
                className={`filter-btn${cat === c ? " active" : ""}`}
                onClick={() => setCat(c)}
              >
                {c}
              </button>
            ))}
          </div>
        )}

        {error && <p className="form-note">{error}</p>}

        {data && posts.length === 0 && !error && (
          <div className="blog-empty card">
            <Icon name="pen" size={26} />
            <h3>No posts yet</h3>
            <p>New articles are on the way — check back soon.</p>
          </div>
        )}

        <div className="blog-grid">
          {posts.map((p, i) => (
            <BlogCard key={p.slug} p={p} i={i} />
          ))}
        </div>
      </div>
    </section>
  );
}

function BlogCard({ p, i }: { p: Post; i: number }) {
  return (
    <Reveal as="article" className="card blog-card" delay={(i % 3) * 0.06}>
      <Link to={`/blog/${p.slug}`} className="blog-card-link" aria-label={p.title}>
        <div className="blog-thumb">
          {p.cover_image ? (
            <img src={p.cover_image} alt="" loading="lazy" />
          ) : (
            <span className="blog-thumb-ph">
              <Icon name="pen" size={26} />
            </span>
          )}
          <span className="blog-chip">{p.category}</span>
        </div>
        <div className="blog-body">
          <h2>{p.title}</h2>
          <p>{p.excerpt}</p>
          <div className="blog-meta">
            {p.published_at && <span>{fmtDay(p.published_at)}</span>}
            {p.published_at && <span className="dotsep">·</span>}
            <span className="blog-read">
              <Icon name="clock" size={13} /> {p.reading_minutes} min read
            </span>
          </div>
        </div>
      </Link>
    </Reveal>
  );
}
