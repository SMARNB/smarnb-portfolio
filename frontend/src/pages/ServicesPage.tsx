/* Services overview page — the same scroll-story flow as Home, one information
   section per screen: each showcase story is a full-view stage, then the
   catalogue arrives ONE ROW (3 cards) at a time, then the store banner rides
   the last row, and process + CTA each get their own screen. A real, crawlable
   /services URL. */
import { useNavigate } from "react-router-dom";
import { featureSlides } from "../components/sections/FeatureShowcase";
import { ProcessSection, CtaBand } from "../components/sections/staticSections";
import { StoryStack } from "../components/ui/StoryStack";
import { ServiceCard } from "../components/ui/ServiceCard";
import { Reveal } from "../components/ui/Reveal";
import { Icon } from "../lib/icons";
import { useCatalog } from "../context/CatalogContext";

/** The full catalogue chunked into rows of 3 (the desktop grid width), each row
 *  its own stack panel. On narrow screens a row grows taller than the viewport
 *  and StoryStack simply lets it flow (no-pin). */
const ROW = 3;

export function ServicesPage() {
  const { services } = useCatalog();
  const navigate = useNavigate();
  const rows: (typeof services)[] = [];
  for (let i = 0; i < services.length; i += ROW) rows.push(services.slice(i, i + ROW));

  return (
    <StoryStack className="flush">
      {featureSlides(true)}
      {rows.map((row, ri) => (
        <section className="svc-slide" key={ri} id={ri === 0 ? "services" : undefined}>
          <div className="container">
            {ri === 0 ? (
              <Reveal className="section-head center">
                <span className="eyebrow">What I do</span>
                <h2 className="section-title">Services built to move your project forward</h2>
                <p className="lead" style={{ marginInline: "auto" }}>
                  The full catalogue — every service with transparent pricing. Compare packages and order in two
                  clicks in the store.
                </p>
              </Reveal>
            ) : (
              <span className="eyebrow svc-slide-note">
                Catalogue · {ri + 1} / {rows.length}
              </span>
            )}
            <div className="grid cols-3">
              {row.map((s, i) => (
                <ServiceCard key={s.id} s={s} index={i} onView={(id) => navigate(`/store#svc-${id}`)} />
              ))}
            </div>
            {ri === rows.length - 1 && (
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
            )}
          </div>
        </section>
      ))}
      <ProcessSection />
      <CtaBand />
    </StoryStack>
  );
}
