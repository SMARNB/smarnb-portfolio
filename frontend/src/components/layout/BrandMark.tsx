/* SMARNB brand mark — a flat indigo tile carrying a white spark-"S" over the
   full "SMARNB" wordmark. The S reads on its own at favicon sizes; the wordmark
   resolves from ~28px up (splash, app/PWA icon, social card). Colours follow the
   accent tokens so the mark tracks the theme. Decorative by default — the
   surrounding <Link> carries the accessible label; the studio's name
   ("Muhammad Ali Raza") stays as the wordmark beside it.
   Keep this in sync with public/favicon.svg and the splash mark in index.html
   (same art, hard-coded colours there since a browser tab / pre-bundle splash
   can't read CSS variables). */
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
      viewBox="0 0 64 64"
      fill="none"
      aria-hidden="true"
      focusable="false"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="64" height="64" rx="16" fill="var(--accent)" />
      <path
        d="M41 21 C41 15.5 35.5 12.5 28.5 12.5 C21.5 12.5 16.5 15.5 16.5 20.5 C16.5 25 20 26.7 28.5 27.6 C37 28.5 46 29.5 46 35 C46 40.5 40.5 43.5 33 43.5 C26 43.5 20.5 41 19 36"
        stroke="var(--on-accent)"
        strokeWidth="8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M49 8.5 L50.5 12.5 L54.5 14 L50.5 15.5 L49 19.5 L47.5 15.5 L43.5 14 L47.5 12.5 Z"
        fill="var(--on-accent)"
      />
      <text
        x="32"
        y="56"
        textAnchor="middle"
        fontFamily="'Segoe UI', system-ui, -apple-system, Arial, sans-serif"
        fontWeight="700"
        fontSize="8"
        letterSpacing="1.6"
        fill="var(--on-accent)"
      >
        SMARNB
      </text>
    </svg>
  );
}
