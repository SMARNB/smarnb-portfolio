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

export function PerksSection() {
  return (
    <section id="why" style={{ paddingTop: 0 }}>
      <div className="container">
        <div className="grid cols-4" id="perksGrid">
          {perks.map((p, i) => (
            <Reveal className="perk" key={p.title} delay={i * 0.07}>
              <div className="ic"><Icon name={p.icon} /></div>
              <div>
                <h3>{p.title}</h3>
                <p>{p.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

export function AboutSection() {
  const reduce = useReducedMotion();
  return (
    <section id="about">
      <div className="container about-grid">
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
        <Reveal delay={0.12}>
          <span className="eyebrow">About me</span>
          <h2 className="section-title">
            Hi, I'm <span>{CONFIG.name}</span> 👋
          </h2>
          <p className="lead">{CONFIG.bio}</p>
          <p className="lead mt-4" style={{ color: "var(--muted-2)" }}>{CONFIG.location}</p>
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
        </Reveal>
      </div>
    </section>
  );
}

export function ExperienceSection() {
  return (
    <section id="experience">
      <div className="container">
        <Reveal className="section-head">
          <span className="eyebrow">Experience</span>
          <h2 className="section-title">Where I've focused my time</h2>
          <p className="lead">A snapshot of my freelance work, key projects and education.</p>
        </Reveal>
        <div className="xp-list" id="experienceList">
          {experience.map((x, i) => (
            <Reveal className={`xp-item${x.current ? " current" : ""}`} key={x.role} delay={i * 0.08}>
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
            </Reveal>
          ))}
        </div>
      </div>
    </section>
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
