/* =============================================================================
   First-party card media — a clean, theme-aware, monochrome system.

   The old design painted every card with a loud category gradient + white
   line-art (the "AI template" wall). This replaces it with a neutral surface
   panel carrying a single monochrome line-art motif (currentColor, so it adapts
   to dark/light) plus ONE accent element. Accent colour is otherwise reserved
   for CTAs. Every frame also accepts a real screenshot (`image`) so cards can be
   swapped to real project outputs later with no markup change.
   ========================================================================== */
import type { Service, PortfolioItem, Product } from "./data";

/* Category gradients kept exported for backwards-compatibility with any caller,
   but card media no longer uses them — the neutral MediaFrame does. */
export const CAT_GRAD: Record<string, string> = {
  Development: "linear-gradient(135deg,#7c5cff,#22d3ee)",
  Design: "linear-gradient(135deg,#f472b6,#7c5cff)",
  Automation: "linear-gradient(135deg,#22d3ee,#34d399)",
  Packaging: "linear-gradient(135deg,#fbbf24,#f472b6)",
  "AI / Computer Vision": "linear-gradient(135deg,#34d399,#7c5cff)",
};
export const CAT_ICON: Record<string, string> = {
  Development: "code",
  Design: "pen",
  Automation: "bot",
  Packaging: "box",
};
export const DEFAULT_GRAD = "linear-gradient(135deg,#7c5cff,#22d3ee)";
export const gradFor = (cat: string) => CAT_GRAD[cat] || DEFAULT_GRAD;

/* ---- Monochrome motifs --------------------------------------------------- */
/* All strokes/fills use currentColor (themed via CSS `.media-art { color }`)
   except the single accent element, which is inlined as var(--accent). */

const M_DASHBOARD =
  '<g fill="none" stroke="currentColor" stroke-width="2" opacity=".5">' +
  '<rect x="42" y="30" width="236" height="100" rx="9"/>' +
  '<line x1="104" y1="30" x2="104" y2="130"/><line x1="42" y1="56" x2="278" y2="56"/></g>' +
  '<g fill="currentColor" opacity=".3">' +
  '<rect x="60" y="72" width="30" height="6" rx="3"/><rect x="60" y="86" width="22" height="6" rx="3"/><rect x="60" y="100" width="26" height="6" rx="3"/>' +
  '<rect x="118" y="70" width="47" height="24" rx="5"/><rect x="171" y="70" width="47" height="24" rx="5"/><rect x="224" y="70" width="44" height="24" rx="5"/></g>' +
  '<polyline points="120,120 148,108 174,114 202,96 228,104 268,84" fill="none" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" style="stroke:var(--accent)"/>';

const M_CV =
  '<g fill="none" stroke="currentColor" stroke-width="2.4" opacity=".5">' +
  '<path d="M46 42v-11h11M274 42v-11h-11M46 118v11h11M274 118v11h-11"/></g>' +
  '<path d="M46 84h228" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 8" opacity=".3"/>' +
  '<rect x="176" y="60" width="52" height="52" rx="3" fill="none" stroke="currentColor" stroke-width="2" opacity=".5"/>' +
  '<rect x="92" y="52" width="70" height="66" rx="3" fill="none" stroke-width="2.6" style="stroke:var(--accent)"/>' +
  '<rect x="92" y="41" width="52" height="12" rx="2" style="fill:var(--accent)"/>' +
  '<text x="97" y="50.5" font-size="8" font-family="ui-monospace,monospace" fill="#fff">0.98</text>';

const M_DESIGN =
  '<g fill="none" stroke="currentColor" stroke-width="2" opacity=".5">' +
  '<circle cx="120" cy="82" r="30"/>' +
  '<rect x="150" y="54" width="52" height="52" rx="11" transform="rotate(12 176 80)"/></g>' +
  '<path d="M150 114 l8 -28 40 -40 20 20 -40 40z" fill="none" stroke-width="2.6" stroke-linejoin="round" style="stroke:var(--accent)"/>' +
  '<circle cx="120" cy="82" r="4" style="fill:var(--accent)"/>';

const M_BOX =
  '<g fill="none" stroke="currentColor" stroke-width="2" opacity=".5" stroke-linejoin="round">' +
  '<path d="M160 38 l56 31 v42 l-56 31 -56 -31 v-42z"/><path d="M160 100 v42"/>' +
  '<path d="M104 69 l56 31 56 -31"/></g>' +
  '<path d="M160 38 l56 31 -56 31 -56 -31z" fill="none" stroke-width="2.6" stroke-linejoin="round" style="stroke:var(--accent)"/>';

