/* Contact — direct methods + a custom-request form that emails via Formspree
   (falls back to WhatsApp/mailto when no Formspree id). Ports initContactForm in
   app.js, including the project-modal message prefill. */
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { CONFIG } from "../../lib/config";
import { Icon } from "../../lib/icons";
import { validEmail, shortTitle, whatsappLink } from "../../lib/format";
import { sendMessage } from "../../lib/cart";
import { takeContactPrefill } from "../../lib/contactPrefill";
import { useCatalog } from "../../context/CatalogContext";
import { Reveal } from "../ui/Reveal";

export function Contact() {
  const { services } = useCatalog();
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const msgRef = useRef<HTMLTextAreaElement>(null);
  const wa = (CONFIG.whatsapp || "").replace(/\D/g, "");

  // Seed the message if a project CTA stashed one before navigating here.
  useEffect(() => {
    const pre = takeContactPrefill();
    if (pre && msgRef.current) msgRef.current.value = pre;
  }, []);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget;
    if ((f.elements.namedItem("_gotcha") as HTMLInputElement)?.value) return; // honeypot
    const name = (f.elements.namedItem("name") as HTMLInputElement).value.trim();
    const email = (f.elements.namedItem("email") as HTMLInputElement).value.trim();
    const message = (f.elements.namedItem("message") as HTMLTextAreaElement).value.trim();
    if (!name || !validEmail(email) || !message) {
      setStatus({ type: "err", msg: "Please fill in your name, a valid email, and your message." });
      return;
    }
    const payload = {
      _subject: "New project inquiry — " + CONFIG.brand,
      name,
      email,
      whatsapp: (f.elements.namedItem("whatsapp") as HTMLInputElement).value.trim(),
      service: (f.elements.namedItem("service") as HTMLSelectElement).value,
      budget: (f.elements.namedItem("budget") as HTMLSelectElement).value,
      timeline: (f.elements.namedItem("timeline") as HTMLSelectElement).value,
      message,
      _gotcha: "",
    };

    if (CONFIG.formspreeId) {
      setBusy(true);
      setStatus({ type: "ok", msg: "Sending…" });
      try {
        await sendMessage(payload);
        setStatus({ type: "ok", msg: `Thanks ${name}! Your request is on its way — I'll reply by email soon.` });
        f.reset();
      } catch {
        setStatus({ type: "err", msg: "Couldn't send right now. Please email or WhatsApp me directly (buttons on the left)." });
      } finally {
        setBusy(false);
      }
    } else {
      const text = `New inquiry from ${name} (${email})\nService: ${payload.service}\nBudget: ${payload.budget}\nTimeline: ${payload.timeline}\n\n${message}`;
      setStatus({ type: "ok", msg: "Opening WhatsApp to send your message…" });
      window.open(whatsappLink(text), "_blank", "noopener");
    }
  }

  return (
    <section id="contact">
      <div className="container">
        <Reveal className="section-head">
          <span className="eyebrow">Let's talk</span>
          <h2 className="section-title">Start your project or request a custom quote</h2>
          <p className="lead">
            Order standard services directly from the{" "}
            <Link to="/store" style={{ color: "var(--accent-2)", fontWeight: 600 }}>store</Link>. For custom work, send
            the details here or reach out directly — I usually reply within a day.
          </p>
        </Reveal>

        <div className="contact-grid">
          <Reveal style={{ display: "grid", gap: ".8rem", alignContent: "start" }}>
            <a className="contact-method" href={`mailto:${CONFIG.email}`}>
              <span className="ic"><Icon name="mail" size={22} /></span>
              <span><small>Email</small><b>{CONFIG.email}</b></span>
            </a>
            <a className="contact-method" href={`https://wa.me/${wa}`} target="_blank" rel="noopener">
              <span className="ic"><Icon name="whatsapp" size={22} /></span>
              <span><small>WhatsApp</small><b>+{wa}</b></span>
            </a>
            <div className="contact-method" style={{ cursor: "default" }}>
              <span className="ic">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <circle cx="12" cy="12" r="9" />
                  <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
                </svg>
              </span>
              <span><small>Working with</small><b>Clients worldwide · Remote</b></span>
            </div>
            <div className="card" style={{ marginTop: ".4rem" }}>
              <b>Prefer to order directly?</b>
              <p style={{ color: "var(--muted)", fontSize: ".92rem", marginTop: ".4rem" }}>
                Pick a package in the{" "}
                <Link to="/store" style={{ color: "var(--accent-2)", fontWeight: 600 }}>store</Link>, add it to your
                cart and check out. You'll get an order ID to track progress right here on the site.
              </p>
            </div>
          </Reveal>

          <Reveal delay={0.12}>
            <form className="form card" onSubmit={onSubmit} noValidate>
              <h3 style={{ fontSize: "1.2rem" }}>Tell me about your project</h3>
              <div className="two">
          <div className="field">
            <label htmlFor="cf-name">Name <span className="req">*</span></label>
            <input className="input" id="cf-name" name="name" required autoComplete="name" />
          </div>
          <div className="field">
            <label htmlFor="cf-email">Email <span className="req">*</span></label>
            <input className="input" id="cf-email" name="email" type="email" required autoComplete="email" />
          </div>
        </div>
        <div className="two">
          <div className="field">
            <label htmlFor="cf-whatsapp">WhatsApp <span style={{ color: "var(--muted)", fontWeight: 400 }}>(optional)</span></label>
            <input className="input" id="cf-whatsapp" name="whatsapp" autoComplete="tel" />
          </div>
          <div className="field">
            <label htmlFor="cf-service">Service</label>
            <select className="select" id="cf-service" name="service">
              <option value="">Select a service…</option>
              {services.map((s) => (
                <option key={s.id}>{shortTitle(s.title)}</option>
              ))}
              <option>Custom / Something else</option>
            </select>
          </div>
        </div>
        <div className="two">
          <div className="field">
            <label htmlFor="cf-budget">Budget</label>
            <select className="select" id="cf-budget" name="budget">
              <option value="">Select…</option>
              <option>Under $250</option>
              <option>$250–$1,000</option>
              <option>$1,000–$5,000</option>
              <option>$5,000+</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="cf-timeline">Timeline</label>
            <select className="select" id="cf-timeline" name="timeline">
              <option value="">Select…</option>
              <option>ASAP</option>
              <option>1–2 weeks</option>
              <option>This month</option>
              <option>Flexible</option>
            </select>
          </div>
        </div>
        <div className="field">
          <label htmlFor="cf-message">Project details <span className="req">*</span></label>
          <textarea className="textarea" id="cf-message" name="message" ref={msgRef} required placeholder="What are you building? Share goals, links, references, deadlines…" />
        </div>
        <input className="hp" tabIndex={-1} autoComplete="off" name="_gotcha" aria-hidden="true" placeholder="Leave this empty" />
        {status && <div className={`form-status show ${status.type}`}>{status.msg}</div>}
        <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
          <Icon name="mail" size={18} /> Send project request
        </button>
              <p className="form-note">Your details are only used to reply to you. No spam, ever.</p>
            </form>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
