/* Custom cursor — a small indigo dot that tracks the pointer exactly plus a ring
   that trails it with a little inertia, growing over interactive elements. It
   *accompanies* the native cursor (never replaces it, so nothing is lost for
   accessibility). First-party (no libraries); only mounts for precise pointers
   (skips touch) and is disabled under prefers-reduced-motion. */
import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

const INTERACTIVE = "a, button, [role='button'], input, textarea, select, label, summary, .card, .work-card";

// Elements that sit on an accent/coloured background — tinting their text to indigo
// would make it vanish, so the text-highlight skips anything inside these.
const NO_TINT =
  ".btn, .cta-band, .hero-shot, .mark, .media, .price-tab, .badge-pop, .status-chip, .tperson .av, .skip-link, .cart-count, .blog-chip";

/** True when the element directly contains visible text (a text leaf, not a big
 *  layout container) — so we tint the actual word/line under the cursor. */
function hasDirectText(el: Element): boolean {
  for (let i = 0; i < el.childNodes.length; i++) {
    const n = el.childNodes[i];
    if (n.nodeType === 3 && (n.textContent || "").trim()) return true;
  }
  return false;
}

export function CustomCursor() {
  const reduce = useReducedMotion();
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fine = window.matchMedia?.("(hover: hover) and (pointer: fine)").matches;
    if (!fine || reduce) return;

    const dot = dotRef.current;
    const ring = ringRef.current;
    if (!dot || !ring) return;

    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;
    let rx = mx;
    let ry = my;
    let shown = false;
    let raf = 0;
    let running = false;
    let txtEl: Element | null = null;

    const body = document.body;
    const show = () => {
      if (!shown) {
        shown = true;
        body.classList.add("cursor-on");
      }
    };

    // The ring eases toward the pointer, then the loop parks itself once it has
    // caught up — so nothing spins the CPU (or blocks frame capture) while idle.
    const loop = () => {
      rx += (mx - rx) * 0.2;
      ry += (my - ry) * 0.2;
      ring.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
      if (Math.abs(mx - rx) < 0.15 && Math.abs(my - ry) < 0.15) {
        running = false; // settled — idle until the next move
        return;
      }
      raf = requestAnimationFrame(loop);
    };
    const start = () => {
      if (!running) {
        running = true;
        raf = requestAnimationFrame(loop);
      }
    };

    const onMove = (e: MouseEvent) => {
      mx = e.clientX;
      my = e.clientY;
      // The dot pins to the pointer (feels instant); the ring lags via rAF.
      dot.style.transform = `translate3d(${mx}px, ${my}px, 0)`;
      show();
      start();
      const t = e.target as Element | null;
      body.classList.toggle("cursor-hover", !!t?.closest?.(INTERACTIVE));
      // Tint the single text element under the pointer (accent colour).
      if (t !== txtEl) {
        if (txtEl) txtEl.classList.remove("cursor-text");
        txtEl = null;
        if (t instanceof HTMLElement && hasDirectText(t) && !t.closest(NO_TINT)) {
          t.classList.add("cursor-text");
          txtEl = t;
        }
      }
    };
    const onLeave = () => {
      shown = false;
      body.classList.remove("cursor-on");
      if (txtEl) {
        txtEl.classList.remove("cursor-text");
        txtEl = null;
      }
    };
    const onDown = () => body.classList.add("cursor-press");
    const onUp = () => body.classList.remove("cursor-press");

    window.addEventListener("mousemove", onMove, { passive: true });
    document.addEventListener("mouseleave", onLeave);
    window.addEventListener("mousedown", onDown, { passive: true });
    window.addEventListener("mouseup", onUp, { passive: true });

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseleave", onLeave);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      if (txtEl) txtEl.classList.remove("cursor-text");
      body.classList.remove("cursor-on", "cursor-hover", "cursor-press");
    };
  }, [reduce]);

  return (
    <>
      <div ref={ringRef} className="cursor-ring" aria-hidden="true" />
      <div ref={dotRef} className="cursor-dot" aria-hidden="true" />
    </>
  );
}
