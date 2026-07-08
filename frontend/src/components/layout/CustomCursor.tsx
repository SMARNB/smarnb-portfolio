/* Custom cursor — an indigo dot pinned to the pointer plus a ring that trails it
   with a little inertia, growing over interactive elements. It also highlights the
   single WORD under the pointer (accent) via the CSS Custom Highlight API — no DOM
   changes, no reflow — falling back to tinting the whole text element where the API
   is unsupported. Accompanies the native cursor (never replaces it); only mounts for
   precise pointers (skips touch) and is disabled under prefers-reduced-motion.
   First-party, no libraries. */
import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

const INTERACTIVE = "a, button, [role='button'], input, textarea, select, label, summary, .card, .work-card";

// Elements on an accent/coloured background (or form fields) — highlighting their
// text to indigo would make it vanish, so the text-highlight skips anything inside.
const NO_TINT =
  ".btn, .cta-band, .hero-shot, .mark, .media, .price-tab, .badge-pop, .status-chip, .tperson .av, .skip-link, .cart-count, .blog-chip, input, textarea, select";

/** True when the element directly contains visible text (fallback path only). */
function hasDirectText(el: Element): boolean {
  for (let i = 0; i < el.childNodes.length; i++) {
    const n = el.childNodes[i];
    if (n.nodeType === 3 && (n.textContent || "").trim()) return true;
  }
  return false;
}

/** A Range spanning the whole word (run of non-whitespace) under the point. */
function wordRangeAt(x: number, y: number): Range | null {
  const d = document as unknown as {
    caretPositionFromPoint?: (x: number, y: number) => { offsetNode: Node; offset: number } | null;
    caretRangeFromPoint?: (x: number, y: number) => Range | null;
  };
  let node: Node | null = null;
  let offset = 0;
  if (d.caretPositionFromPoint) {
    const p = d.caretPositionFromPoint(x, y);
    if (!p || !p.offsetNode) return null;
    node = p.offsetNode;
    offset = p.offset;
  } else if (d.caretRangeFromPoint) {
    const r = d.caretRangeFromPoint(x, y);
    if (!r) return null;
    node = r.startContainer;
    offset = r.startOffset;
  } else {
    return null;
  }
  if (!node || node.nodeType !== 3) return null;
  const text = node.nodeValue || "";
  if (!text.trim()) return null;
  const ws = (c: string | undefined) => !c || /\s/.test(c);
  if (ws(text[offset]) && ws(text[offset - 1])) return null; // pointer is on whitespace
  let s = offset;
  let e = offset;
  while (s > 0 && !ws(text[s - 1])) s--;
  while (e < text.length && !ws(text[e])) e++;
  if (s >= e) return null;
  try {
    const range = document.createRange();
    range.setStart(node, s);
    range.setEnd(node, e);
    return range;
  } catch {
    return null;
  }
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

    // CSS Custom Highlight API (word-by-word); fall back to element tint if absent.
    const win = window as unknown as { Highlight?: unknown; CSS?: { highlights?: Map<string, unknown> } };
    const HLc = win.Highlight as (new (r: Range) => unknown) | undefined;
    const highlights = win.CSS && win.CSS.highlights;
    const HL = !!(HLc && highlights);

    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;
    let rx = mx;
    let ry = my;
    let shown = false;
    let raf = 0;
    let running = false;
    let txtEl: Element | null = null; // fallback element-tint target

    const body = document.body;
    const show = () => {
      if (!shown) {
        shown = true;
        body.classList.add("cursor-on");
      }
    };
    const clearText = () => {
      if (HL) highlights!.delete("cursor-word");
      if (txtEl) {
        txtEl.classList.remove("cursor-text");
        txtEl = null;
      }
    };

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
      dot.style.transform = `translate3d(${mx}px, ${my}px, 0)`;
      show();
      start();
      const t = e.target as Element | null;
      body.classList.toggle("cursor-hover", !!t?.closest?.(INTERACTIVE));

      // Highlight the word (or, as a fallback, the element) under the pointer.
      const skip = !t || !!t.closest?.(NO_TINT);
      if (HL) {
        if (skip) {
          highlights!.delete("cursor-word");
        } else {
          const r = wordRangeAt(mx, my);
          if (r) highlights!.set("cursor-word", new HLc!(r));
          else highlights!.delete("cursor-word");
        }
      } else if (t !== txtEl) {
        if (txtEl) txtEl.classList.remove("cursor-text");
        txtEl = null;
        if (!skip && t instanceof HTMLElement && hasDirectText(t)) {
          t.classList.add("cursor-text");
          txtEl = t;
        }
      }
    };
    const onLeave = () => {
      shown = false;
      body.classList.remove("cursor-on");
      clearText();
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
      clearText();
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
