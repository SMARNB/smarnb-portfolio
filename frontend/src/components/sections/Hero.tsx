/* Hero — a proof-first thesis: a sharp value line with ONE primary action, and a
   real product (CodeWatch) framed as the visual instead of a fake IDE mockup. One
   restrained entrance + a gentle scroll drift; reduced-motion safe. */
import { useRef } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { CONFIG } from "../../lib/config";
import { Icon } from "../../lib/icons";
import { CountUp } from "../ui/CountUp";
import { useCatalog } from "../../context/CatalogContext";

const EASE = [0.22, 1, 0.36, 1] as const;

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

  const container = {
    hidden: {},
    show: { transition: { staggerChildren: 0.08, delayChildren: 0.04 } },
  };
  const item = {
    hidden: reduce ? {} : { opacity: 0, y: 22 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: EASE } },
  };

  return (
    <section className="hero" id="hero" aria-label="Intro" ref={ref}>
      <div className="container hero-grid">
        {/* whileInView, NOT animate: a mount-time animation started in a
            background tab runs against a frozen rAF and can strand the whole
            hero at opacity 0 (blank first screen). In-view triggering only
            fires once the page is actually visible. */}
        <motion.div
          className="hero-copy"
          style={{ opacity: copyOpacity }}
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.2 }}
        >
          <motion.span className="status-pill" variants={item}>
            <span className="dot" />
            <span>{CONFIG.availability}</span>
          </motion.span>
          <motion.h1 variants={item}>
            I <span className="text-grad">Design, Build &amp; Automate</span> production-ready software.
          </motion.h1>
          <motion.p className="lead" variants={item}>
            SaaS dashboards, Selenium &amp; OCR automation, computer-vision systems, and the
            interfaces &amp; packaging to match — taken from idea to delivery, on time.
          </motion.p>
          <motion.div className="hero-cta" variants={item}>
            <Link className="btn btn-primary" to="/store">
              Browse services &amp; pricing
              <Icon name="arrow" size={18} />
            </Link>
            <Link className="btn btn-ghost" to="/work">
              See my work
            </Link>
          </motion.div>
          <motion.div className="hero-stats" id="heroStats" variants={item}>
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
          </motion.div>
        </motion.div>

        <motion.div
          className="hero-visual"
          style={{ y: visualY }}
          initial={reduce ? false : { opacity: 0, y: 24, scale: 0.98 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.8, ease: EASE, delay: 0.12 }}
        >
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
