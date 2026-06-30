/* Single blog post (/blog/:slug). The FastAPI server already injects the full
   article + per-post meta/JSON-LD into the shell for crawlers; here we fetch the
   post for the live app (React replaces the server-rendered #root content on
   mount). Eager-imported (lives inside the animated PublicLayout shell). */
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { API } from "../lib/api";
import type { ApiError, BlogPost as Post } from "../lib/types";
import { Icon } from "../lib/icons";
import { fmtDay, money } from "../lib/format";

type State = "loading" | "ok" | "missing" | "error";

export function BlogPost() {
  const { slug } = useParams();
  const [post, setPost] = useState<Post | null>(null);
  const [state, setState] = useState<State>("loading");

  useEffect(() => {
    if (!slug) return;
    setState("loading");
    window.scrollTo({ top: 0 });
    API.get<Post>(`/api/blog/${slug}`)
      .then((p) => {
        setPost(p);
        setState("ok");
      })
      .catch((e: ApiError) => setState(e.status === 404 ? "missing" : "error"));
  }, [slug]);

  if (state === "loading") {
    return (
      <section id="post">
        <div className="container narrow">
          <p className="form-note">Loading…</p>
        </div>
      </section>
    );
  }

  if (state === "missing") {
    return (
      <section id="post">
        <div className="container narrow">
          <div className="blog-empty card">
            <h1>Post not found</h1>
            <p>This article may have been moved or unpublished.</p>
            <Link className="btn btn-outline" to="/blog">
              ← Back to the blog
            </Link>
          </div>
        </div>
      </section>
    );
  }

  if (state === "error" || !post) {
    return (
      <section id="post">
        <div className="container narrow">
          <p className="form-note">
            Couldn't load this post right now. <Link to="/blog">Back to the blog</Link>
          </p>
        </div>
      </section>
    );
  }

  const related = post.related || [];
  const hasAside = related.length > 0;

  return (
    <article id="post" className="post-page">
      <div className={`container post-shell${hasAside ? "" : " narrow"}`}>
        <div className={`post-layout${hasAside ? " has-aside" : ""}`}>
          <div className="post-main">
            <Link className="post-back" to="/blog">
              <span aria-hidden="true">←</span> Blog
            </Link>
            <p className="post-cat">{post.category}</p>
            <h1 className="post-title">{post.title}</h1>
            <div className="post-meta">
              {post.published_at && <span>{fmtDay(post.published_at)}</span>}
              {post.published_at && <span className="dotsep">·</span>}
              <span className="blog-read">
                <Icon name="clock" size={14} /> {post.reading_minutes} min read
              </span>
            </div>

            {post.cover_image && <img className="post-cover" src={post.cover_image} alt="" />}

            {/* body_html is rendered + sanitised server-side (mistune escape=True). */}
            <div className="post-body" dangerouslySetInnerHTML={{ __html: post.body_html || "" }} />

            {post.tags.length > 0 && (
              <div className="tag-row post-tags">
                {post.tags.map((t) => (
                  <span className="tag" key={t}>
                    #{t}
                  </span>
                ))}
              </div>
            )}

            <div className="post-cta card">
              <h3>Have a project like this?</h3>
              <p>I build SaaS dashboards, automation and computer-vision tools end to end.</p>
              <Link className="btn btn-primary" to="/contact">
                Start a conversation
              </Link>
            </div>
          </div>

          {hasAside && (
            <aside className="post-aside">
              <div className="card post-aside-card">
                <h3>Related services</h3>
                <p className="post-aside-sub">Want work like this? These are for hire.</p>
                <ul className="post-rel-list">
                  {related.map((s) => (
                    <li key={s.slug}>
                      <Link className="post-rel" to={`/store#svc-${s.slug}`}>
                        <span className="post-rel-cat">{s.category}</span>
                        <b>{s.title}</b>
                        {s.short && <span className="post-rel-short">{s.short}</span>}
                        {s.min_price != null && (
                          <span className="post-rel-price">from {money(s.min_price)}</span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
                <Link className="btn btn-outline btn-sm post-rel-all" to="/store">
                  Browse all services <Icon name="arrow" size={15} />
                </Link>
              </div>
            </aside>
          )}
        </div>
      </div>
    </article>
  );
}
