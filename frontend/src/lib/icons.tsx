/* =============================================================================
   Inline SVG icon set — port of the ICONS (P) map + icon() in assets/js/app.js.
   currentColor based; a small set is filled, the rest are stroked line icons.
   ========================================================================== */
import type { CSSProperties } from "react";

export const ICON_PATHS: Record<string, string> = {
  code: '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
  pen: '<path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/>',
  bot: '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="8" cy="16" r="1.4"/><circle cx="16" cy="16" r="1.4"/><path d="M12 7v4M12 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM2 14h1M21 14h1"/>',
  box: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
  chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
  doc: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/>',
  check: '<polyline points="20 6 9 17 4 12"/>',
  rocket: '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>',
  clock: '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>',
  arrow: '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
  cart: '<circle cx="9" cy="21" r="1.5"/><circle cx="19" cy="21" r="1.5"/><path d="M2.5 3H5l2.7 13.4a1.5 1.5 0 0 0 1.5 1.2h9.7a1.5 1.5 0 0 0 1.5-1.2L22 7H6"/>',
  close: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  menu: '<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>',
  sun: '<circle cx="12" cy="12" r="4.5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
  star: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
  plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  minus: '<line x1="5" y1="12" x2="19" y2="12"/>',
  mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="2.5 6 12 13 21.5 6"/>',
  whatsapp:
    '<path fill="currentColor" stroke="none" d="M20 11.9a8 8 0 0 1-11.9 7L3 20l1.2-4.9A8 8 0 1 1 20 11.9zM12 5.6a6.3 6.3 0 0 0-5.4 9.6l-.7 2.6 2.7-.7A6.3 6.3 0 1 0 12 5.6zm3.7 8c-.2.5-1 1-1.4 1-.4.1-.8.1-1.3-.1-.3-.1-.7-.2-1.2-.5a6.7 6.7 0 0 1-2.5-2.6c-.2-.3-.6-.9-.6-1.6 0-.7.4-1.1.5-1.2.2-.2.4-.2.5-.2h.4c.1 0 .3 0 .5.4l.5 1.2c0 .1.1.2 0 .4l-.3.4-.2.2c-.1.1-.2.2 0 .4.2.4.6.9 1 1.2.6.5 1 .6 1.2.7.1 0 .3 0 .4-.1l.5-.6c.2-.2.3-.1.5-.1l1.2.6c.2.1.3.2.4.2.1.2.1.5-.1.9z"/>',
  chevron: '<polyline points="6 9 12 15 18 9"/>',
  trash: '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  spark: '<path d="M12 2l2.4 6.5L21 11l-6.6 2.5L12 20l-2.4-6.5L3 11l6.6-2.5z"/>',
  eye: '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/>',
  server: '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><line x1="7" y1="7.5" x2="7.01" y2="7.5"/><line x1="7" y1="16.5" x2="7.01" y2="16.5"/>',
  layout: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>',
  card: '<rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>',
  top: '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  cartBig: '<circle cx="9" cy="21" r="1.5"/><circle cx="19" cy="21" r="1.5"/><path d="M2.5 3H5l2.7 13.4a1.5 1.5 0 0 0 1.5 1.2h9.7a1.5 1.5 0 0 0 1.5-1.2L22 7H6"/>',
  github:
    '<path fill="currentColor" stroke="none" d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.36 1.09 2.94.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.6 9.6 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2z"/>',
  linkedin:
    '<path fill="currentColor" stroke="none" d="M4.98 3.5A2.5 2.5 0 1 1 5 8.5a2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05 4 0 4.75 2.65 4.75 6.1V21H17.6v-5.4c0-1.3 0-2.95-1.8-2.95s-2.05 1.4-2.05 2.85V21H9z"/>',
  instagram: '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor" stroke="none"/>',
  facebook:
    '<path fill="currentColor" stroke="none" d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.4h-1.2c-1.2 0-1.6.8-1.6 1.5V12h2.7l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/>',
  x: '<path fill="currentColor" stroke="none" d="M18.9 2H22l-7.1 8.1L23.3 22h-6.6l-5.2-6.8L5.5 22H2.4l7.6-8.7L1.1 2h6.8l4.6 6.2L18.9 2z"/>',
};

const FILLED = new Set(["star", "whatsapp", "github", "linkedin", "instagram", "facebook", "x"]);

export function Icon({
  name,
  className,
  style,
  size = 24,
}: {
  name: string;
  className?: string;
  style?: CSSProperties;
  size?: number;
}) {
  const inner = ICON_PATHS[name] || "";
  const filled = FILLED.has(name);
  const stroke = filled
    ? { fill: "currentColor", stroke: "none" as const }
    : {
        fill: "none" as const,
        stroke: "currentColor",
        strokeWidth: 1.9,
        strokeLinecap: "round" as const,
        strokeLinejoin: "round" as const,
      };
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      style={style}
      aria-hidden="true"
      {...stroke}
      dangerouslySetInnerHTML={{ __html: inner }}
    />
  );
}
