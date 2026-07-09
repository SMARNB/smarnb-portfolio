/* Feature showcase — the top 3 strengths, each a Problem → Solution → Result
   story with a neutral media panel and a CTA into the store.

   Two forms:
   • featureSlides() — one FULL-VIEW slide per story, meant to be spread into a
     <StoryStack> (Home + /services): each card pins and the next slides over it,
     so exactly one story is on stage at a time.
   • <FeatureShowcase compact/> — the original in-flow strip (used on /store).
   Reduced-motion safe (reveals via <Reveal>; the stack itself degrades in
   StoryStack). */
import { Link } from "react-router-dom";
import { MediaFrame } from "../../lib/art";
import { Icon } from "../../lib/icons";
import { FEATURED } from "../../lib/featured";
import type { Featured } from "../../lib/featured";
import { Reveal } from "../ui/Reveal";

function Head() {
  return (
    <Reveal className="section-head center">
      <span className="eyebrow">What I'm known for</span>
      <h2 className="section-title">Proof, not promises</h2>
      <p className="lead" style={{ marginInline: "auto" }}>
        Three problems I solve end to end — the challenge, how I build it, and the outcome.
      </p>
    </Reveal>
  );
}

function FeatureRow({ f, flip }: { f: Featured; flip: boolean }) {
  return (
    <div className={`feature-row${flip ? " rev" : ""}`}>
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
    </div>
  );
}

/** The "Proof, not promises" heading as its own in-flow section — placed BEFORE
 *  the StoryStack so slides stay short enough to pin on phones too. */
export function ShowcaseHead() {
  return (
    <section className="showcase-head" id="showcase">
      <div className="container">
        <Head />
      </div>
    </section>
  );
}

/** One full-view story per panel — spread these into a StoryStack. */
export function featureSlides() {
  return FEATURED.map((f, i) => (
    <section className="showcase feature-slide" key={f.id}>
      <div className="container">
        <FeatureRow f={f} flip={i % 2 === 1} />
      </div>
    </section>
  ));
}

/** In-flow variant (all three stories in one section) — used compact on /store. */
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
        {heading && <Head />}
        <div className="feature-list">
          {FEATURED.map((f, i) => (
            <Reveal key={f.id} delay={0.04}>
              <FeatureRow f={f} flip={i % 2 === 1} />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
