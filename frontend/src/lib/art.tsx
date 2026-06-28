/* =============================================================================
   First-party illustrated SVG art — port of CAT_GRAD / SVC_ART / PORTFOLIO_ART /
   serviceArt / portfolioArt / productArt from assets/js/app.js. White line-art on
   the category gradient so cards read as images, not placeholders.
   ========================================================================== */
import { Icon } from "./icons";
import type { Service, PortfolioItem, Product } from "./data";

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

const SVC_ART: Record<string, string> = {
  Development:
    '<rect x="64" y="34" width="192" height="92" rx="10" fill="rgba(255,255,255,.12)" stroke="rgba(255,255,255,.75)" stroke-width="2"/>' +
    '<line x1="64" y1="54" x2="256" y2="54" stroke="rgba(255,255,255,.75)" stroke-width="2"/>' +
    '<circle cx="78" cy="44" r="3" fill="#fff"/><circle cx="90" cy="44" r="3" fill="rgba(255,255,255,.7)"/><circle cx="102" cy="44" r="3" fill="rgba(255,255,255,.5)"/>' +
    '<rect x="80" y="68" width="64" height="6" rx="3" fill="rgba(255,255,255,.55)"/>' +
    '<rect x="80" y="82" width="92" height="6" rx="3" fill="rgba(255,255,255,.35)"/>' +
    '<rect x="80" y="96" width="46" height="6" rx="3" fill="rgba(255,255,255,.35)"/>' +
    '<rect x="196" y="96" width="10" height="20" rx="2" fill="rgba(255,255,255,.55)"/>' +
    '<rect x="212" y="84" width="10" height="32" rx="2" fill="rgba(255,255,255,.78)"/>' +
    '<rect x="228" y="72" width="10" height="44" rx="2" fill="#fff"/>',
  Design:
    '<circle cx="124" cy="82" r="34" fill="rgba(255,255,255,.18)"/>' +
    '<rect x="150" y="52" width="58" height="58" rx="12" fill="rgba(255,255,255,.26)" transform="rotate(12 179 81)"/>' +
    '<path d="M150 116 l8 -30 44 -44 22 22 -44 44z" fill="rgba(255,255,255,.9)" stroke="rgba(255,255,255,.9)" stroke-width="2" stroke-linejoin="round"/>' +
    '<path d="M196 64 l16 16" stroke="rgba(0,0,0,.18)" stroke-width="2"/>',
  Automation:
    '<rect x="120" y="56" width="80" height="62" rx="13" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.75)" stroke-width="2"/>' +
    '<circle cx="160" cy="42" r="4" fill="#fff"/><line x1="160" y1="46" x2="160" y2="56" stroke="rgba(255,255,255,.75)" stroke-width="2"/>' +
    '<circle cx="144" cy="86" r="8" fill="#fff"/><circle cx="176" cy="86" r="8" fill="#fff"/>' +
    '<rect x="140" y="104" width="40" height="6" rx="3" fill="rgba(255,255,255,.5)"/>' +
    '<g stroke="rgba(255,255,255,.78)" stroke-width="2" fill="none"><circle cx="228" cy="92" r="13"/><path d="M228 75v-6M228 115v-6M207 92h-6M249 92h-6M213 77l-4-4M247 111l4 4"/></g>',
  Packaging:
    '<path d="M160 38 l56 31 v44 l-56 31 -56 -31 v-44z" fill="rgba(255,255,255,.14)" stroke="rgba(255,255,255,.8)" stroke-width="2" stroke-linejoin="round"/>' +
    '<path d="M160 38 l56 31 -56 31 -56 -31z" fill="rgba(255,255,255,.3)" stroke="rgba(255,255,255,.8)" stroke-width="2" stroke-linejoin="round"/>' +
    '<path d="M160 100 v44" stroke="rgba(255,255,255,.8)" stroke-width="2"/>',
  "AI / Computer Vision":
    '<g stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M120 58h-14v-14M200 58h14v-14M120 110h-14v14M200 110h14v14"/></g>' +
    '<circle cx="160" cy="84" r="30" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.85)" stroke-width="2"/>' +
    '<circle cx="160" cy="84" r="10" fill="#fff"/>' +
    '<path d="M108 84h104" stroke="rgba(255,255,255,.45)" stroke-width="2" stroke-dasharray="3 7"/>',
};

const SVC_ART_GENERIC =
  '<g fill="#fff"><path d="M160 50l9 24 24 9-24 9-9 24-9-24-24-9 24-9z" opacity=".9"/>' +
  '<path d="M214 60l4 11 11 4-11 4-4 11-4-11-11-4 11-4z" opacity=".55"/>' +
  '<path d="M104 96l4 11 11 4-11 4-4 11-4-11-11-4 11-4z" opacity=".4"/></g>';

