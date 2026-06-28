/* Home services teaser — first 6 services; "View packages" jumps to the store
   deep-linked to that service (#svc-<id>). Port of the teaser path in app.js. */
import { useNavigate } from "react-router-dom";
import { Icon } from "../../lib/icons";
import { useCatalog } from "../../context/CatalogContext";
import { ServiceCard } from "../ui/ServiceCard";
import { Reveal } from "../ui/Reveal";

export function ServicesTeaser() {
  const { services } = useCatalog();
  const navigate = useNavigate();
  const list = services.slice(0, 6);

  return (
    <section id="services">
      <div className="container">
        <Reveal className="section-head center">
          <span className="eyebrow">What I do</span>
          <h2 className="section-title">Services built to move your project forward</h2>
          <p className="lead" style={{ marginInline: "auto" }}>
            A snapshot of what I offer — see the full catalogue, packages and transparent pricing in the store, then
            order in two clicks.
          </p>
        </Reveal>
        <div className="grid cols-2" id="servicesGrid">
          {list.map((s, i) => (
            <ServiceCard key={s.id} s={s} index={i} onView={(id) => navigate(`/store#svc-${id}`)} />
          ))}
        </div>
        <Reveal className="custom-banner">
          <div>
            <h3>See every service &amp; transparent pricing</h3>
            <p>Browse all packages, compare tiers and order directly in the store.</p>
          </div>
          <button className="btn btn-primary" onClick={() => navigate("/store")}>
            Visit the store
            <Icon name="arrow" size={18} />
          </button>
        </Reveal>
      </div>
    </section>
  );
}
