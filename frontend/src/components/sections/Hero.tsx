/* Hero — animated entrance, count-up trust stats, and a parallax visual that
   drifts/scales on scroll (the "pinned storytelling" feel). Reduced-motion safe. */
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
  const visualY = useTransform(scrollYProgress, [0, 1], [0, reduce ? 0 : -70]);
  const visualScale = useTransform(scrollYProgress, [0, 1], [1, reduce ? 1 : 0.94]);
  const copyY = useTransform(scrollYProgress, [0, 1], [0, reduce ? 0 : 40]);
  const copyOpacity = useTransform(scrollYProgress, [0, 0.8], [1, reduce ? 1 : 0.3]);

  const container = {
    hidden: {},
    show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
  };
  const item = {
    hidden: reduce ? {} : { opacity: 0, y: 26 },
    show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: EASE } },
  };

  return (
    <section className="hero" id="hero" aria-label="Intro" ref={ref}>
      <div className="container hero-grid">
        <motion.div
          className="hero-copy"
          style={{ y: copyY, opacity: copyOpacity }}
          variants={container}
          initial="hidden"
          animate="show"
        >
          <motion.span className="status-pill" variants={item}>
            <span className="dot" />
            <span>{CONFIG.availability}</span>
          </motion.span>
          <motion.h1 variants={item}>
            I <span className="text-grad">build, automate &amp; design</span> the products that grow your business.
          </motion.h1>
          <motion.p className="lead" variants={item}>
            {CONFIG.bio}
          </motion.p>
          <motion.div className="hero-cta" variants={item}>
            <Link className="btn btn-primary" to="/store">
              Order a service
              <Icon name="arrow" size={18} />
            </Link>
            <Link className="btn btn-ghost" to="/contact">
              Request custom work
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
          aria-hidden="true"
          style={{ y: visualY, scale: visualScale }}
          initial={reduce ? false : { opacity: 0, y: 30, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.9, ease: EASE, delay: 0.15 }}
        >
          <div className="hero-card">
            <div className="win-dots"><span /><span /><span /></div>
            <div className="code-line w2" />
            <div className="code-line w1" />
            <div className="code-line w4" />
            <div className="code-line w3" />
            <div className="mini-chart">
              <span className="bar" style={{ height: "40%" }} />
              <span className="bar" style={{ height: "65%" }} />
              <span className="bar" style={{ height: "50%" }} />
              <span className="bar" style={{ height: "85%" }} />
              <span className="bar" style={{ height: "70%" }} />
              <span className="bar" style={{ height: "100%" }} />
            </div>
          </div>
          <div className="float-badge b1">
            <span className="ic"><Icon name="bot" size={20} /></span>
            Bots running 24/7
          </div>
          <div className="float-badge b2">
            <span className="ic"><Icon name="check" size={20} /></span>
            99% on-time delivery
          </div>
        </motion.div>
      </div>
    </section>
  );
}
