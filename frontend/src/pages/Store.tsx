/* Store — full services catalogue, pricing, products/licenses and payments.
   Supports #svc-<id> deep links (preselect a service + scroll to pricing) and the
   "View packages" jump from a service card. Ports the store path of app.js. */
import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { Link } from "react-router-dom";
import { useCatalog } from "../context/CatalogContext";
import { ServiceCard } from "../components/ui/ServiceCard";
import { Pricing } from "../components/sections/Pricing";
import { Products } from "../components/sections/Products";
import { PaymentsSection } from "../components/sections/staticSections";
import { Reveal } from "../components/ui/Reveal";
import { scrollToHash } from "../lib/lenis";

export function Store() {
  const { services } = useCatalog();
  const { hash } = useLocation();
  const [selectedId, setSelectedId] = useState("");
  const hashApplied = useRef(false);

  const selectService = (id: string, scroll: boolean) => {
    setSelectedId(id);
    if (scroll) {
      // Wait a tick for the tab/grid to update, then scroll to pricing.
      window.setTimeout(() => scrollToHash("#pricing"), 30);
    }
  };

  // Honour a #svc-<id> deep link once (preselect + scroll to pricing).
  useEffect(() => {
    if (hashApplied.current) return;
    const m = /^#svc-(.+)$/.exec(hash || "");
    if (!m) return;
    const id = decodeURIComponent(m[1]);
    if (!services.some((s) => s.id === id)) return;
    hashApplied.current = true;
    setSelectedId(id);
    window.setTimeout(() => scrollToHash("#pricing", true), 80);
  }, [hash, services]);

  return (
    <>
      <section className="store-hero" aria-label="Store intro">
        <div className="container">
          <Reveal className="section-head center">
            <span className="eyebrow">The store</span>
            <h1 className="section-title">Services &amp; transparent pricing</h1>
            <p className="lead" style={{ marginInline: "auto" }}>
              Pick a service, choose a package and add it to your cart — you'll get an order ID to track right here on
              the site. Bigger or custom jobs get a tailored quote.
            </p>
          </Reveal>
        </div>
      </section>

      <section id="services" style={{ paddingTop: 0 }}>
        <div className="container">
          <Reveal className="section-head">
            <span className="eyebrow">What I do</span>
            <h2 className="section-title">Browse all services</h2>
            <p className="lead">
              Each is delivered to a professional standard — pick a ready-made package below or ask for something custom.
            </p>
          </Reveal>
          <div className="grid cols-2" id="servicesGrid">
            {services.map((s, i) => (
              <ServiceCard key={s.id} s={s} index={i} onView={(id) => selectService(id, true)} />
            ))}
          </div>
        </div>
      </section>

      <section id="pricing">
        <div className="container">
          <Reveal className="section-head center">
            <span className="eyebrow">Packages &amp; pricing</span>
            <h2 className="section-title">Transparent pricing. Order in two clicks.</h2>
            <p className="lead" style={{ marginInline: "auto" }}>
              Choose a service, pick a tier, and add it to your cart. Every package is a starting point — bigger jobs get
              a custom quote.
            </p>
          </Reveal>
          {services.length > 0 && (
            <Pricing services={services} selectedId={selectedId || services[0].id} onSelect={(id) => selectService(id, false)} />
          )}
          <Reveal className="custom-banner">
            <div>
              <h3>Have a bigger or custom project?</h3>
              <p>Tell me what you need and I'll send a tailored quote and timeline — no obligation.</p>
            </div>
            <Link className="btn btn-primary" to="/contact">
              Get a custom quote
            </Link>
          </Reveal>
        </div>
      </section>

      <Products />
      <PaymentsSection />
    </>
  );
}