const PORTFOLIO_ART: Record<string, string> = {
  p1:
    '<rect x="58" y="38" width="204" height="84" rx="10" fill="rgba(255,255,255,.12)" stroke="rgba(255,255,255,.7)" stroke-width="2"/>' +
    '<rect x="72" y="50" width="36" height="9" rx="4" fill="rgba(255,255,255,.55)"/>' +
    '<rect x="116" y="50" width="24" height="9" rx="4" fill="rgba(255,255,255,.35)"/>' +
    '<polyline points="74,106 104,88 134,96 164,68 194,76 224,52" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>' +
    '<circle cx="224" cy="52" r="3.6" fill="#fff"/>',
  p2:
    '<rect x="66" y="42" width="82" height="74" rx="8" fill="rgba(255,255,255,.14)" stroke="rgba(255,255,255,.7)" stroke-width="2"/>' +
    '<rect x="158" y="42" width="92" height="74" rx="8" fill="rgba(255,255,255,.2)" stroke="rgba(255,255,255,.7)" stroke-width="2"/>' +
    '<rect x="78" y="54" width="58" height="6" rx="3" fill="rgba(255,255,255,.6)"/>' +
    '<rect x="78" y="70" width="44" height="6" rx="3" fill="rgba(255,255,255,.4)"/>' +
    '<rect x="78" y="86" width="50" height="6" rx="3" fill="rgba(255,255,255,.4)"/>' +
    '<rect x="170" y="54" width="68" height="6" rx="3" fill="rgba(255,255,255,.6)"/>' +
    '<circle cx="182" cy="86" r="11" fill="rgba(255,255,255,.5)"/>' +
    '<rect x="200" y="82" width="40" height="6" rx="3" fill="rgba(255,255,255,.4)"/>',
  p3:
    '<rect x="60" y="40" width="72" height="90" rx="8" fill="rgba(255,255,255,.14)" stroke="rgba(255,255,255,.75)" stroke-width="2"/>' +
    '<rect x="72" y="54" width="48" height="6" rx="3" fill="rgba(255,255,255,.55)"/>' +
    '<rect x="72" y="68" width="42" height="5" rx="2.5" fill="rgba(255,255,255,.4)"/>' +
    '<rect x="72" y="80" width="48" height="5" rx="2.5" fill="rgba(255,255,255,.4)"/>' +
    '<line x1="64" y1="98" x2="128" y2="98" stroke="#fff" stroke-width="2" stroke-dasharray="4 4"/>' +
    '<path d="M146 84h26m0 0l-8-8m8 8l-8 8" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' +
    '<rect x="188" y="54" width="68" height="62" rx="8" fill="rgba(255,255,255,.18)" stroke="rgba(255,255,255,.75)" stroke-width="2"/>' +
    '<rect x="200" y="66" width="44" height="6" rx="3" fill="rgba(255,255,255,.6)"/>' +
    '<rect x="200" y="80" width="34" height="6" rx="3" fill="rgba(255,255,255,.4)"/>' +
    '<rect x="200" y="94" width="40" height="6" rx="3" fill="rgba(255,255,255,.4)"/>',
  p4:
    '<path d="M150 40 l52 29 v42 l-52 29 -52 -29 v-42z" fill="rgba(255,255,255,.14)" stroke="rgba(255,255,255,.8)" stroke-width="2" stroke-linejoin="round"/>' +
    '<path d="M150 40 l52 29 -52 29 -52 -29z" fill="rgba(255,255,255,.3)" stroke="rgba(255,255,255,.8)" stroke-width="2" stroke-linejoin="round"/>' +
    '<path d="M150 98 v42" stroke="rgba(255,255,255,.8)" stroke-width="2"/>' +
    '<path d="M214 64 c-16 2 -24 12 -22 26 14 2 24 -8 22 -26z" fill="rgba(255,255,255,.6)"/>' +
    '<path d="M198 88 q8 -10 16 -22" stroke="rgba(10,13,20,.18)" stroke-width="2" fill="none"/>',
  p5:
    '<rect x="60" y="42" width="200" height="76" rx="10" fill="rgba(255,255,255,.12)" stroke="rgba(255,255,255,.7)" stroke-width="2"/>' +
    '<line x1="60" y1="62" x2="260" y2="62" stroke="rgba(255,255,255,.5)" stroke-width="1.5"/>' +
    '<line x1="124" y1="42" x2="124" y2="118" stroke="rgba(255,255,255,.35)" stroke-width="1.5"/>' +
    '<rect x="74" y="72" width="34" height="6" rx="3" fill="rgba(255,255,255,.5)"/>' +
    '<rect x="74" y="88" width="34" height="6" rx="3" fill="rgba(255,255,255,.5)"/>' +
    '<rect x="74" y="104" width="28" height="6" rx="3" fill="rgba(255,255,255,.5)"/>' +
    '<rect x="138" y="72" width="64" height="8" rx="4" fill="rgba(255,255,255,.6)"/>' +
    '<rect x="138" y="88" width="44" height="8" rx="4" fill="rgba(255,255,255,.4)"/>' +
    '<rect x="138" y="104" width="54" height="8" rx="4" fill="rgba(255,255,255,.4)"/>',
  p6:
    '<rect x="58" y="38" width="204" height="84" rx="10" fill="rgba(255,255,255,.12)" stroke="rgba(255,255,255,.7)" stroke-width="2"/>' +
    '<g stroke="#fff" stroke-width="2" fill="none"><line x1="88" y1="56" x2="88" y2="104"/><line x1="120" y1="62" x2="120" y2="110"/>' +
    '<line x1="152" y1="50" x2="152" y2="100"/><line x1="184" y1="60" x2="184" y2="108"/><line x1="216" y1="46" x2="216" y2="96"/></g>' +
    '<g fill="none"><rect x="82" y="68" width="12" height="24" rx="2" fill="rgba(255,255,255,.6)"/>' +
    '<rect x="114" y="78" width="12" height="20" rx="2" fill="rgba(255,255,255,.4)"/>' +
    '<rect x="146" y="60" width="12" height="28" rx="2" fill="rgba(255,255,255,.7)"/>' +
    '<rect x="178" y="74" width="12" height="22" rx="2" fill="rgba(255,255,255,.45)"/>' +
    '<rect x="210" y="54" width="12" height="26" rx="2" fill="#fff"/></g>',
  p7:
    '<g stroke="rgba(255,255,255,.55)" stroke-width="2"><line x1="160" y1="82" x2="100" y2="50"/><line x1="160" y1="82" x2="100" y2="112"/>' +
    '<line x1="160" y1="82" x2="222" y2="54"/><line x1="160" y1="82" x2="224" y2="106"/><line x1="160" y1="82" x2="160" y2="42"/></g>' +
    '<circle cx="160" cy="82" r="15" fill="rgba(255,255,255,.25)" stroke="#fff" stroke-width="2"/>' +
    '<g fill="#fff"><circle cx="100" cy="50" r="7"/><circle cx="100" cy="112" r="7"/><circle cx="222" cy="54" r="7"/><circle cx="224" cy="106" r="7"/><circle cx="160" cy="42" r="6"/></g>',
  p8:
    '<rect x="118" y="56" width="36" height="66" rx="10" fill="rgba(255,255,255,.2)" stroke="rgba(255,255,255,.75)" stroke-width="2"/>' +
    '<rect x="128" y="44" width="16" height="14" rx="3" fill="rgba(255,255,255,.6)"/>' +
    '<rect x="124" y="80" width="24" height="22" rx="4" fill="rgba(255,255,255,.5)"/>' +
    '<rect x="170" y="64" width="42" height="58" rx="16" fill="rgba(255,255,255,.14)" stroke="rgba(255,255,255,.75)" stroke-width="2"/>' +
    '<rect x="183" y="54" width="16" height="12" rx="3" fill="rgba(255,255,255,.55)"/>' +
    '<rect x="177" y="86" width="28" height="18" rx="4" fill="rgba(255,255,255,.4)"/>',
  codewatch: SVC_ART["AI / Computer Vision"],
};

