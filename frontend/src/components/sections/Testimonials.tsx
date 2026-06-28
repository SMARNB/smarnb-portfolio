/* Testimonials grid (approved client reviews prepended to samples) + a collapsible
   "leave a review" form that posts to /api/testimonials. Ports renderTestimonials
   + initReviewForm in app.js. */
import { useState } from "react";
import { CONFIG } from "../../lib/config";
import { Icon } from "../../lib/icons";
import { useTestimonials } from "../../lib/useTestimonials";
import { Reveal } from "../ui/Reveal";

function initials(name: string): string {
  return name.split(" ").map((w) => w[0]).join("").slice(0, 2);
}

export function Testimonials() {
  const list = useTestimonials();

  return (
    <section id="reviews">
      <div className="container">
        <Reveal className="section-head center">
          <span className="eyebrow">Client love</span>
          <h2 className="section-title">What clients say</h2>
          <p className="lead" style={{ marginInline: "auto" }}>
            A few words from people I've worked with — and you can add yours below.
          </p>
        </Reveal>

        <div className="grid cols-3" id="testimonialsGrid">
          {list.map((t, i) => (
            <Reveal className="card tcard" key={`${t.name}-${i}`} as="article" delay={(i % 3) * 0.06}>
              <div className="stars">
                {Array.from({ length: t.rating }).map((_, k) => (
                  <Icon name="star" key={k} size={18} />
                ))}
              </div>
              <p>“{t.text}”</p>
              <div className="tperson">
                <span className="av">{initials(t.name)}</span>
                <span>
                  <b>{t.name}</b>
                  <small>{t.role}{t.loc ? ` · ${t.loc}` : ""}</small>
                </span>
              </div>
            </Reveal>
          ))}
        </div>

        <div className="review-cta">
          <ReviewForm />
        </div>
      </div>
    </section>
  );
}

function ReviewForm() {
  const [rating, setRating] = useState(5);
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget;
    if ((f.elements.namedItem("company") as HTMLInputElement)?.value) return; // honeypot
    const name = (f.elements.namedItem("name") as HTMLInputElement).value.trim();
    const text = (f.elements.namedItem("text") as HTMLTextAreaElement).value.trim();
    if (name.length < 2 || text.length < 10) {
      setStatus({ type: "err", msg: "Please add your name and a few words." });
      return;
    }
    const payload = {
      name,
      role: (f.elements.namedItem("role") as HTMLInputElement).value.trim(),
      location: (f.elements.namedItem("location") as HTMLInputElement).value.trim(),
      rating,
      text,
      company: "",
    };
    setBusy(true);
    setStatus({ type: "", msg: "Sending…" });
    try {
      const r = await fetch((CONFIG.apiBase || "") + "/api/testimonials", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (!r.ok) throw new Error((d && d.detail) || "Could not submit.");
      setStatus({ type: "ok", msg: d.message || "Thank you! Your review will appear once approved." });
      f.reset();
      setRating(5);
    } catch (err) {
      setStatus({ type: "err", msg: (err as Error).message || "Could not submit — is the backend running?" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <details className="review-box">
      <summary className="btn btn-outline">★ Leave a review</summary>
      <form className="form card review-form" onSubmit={onSubmit} noValidate>
        <h3 style={{ fontSize: "1.15rem" }}>Share your experience</h3>
        <p className="form-note" style={{ marginTop: "-.3rem" }}>
          Worked with me? I'd love your feedback. Reviews appear on the site once approved.
        </p>
        <div className="two">
          <div className="field">
            <label htmlFor="rv-name">Name <span className="req">*</span></label>
            <input className="input" id="rv-name" name="name" required autoComplete="name" />
          </div>
          <div className="field">
            <label htmlFor="rv-role">Role / company</label>
            <input className="input" id="rv-role" name="role" placeholder="e.g. SaaS Founder" />
          </div>
        </div>
        <div className="two">
          <div className="field">
            <label htmlFor="rv-location">Location</label>
            <input className="input" id="rv-location" name="location" placeholder="e.g. Dubai, UAE 🇦🇪" />
          </div>
          <div className="field">
            <label>Rating</label>
            <div className="star-pick" role="radiogroup" aria-label="Rating">
              {[1, 2, 3, 4, 5].map((v) => (
                <button
                  type="button"
                  key={v}
                  className={v <= rating ? "on" : ""}
                  aria-label={`${v} star${v > 1 ? "s" : ""}`}
                  aria-checked={v === rating}
                  onClick={() => setRating(v)}
                >
                  ★
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="field">
          <label htmlFor="rv-text">Your review <span className="req">*</span></label>
          <textarea className="textarea" id="rv-text" name="text" required placeholder="What did we build together? How was the experience?" />
        </div>
        <input className="hp" tabIndex={-1} autoComplete="off" name="company" aria-hidden="true" placeholder="Leave this empty" />
        {status && <div className={`form-status show ${status.type}`}>{status.msg}</div>}
        <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
          Submit review
        </button>
      </form>
    </details>
  );
}
