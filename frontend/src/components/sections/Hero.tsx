/* Hero — a proof-first thesis: a sharp value line with ONE primary action, and a
   real product (CodeWatch) framed as the visual instead of a fake IDE mockup.

   The entrance is PURE CSS (.hero-enter keyframes in global.css): both JS
   approaches stranded the first screen blank in the wild — a mount-time
   `animate` froze against a background tab's paused rAF, and the whileInView
   replacement still stalled its stagger orchestration on real fresh loads.
   CSS animations complete by declaration, so the hero can never be stuck
   hidden. Framer only drives the value-based scroll drift here (MotionValues
   have correct initial values and no animation lifecycle). Reduced-motion is
   handled in CSS for the entrance and inline for the drift. */
import { useRef } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { CONFIG } from "../../lib/config";
import { Icon } from "../../lib/icons";
import { CountUp } from "../ui/CountUp";
import { useCatalog } from "../../context/CatalogContext";

export function Hero() {
  const { services } = useCatalog();
  const reduce = useReducedMotion();
  const ref = useRef<HTMLElement>(null);

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  // Gentle, single-axis drift — the "scattered parallax" of the old hero is gone.
  const visualY = useTransform(scrollYProgress, [0, 1], [0, reduce ? 0 : -28]);
  const copyOpacity = useTransform(scrollYProgress, [0, 0.9], [1, reduce ? 1 : 0.6]);

  return (
    <section className="hero" id="hero" aria-label="Intro" ref={ref}>
      <div className="container hero-grid">
        <motion.div className="hero-copy hero-enter" style={{ opacity: copyOpacity }}>
          <span className="status-pill">
            <span className="dot" />
            <span>{CONFIG.availability}</span>
          </span>
          <h1>
            I <span className="text-grad">Design, Build &amp; Automate</span> production-ready software.
          </h1>
          <p className="lead">
            SaaS dashboards, Selenium &amp; OCR automation, computer-vision systems, and the
            interfaces &amp; packaging to match — taken from idea to delivery, on time.
          </p>
          <div className="hero-cta">
            <Link className="btn btn-primary" to="/store">
              Browse services &amp; pricing
              <Icon name="arrow" size={18} />
            </Link>
            <Link className="btn btn-ghost" to="/work">
              See my work
            </Link>
          </div>
          <div className="hero-stats" id="heroStats">
            {CONFIG.stats.map((s, i) => {
              const val = s.auto === "services" ? services.length : s.value;
              return (
                <div className="stat" key={i}>
                  <div className="stat-num">
                    <CountUp value={val} suffix={s.suffix} />
                  </div>
                  <div className="stat-label">{s.label}</div>
                </div>
              );
            })}
          </div>
        </motion.div>

        <motion.div className="hero-visual hero-enter-visual" style={{ y: visualY }}>
          <Link className="hero-shot" to="/projects" aria-label="See CodeWatch and other projects">
            <img
              src="/assets/img/codewatch-admin.jpg"
              alt="CodeWatch — AI liveness and surveillance dashboard"
              width={960}
              height={520}
              loading="eager"
              decoding="async"
            />
            <span className="hero-shot-scrim" aria-hidden="true" />
            <span className="hero-shot-cap">
              <span className="hero-shot-logo">
                <img src="/assets/img/codewatch-logo.svg" alt="" width={22} height={20} />
              </span>
              <span className="hero-shot-text">
                <b>CodeWatch</b>
                <small>AI liveness + surveillance · shipped to production</small>
              </span>
            </span>
          </Link>
          <span className="hero-shot-tag">LIVE PROJECT</span>
        </motion.div>
      </div>
    </section>
  );
}