/** Service card illustrated header (gradient media + line-art + category badge + icon chip). */
export function ServiceArt({ s }: { s: Service }) {
  const motif = SVC_ART[s.category] || SVC_ART_GENERIC;
  return (
    <div className="svc-media" style={{ background: gradFor(s.category) }}>
      <svg
        className="svc-art"
        viewBox="0 0 320 160"
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
        dangerouslySetInnerHTML={{ __html: motif }}
      />
      <span className="svc-badge">{s.category}</span>
      <span className="svc-chip">
        <Icon name={s.icon} />
      </span>
    </div>
  );
}

/** Portfolio thumbnail line-art (sits over the gradient placeholder). */
export function PortfolioArt({ p }: { p: PortfolioItem }) {
  const motif = PORTFOLIO_ART[p.id] || SVC_ART[p.category] || SVC_ART_GENERIC;
  return (
    <svg
      className="work-art"
      viewBox="0 0 320 160"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: motif }}
    />
  );
}

/** Product media header (gradient + line-art + badge). */
export function ProductArt({ p }: { p: Product }) {
  const motif = PORTFOLIO_ART[p.art] || SVC_ART[p.category] || SVC_ART_GENERIC;
  return (
    <div className="product-media" style={{ background: gradFor(p.category) }}>
      <svg
        className="svc-art"
        viewBox="0 0 320 160"
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
        dangerouslySetInnerHTML={{ __html: motif }}
      />
      {p.badge ? <span className="product-badge">{p.badge}</span> : null}
    </div>
  );
}
