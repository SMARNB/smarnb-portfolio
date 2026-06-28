/* Service card — illustrated header, "from" price chip, title/blurb/tags and a
   "View packages" action. Shared by the Home teaser and the Store grid. Springy
   scroll-reveal + hover lift via Framer (reduced-motion aware). */
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
      initial={reduce ? false : { opacity: 0, y: 26 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.15, margin: "0px 0px -40px 0px" }}
      transition={{ type: "spring", stiffness: 90, damping: 18, mass: 0.6, delay: reduce ? 0 : (index % 6) * 0.06 }}
      whileHover={reduce ? undefined : { y: -5 }}
    >
      <ServiceArt s={s} />
      <div className="from">
        from <b>{money(min)}</b>
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
