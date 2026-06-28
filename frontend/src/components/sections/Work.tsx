/* "Selected work" — category filters + portfolio grid with per-project SVG art;
   cards open the project modal. Port of renderFilters/renderPortfolio in app.js. */
import { useMemo, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { portfolio } from "../../lib/data";
import { Icon } from "../../lib/icons";
import { CAT_GRAD, DEFAULT_GRAD, PortfolioArt } from "../../lib/art";
import { Reveal } from "../ui/Reveal";
import { useUI } from "../../context/UIContext";

export function Work() {
  const reduce = useReducedMotion();
  const { openProject } = useUI();
  const [filter, setFilter] = useState("All");

  const cats = useMemo(
    () => ["All", ...Array.from(new Set(portfolio.map((p) => p.category)))],
    [],
  );
  const items = filter === "All" ? portfolio : portfolio.filter((p) => p.category === filter);

  return (
    <section id="work">
      <div className="container">
        <Reveal className="section-head center">
          <span className="eyebrow">Selected work</span>
          <h2 className="section-title">A look at recent projects</h2>
          <p className="lead" style={{ marginInline: "auto" }}>
            Real results across development, design, automation and packaging.
          </p>
        </Reveal>

        <div className="filter-row" id="workFilters">
          {cats.map((c) => (
            <button
              key={c}
              className={`filter-btn${filter === c ? " active" : ""}`}
              onClick={() => setFilter(c)}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="work-grid" id="workGrid">
          {items.map((p, i) => (
            <motion.article
              key={p.id}
              className="card work-card"
              tabIndex={0}
              role="button"
              aria-label={`View ${p.title}`}
              layout
              initial={reduce ? false : { opacity: 0, y: 26 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.15 }}
              transition={{ type: "spring", stiffness: 90, damping: 18, delay: reduce ? 0 : (i % 3) * 0.06 }}
              whileHover={reduce ? undefined : { y: -5 }}
              onClick={() => openProject(p.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  openProject(p.id);
                }
              }}
            >
              <div className="work-thumb">
                <span className="ph" style={{ background: CAT_GRAD[p.category] || DEFAULT_GRAD }} />
                <PortfolioArt p={p} />
                <span className="hover-go"><Icon name="arrow" size={18} /></span>
              </div>
              <div className="work-body">
                <span className="cat">{p.category}</span>
                <h3>{p.title}</h3>
                <p>{p.desc}</p>
                <div className="tag-row">
                  {p.tags.map((t) => (
                    <span className="tag" key={t}>{t}</span>
                  ))}
                </div>
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
