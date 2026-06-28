/* Products & licenses — finished products (CodeWatch) with license tiers. Fixed
   prices add to the cart; a `contact` tier links to a quote request. Port of
   renderProducts/productArt in app.js. */
import { Link } from "react-router-dom";
import { Icon } from "../../lib/icons";
import { ProductArt } from "../../lib/art";
import { money } from "../../lib/format";
import { products } from "../../lib/data";
import { useCart } from "../../context/CartContext";
import { useUI } from "../../context/UIContext";
import { useToast } from "../../context/ToastContext";
import { Reveal } from "../ui/Reveal";

export function Products() {
  const { add } = useCart();
  const { openCart } = useUI();
  const { toast } = useToast();

  return (
    <section id="products">
      <div className="container">
        <Reveal className="section-head center">
          <span className="eyebrow">Ready-made products</span>
          <h2 className="section-title">Products &amp; licenses</h2>
          <p className="lead" style={{ marginInline: "auto" }}>
            Finished products you can license today — no build time required. Buy a license and check out, or request a
            quote for full-rights / white-label deals.
          </p>
        </Reveal>

        <div className="grid" id="productsGrid">
          {products.map((p, i) => (
            <Reveal className="card product-card" key={p.id} as="article" delay={i * 0.08}>
              <ProductArt p={p} />
              <div className="product-body">
                <span className="eyebrow">{p.category}</span>
                <h3>
                  {p.title} <span className="pf-sub">— {p.subtitle}</span>
                </h3>
                <p className="lead">{p.desc}</p>
                {p.includes && (
                  <ul className="feat-list">
                    {p.includes.map((h) => (
                      <li key={h}>
                        <Icon name="check" /> <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="lic-row">
                  {p.licenses.map((l) => (
                    <div className={`lic${l.popular ? " popular" : ""}`} key={l.tier}>
                      <div className="lic-top">
                        <b>{l.tier}</b>
                        <span className="lic-price">{l.contact ? `from ${money(l.price)}` : money(l.price)}</span>
                      </div>
                      <p className="lic-note">{l.note || ""}</p>
                      {l.contact ? (
                        <Link className="btn btn-outline btn-sm" to="/#contact">
                          Request a quote
                        </Link>
                      ) : (
                        <button
                          className={`btn ${l.popular ? "btn-primary" : "btn-outline"} btn-sm`}
                          onClick={() => {
                            add({
                              serviceId: p.id,
                              service: p.title + " (license)",
                              tier: l.tier,
                              price: l.price,
                              delivery: "License",
                            });
                            toast(`${l.tier} added to cart`);
                            openCart();
                          }}
                        >
                          <Icon name="cart" size={18} /> Buy license
                        </button>
                      )}
                    </div>
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
