/* SMARNB brand mark — a flat indigo tile carrying a white "growth arrow" glyph
   (a rising path that turns into an up-right arrow, anchored by a circuit node).
   It replaces the old plain "SMARNB" text pill / gradient favicon as the logo.
   Colours follow the accent tokens so the mark tracks the theme; the studio's
   name ("Muhammad Ali Raza") stays as the wordmark beside it. Decorative by
   default — the surrounding <Link> carries the accessible label. */
export function BrandMark({
  size = 32,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      className={`brand-logo ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
      focusable="false"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="2" y="2" width="36" height="36" rx="11" fill="var(--accent)" />
      <path
        d="M10.5 26 L17 19.5 L21.5 23 L29.5 13"
        stroke="var(--on-accent)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M24 13 L29.5 13 L29.5 18.5"
        stroke="var(--on-accent)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="10.5" cy="26" r="2.4" fill="var(--on-accent)" />
    </svg>
  );
}