const M_SPARK =
  '<g fill="currentColor" opacity=".38">' +
  '<path d="M216 56l4 11 11 4-11 4-4 11-4-11-11-4 11-4z"/>' +
  '<path d="M104 98l3.5 10 10 3.5-10 3.5-3.5 10-3.5-10-10-3.5 10-3.5z"/></g>' +
  '<path d="M160 48l9.5 25 25 9.5-25 9.5-9.5 25-9.5-25-25-9.5 25-9.5z" style="fill:var(--accent)" opacity=".92"/>';

const CODE_SNIPPET =
  '<span class="c"># extract fields from a scanned invoice</span>\n' +
  '<span class="k">import</span> cv2, easyocr\n' +
  'reader = easyocr.<span class="fn">Reader</span>([<span class="s">"en"</span>])\n' +
  'img = cv2.<span class="fn">imread</span>(<span class="s">"invoice.png"</span>)\n' +
  '<span class="k">for</span> box, text, conf <span class="k">in</span> reader.<span class="fn">readtext</span>(img):\n' +
  '    <span class="k">if</span> conf > <span class="n">0.6</span>:\n' +
  '        save(field(box), text)';

export type MediaKind = "cv" | "dashboard" | "code" | "design" | "box" | "spark";
const MOTIF: Record<Exclude<MediaKind, "code">, string> = {
  cv: M_CV,
  dashboard: M_DASHBOARD,
  design: M_DESIGN,
  box: M_BOX,
  spark: M_SPARK,
};

/** Map a catalog category to its default placeholder motif. */
export const CAT_KIND: Record<string, MediaKind> = {
  "AI / Computer Vision": "cv",
  Development: "dashboard",
  Automation: "code",
  Design: "design",
  Packaging: "box",
};
export const kindFor = (cat: string): MediaKind => CAT_KIND[cat] || "spark";

/** Neutral card/panel media. Shows a real screenshot when `image` is set (with an
 *  optional logo/wordmark + scrim), otherwise a monochrome motif for `kind`. */
export function MediaFrame({
  kind,
  image,
  alt,
  logo,
  logoText,
  badge,
  className = "",
}: {
  kind: MediaKind;
  image?: string;
  alt?: string;
  logo?: string;
  logoText?: string;
  badge?: string;
  className?: string;
}) {
  if (image) {
    return (
      <div className={`media has-shot ${className}`.trim()}>
        <img className="media-shot" src={image} alt={alt || ""} loading="lazy" />
        <span className="media-scrim" aria-hidden="true" />
        {logo || logoText ? (
          <span className="media-logo">
            {logo ? <img src={logo} alt="" /> : null}
            {logoText ? <b>{logoText}</b> : null}
          </span>
        ) : null}
        {badge ? <span className="media-badge">{badge}</span> : null}
      </div>
    );
  }
  return (
    <div className={`media ${className}`.trim()}>
      {kind === "code" ? (
        <pre className="media-code" aria-hidden="true" dangerouslySetInnerHTML={{ __html: CODE_SNIPPET }} />
      ) : (
        <svg
          className="media-art"
          viewBox="0 0 320 160"
          preserveAspectRatio="xMidYMid meet"
          aria-hidden="true"
          dangerouslySetInnerHTML={{ __html: MOTIF[kind] }}
        />
      )}
      {badge ? <span className="media-badge">{badge}</span> : null}
    </div>
  );
}

/** Service card media header (neutral). */
export function ServiceArt({ s }: { s: Service }) {
  return <MediaFrame kind={kindFor(s.category)} className="svc-media" />;
}

/** Portfolio / work thumbnail media (neutral). */
export function PortfolioArt({ p, className = "" }: { p: PortfolioItem; className?: string }) {
  return <MediaFrame kind={kindFor(p.category)} className={className} />;
}

/** Product media header — real screenshot (+ logo/wordmark) when provided,
 *  otherwise the neutral motif. */
export function ProductArt({ p }: { p: Product }) {
  return (
    <MediaFrame
      kind={kindFor(p.category)}
      image={p.image}
      alt={p.image ? `${p.title} — product preview` : undefined}
      logo={p.logo}
      logoText={p.image ? p.title : undefined}
      badge={p.badge}
      className="product-media"
    />
  );
}
