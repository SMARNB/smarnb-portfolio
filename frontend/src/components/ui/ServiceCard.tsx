/* Service card — neutral media header, an uppercase category label + a quiet
   "from" price chip, title/blurb/tags, and the single accent element: the
   "View packages" CTA. Shared by the Home teaser and the Store grid. Calm
   fade + rise reveal (reduced-motion aware). */
import { motion, useReducedMotion } from "framer-motion";
import { Icon } from "../../lib/icons";
import { ServiceArt } from "../../lib/art";
import { money } from "../../lib/format";
import type { Service } from "../../lib/data";

export function ServiceCard({ s, index, onView }: { s: Service; index: number; onView: (id: string) => void }) {
  const reduce = useReducedMotion();
  const min = Math.min(...s.packages.map((p) => p.price));

  return (
    <motion.article
      className="card service-card"
      initial={reduce ? false : { opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.15, margin: "0px 0px -40px 0px" }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1], delay: reduce ? 0 : Math.min(index % 6, 4) * 0.05 }}
    >
      <ServiceArt s={s} />
      <div className="svc-head">
        <span className="svc-cat">{s.category}</span>
        <span className="price-chip">
          from <b>{money(min)}</b>
        </span>
      </div>
      <h3>{s.title}</h3>
      <p>{s.short}</p>
      <div className="tag-row">
        {s.tags.slice(0, 4).map((t) => (
          <span className="tag" key={t}>{t}</span>
        ))}
      </div>
      <button className="card-link" onClick={() => onView(s.id)}>
        View packages <Icon name="arrow" size={16} />
      </button>
    </motion.article>
  );
}
