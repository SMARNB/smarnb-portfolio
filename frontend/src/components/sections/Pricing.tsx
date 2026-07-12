/* Pricing — service tabs + the selected service's package cards. Ordering a tier
   adds it to the cart and opens the drawer. Ports renderPriceTabs/renderPricing in
   app.js. */
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Icon } from "../../lib/icons";
import { money, shortTitle } from "../../lib/format";
import type { Service } from "../../lib/data";
import { useCart } from "../../context/CartContext";
import { useUI } from "../../context/UIContext";
import { useToast } from "../../context/ToastContext";

export function Pricing({
  services,
  selectedId,
  onSelect,
}: {
  services: Service[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const reduce = useReducedMotion();
  const { add } = useCart();
  const { openCart } = useUI();
  const { toast } = useToast();
  const s = services.find((x) => x.id === selectedId) || services[0];

  return (
    <>
      <div className="price-tabs" id="priceTabs" role="tablist" aria-label="Choose a service">
        {services.map((svc) => (
          <button
            key={svc.id}
            className="price-tab"
            role="tab"
            id={`tab-${svc.id}`}
            aria-controls="priceGrid"
            aria-selected={svc.id === s.id}
            onClick={() => onSelect(svc.id)}
          >
            {shortTitle(svc.title)}
          </button>
        ))}
      </div>

      <div className="price-grid" id="priceGrid" role="tabpanel">
        <AnimatePresence mode="wait">
          <motion.div
            key={s.id}
            style={{ display: "contents" }}
            initial={reduce ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={reduce ? undefined : { opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {s.packages.map((p, i) => (
              <motion.article
                key={p.tier}
                className={`card price-card${p.popular ? " popular" : ""}`}
                initial={reduce ? false : { opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1], delay: reduce ? 0 : i * 0.06 }}
                whileHover={reduce ? undefined : { y: -5 }}
              >
                {p.popular && <span className="badge-pop">Most popular</span>}
                <div className="tier">{p.tier}</div>
                <div className="amount">
                  {money(p.price)} <small>starting</small>
                </div>
                <p className="summary">{p.summary}</p>
                <div className="price-meta">
                  <span>⏱ <b>{p.delivery}</b></span>
                  <span>↻ <b>{p.revisions}</b> revisions</span>
                </div>
                <ul className="feat-list">
                  {p.features.map((f) => (
                    <li key={f}>
                      <Icon name="check" /> <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <button
                  className={`btn ${p.popular ? "btn-primary" : "btn-outline"} btn-block`}
                  onClick={() => {
                    add({ serviceId: s.id, service: s.title, tier: p.tier, price: p.price, delivery: p.delivery, summary: p.summary, scope: p.features });
                    toast(`${p.tier} package added to cart`);
                    openCart();
                  }}
                >
                  <Icon name="cart" size={18} /> Order {p.tier}
                </button>
              </motion.article>
            ))}
          </motion.div>
        </AnimatePresence>
      </div>
    </>
  );
}
