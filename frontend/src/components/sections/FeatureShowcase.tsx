/* Feature showcase — an alternating Z-pattern of the top 3 strengths, each a
   Problem → Solution → Result story with a neutral media panel and a CTA into the
   store. Used full on Home + /services and `compact` on /store. Reduced-motion
   safe (reveal handled by <Reveal>). */
import { Link } from "react-router-dom";
import { MediaFrame } from "../../lib/art";
import { Icon } from "../../lib/icons";
import { FEATURED } from "../../lib/featured";
import { Reveal } from "../ui/Reveal";

export function FeatureShowcase({
  compact = false,
  heading = true,
}: {
  compact?: boolean;
  heading?: boolean;
}) {
  return (
    <section id="showcase" className={`showcase${compact ? " compact" : ""}`}>
      <div className="container">
        {heading && (
          <Reveal className="section-head center">
            <span className="eyebrow">What I'm known for</span>
            <h2 className="section-title">Proof, not promises</h2>
            <p className="lead" style={{ marginInline: "auto" }}>
              Three problems I solve end to end — the challenge, how I build it, and the outcome.
            </p>
          </Reveal>
        )}

        <div className="feature-list">
          {FEATURED.map((f, i) => (
            <Reveal className={`feature-row${i % 2 ? " rev" : ""}`} key={f.id} delay={0.04}>
              <div className="feature-media">
                <MediaFrame
                  kind={f.media.kind}
                  image={f.media.image}
                  alt={f.media.alt}
                  logo={f.media.logo}
                  logoText={f.media.logoText}
                  className="fs-media"
                />
              </div>
              <div className="feature-body">
                <span className="eyebrow">{f.eyebrow}</span>
                <h3>{f.title}</h3>
                <div className="ps-grid">
                  <div className="ps">
                    <span className="ps-label">Problem</span>
                    <p>{f.problem}</p>
                  </div>
                  <div className="ps">
                    <span className="ps-label">Solution</span>
                    <p>{f.solution}</p>
                  </div>
                  <div className="ps">
                    <span className="ps-label ps-result">Result</span>
                    <p>{f.result}</p>
                  </div>
                </div>
                <div className="tag-row">
                  {f.stack.map((t) => (
                    <span className="tag" key={t}>{t}</span>
                  ))}
                </div>
                <Link className="btn btn-primary btn-sm" to={`/store#svc-${f.serviceId}`}>
                  See packages <Icon name="arrow" size={16} />
                </Link>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
