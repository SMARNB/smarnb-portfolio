/* Mostly-static Home sections: tech marquee, process, perks, about, experience,
   CTA band, payments. Scroll-reveal via <Reveal>; skill bars animate width when
   they enter the viewport. Ports the matching renderers in app.js. */
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { CONFIG } from "../../lib/config";
import { Icon } from "../../lib/icons";
import { process, perks, experience, skills } from "../../lib/data";
import { Reveal } from "../ui/Reveal";

const TECH = [
  "Python", "FastAPI", "Django", "React", "Selenium", "OCR", "Figma",
  "PostgreSQL", "Docker", "Stripe", "Pandas", "UI/UX", "Packaging", "3D Mockups",
];

export function Marquee() {
  const items = TECH.map((t, i) => (
    <span key={i}>
      <Icon name="spark" style={{ display: "inline", width: 14, height: 14, verticalAlign: -2, color: "var(--muted-2)" }} /> {t}
    </span>
  ));
  // Four identical groups: the track animates by exactly one group (-25%), so the
  // loop is seamless AND never leaves an empty gap on wide screens (where a single
  // group is narrower than the viewport). Each group carries its own trailing gap.
  return (
    <div className="marquee" aria-label="Tools and technologies">
      <div className="marquee-track" id="marqueeTrack">
        {[0, 1, 2, 3].map((g) => (
          <div className="marquee-group" key={g} aria-hidden={g > 0}>
            {items}
          </div>
        ))}
      </div>
    </div>
  );
}

export function ProcessSection() {
  return (
    <section id="process">
      <div className="container">
        <Reveal className="section-head center">
          <span className="eyebrow">How it works</span>
          <h2 className="section-title">A simple, transparent process</h2>
          <p className="lead" style={{ marginInline: "auto" }}>
            From first hello to final delivery, you always know what's happening next.
          </p>
        </Reveal>
        <div className="steps" id="processSteps">
          {process.map((s, i) => (
            <Reveal className="step" key={s.title} delay={i * 0.08}>
              <span className="num">{i + 1}</span>
              <div className="ic"><Icon name={s.icon} /></div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---- About page blocks (sticky portrait + stacking content cards) -------- */

/** Sticky column: the portrait stays put while the content moves; visitors can
 *  download the CV from here. (The PDF is a static asset — regenerate it from
 *  /admin → Résumé and replace frontend/public/assets/cv/ when facts change.) */
export function AboutPortrait() {
  return (
    <div>
      <Reveal className="about-photo">
        <svg className="avatar" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21a8 8 0 0 1 16 0" />
        </svg>
        <img
          className="photo-img"
          src={CONFIG.photo}
          alt={CONFIG.name}
          width={760}
          height={892}
          loading="lazy"
          decoding="async"
        />
      </Reveal>
      <div className="about-cv">
        <a
          className="btn btn-ghost"
          href="/assets/cv/Muhammad-Ali-Raza-CV.pdf"
          download="Muhammad-Ali-Raza-CV.pdf"
        >
          <Icon name="download" size={18} />
          Download CV (PDF)
        </a>
      </div>
    </div>
  );
}

export function AboutIntroBlock() {
  return (
    <div className="about-block">
      <span className="eyebrow">About me</span>
      <h2 className="section-title">
        Hi, I'm <span className="text-grad">{CONFIG.name}</span>
      </h2>
      <p className="lead mt-2">{CONFIG.bio}</p>
      <p className="lead mt-4" style={{ color: "var(--muted-2)" }}>{CONFIG.location}</p>
    </div>
  );
}

export function AboutSkillsBlock() {
  const reduce = useReducedMotion();
  return (
    <div className="about-block">
      <span className="eyebrow">Core skills</span>
      <h2 className="section-title">What I work in every day</h2>
      <div className="skills" id="skillsList">
        {skills.map((s) => (
          <div className="skill" key={s.name}>
            <div className="skill-head">
              <span>{s.name}</span>
              <span>{s.level}%</span>
            </div>
            <div className="skill-bar">
              <motion.span
                className="skill-fill"
                initial={reduce ? false : { width: 0 }}
                whileInView={{ width: `${s.level}%` }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AboutXpBlock() {
  return (
    <div className="about-block">
      <span className="eyebrow">Experience</span>
      <h2 className="section-title">Where I've focused my time</h2>
      <div className="xp-list" id="experienceList" style={{ marginTop: "1.1rem" }}>
        {experience.map((x) => (
          <div className={`xp-item${x.current ? " current" : ""}`} key={x.role}>
            <span className="xp-dot" />
            <div className="xp-card">
              <div className="xp-head">
                <div>
                  <h3>{x.role}</h3>
                  <p className="xp-org">{x.org}</p>
                </div>
                <span className="xp-period">{x.period}</span>
              </div>
              <p className="xp-desc">{x.desc}</p>
              <div className="tag-row">
                {(x.tags || []).map((t) => (
                  <span className="tag" key={t}>{t}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AboutPerksBlock() {
  return (
    <div className="about-block">
      <span className="eyebrow">What you get</span>
      <h2 className="section-title">How I work with clients</h2>
      <div className="grid cols-2" id="perksGrid" style={{ marginTop: "1.1rem" }}>
        {perks.map((p) => (
          <div className="perk" key={p.title}>
            <div className="ic"><Icon name={p.icon} /></div>
            <div>
              <h3>{p.title}</h3>
              <p>{p.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function CtaBand() {
  return (
    <section id="cta">
      <div className="container">
        <Reveal className="cta-band">
          <h2>Have a project in mind?</h2>
          <p>Let's turn your idea into something real — fast, polished, and on time.</p>
          <div className="hero-cta" style={{ justifyContent: "center" }}>
            <Link className="btn btn-ghost" to="/store">Browse packages</Link>
            <Link className="btn btn-outline" to="/contact">Start a conversation</Link>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

export function PaymentsSection() {
  const groups: Record<string, typeof CONFIG.payments> = {};
  CONFIG.payments.forEach((p) => {
    (groups[p.group] = groups[p.group] || []).push(p);
  });
  return (
    <section id="payments">
      <div className="container">
        <Reveal className="card pay-band">
          <div className="pay-head">
            <span className="eyebrow" style={{ marginBottom: ".6rem" }}>Payments</span>
            <h3>Pay your way — local &amp; global</h3>
            <p className="lead">
              Local Pakistani methods (Raast, SadaPay, JazzCash), buy-now-pay-later, or international transfers. Pick a
              method at checkout; I'll send secure payment details to confirm.
            </p>
          </div>
          <div className="pay-groups">
            {Object.keys(groups).map((g) => (
              <div className="pay-group" key={g}>
                <h4>{g}</h4>
                {groups[g].map((p) => (
                  <div className="pay-chip" key={p.id}>
                    <Icon name="card" size={18} />
                    <span>{p.label}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
