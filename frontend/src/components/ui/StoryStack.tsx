/* StoryStack — the scroll-story used on Home / Services / Work / About: each child
   is a full-view "stage" (min-height 100svh − stack-top, opaque — see .story-panel
   in global.css) that pins below the floating header while the next arrives over
   it, so ONE information section is on screen at a time.

   Each panel ENTERS with its own scroll-driven transition (rotating by default,
   overridable per page via the `variants` prop):
     cover        — slides up from the bottom (the classic sheet)
     swipe-left / swipe-right — slides in horizontally over the previous section
     split-x / split-y        — barn-door reveal (clip opens from the centre)
     fade         — cross-fades in over the previous section
     zoom-in / zoom-out       — scales into place while fading in
   All are driven by scroll progress (reversible when scrolling back). Non-cover
   variants pin the panel visually at the stack top for the whole entry by
   counter-translating its flow offset; once the entry completes the correction
   is zero and native position:sticky takes over seamlessly. The covered panel
   gently recedes (scale only, never opacity — dimming read washed-out).

   Grounded in classic sticky stacking (each panel `position: sticky` at a shared
   top inside one flow container), so the browser does the pinning and the effect
   costs no scroll listeners beyond framer's rAF-batched rect reads.

   Safety rails:
   - Runs on every viewport (mobile included — sticky is cheap); disabled only
     under prefers-reduced-motion, where children render in plain flow.
   - A panel taller than the pinnable area skips pinning AND its entry variant
     (`no-pin`) so its lower content can never be covered before it was seen.
   - The last panel never recedes (nothing ever covers it). */
import { Children, createRef, useEffect, useMemo, useState } from "react";
import type { ReactNode, RefObject } from "react";
import {
  motion,
  motionValue,
  useMotionValueEvent,
  useReducedMotion,
  useScroll,
  useTransform,
} from "framer-motion";
import type { MotionValue } from "framer-motion";

/** Keep in sync with --stack-top in global.css (header 62px + gap). */
const STACK_TOP_PX = 78;

export type StoryVariant =
  | "cover"
  | "swipe-left"
  | "swipe-right"
  | "split-x"
  | "split-y"
  | "fade"
  | "zoom-in"
  | "zoom-out";

/* Rotating default assignment — intentional variety with zero page wiring.
   Index 0 is "cover" so the first panel always arrives as the classic sheet. */
const CYCLE: StoryVariant[] = [
  "cover", "swipe-left", "split-x", "fade", "swipe-right", "zoom-in", "split-y",
];

function useViewportH(): number {
  const [vh, setVh] = useState(() =>
    typeof window === "undefined" ? 900 : window.innerHeight,
  );
  useEffect(() => {
    const on = () => setVh(window.innerHeight);
    window.addEventListener("resize", on, { passive: true });
    return () => window.removeEventListener("resize", on);
  }, []);
  return vh;
}

function useStackEnabled(): boolean {
  const reduce = useReducedMotion();
  return !reduce;
}

function StoryPanel({
  panelRef,
  isLast,
  variant,
  enterOut,
  nextEnter,
  children,
}: {
  panelRef: RefObject<HTMLDivElement>;
  isLast: boolean;
  variant: StoryVariant;
  /** Shared slot this panel publishes its entry progress into. */
  enterOut: MotionValue<number>;
  /** The NEXT panel's published entry progress (drives this panel's recede). */
  nextEnter: MotionValue<number>;
  children: ReactNode;
}) {
  const vh = useViewportH();

  // Panels taller than the pinnable area must not pin. Stages are exactly
  // 100svh − stack-top tall (svh ≤ innerHeight), so they pin; the +4px only
  // absorbs sub-pixel rounding. Content-driven overflow still opts out.
  const [noPin, setNoPin] = useState(false);
  useEffect(() => {
    const el = panelRef.current;
    if (!el) return;
    const check = () =>
      setNoPin(el.offsetHeight > window.innerHeight - STACK_TOP_PX + 4);
    check();
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(check) : null;
    ro?.observe(el);
    window.addEventListener("resize", check, { passive: true });
    return () => {
      ro?.disconnect();
      window.removeEventListener("resize", check);
    };
  }, [panelRef]);

  // ---- Entry: this panel's own arrival, driven by its top travelling from the
  // viewport bottom to the pinned position (top = STACK_TOP_PX). Layout rects
  // ignore transforms, so the counter-translation below never skews the timing.
  const { scrollYProgress: rawEnter } = useScroll({
    target: panelRef,
    offset: ["start end", "start start"],
  });
  const pinnedAt = Math.max(0.05, (vh - STACK_TOP_PX) / vh); // progress when top hits 78px
  const enter = useTransform(rawEnter, [0, pinnedAt], [0, 1]); // clamped

  // Publish this panel's entry progress so the PREVIOUS sibling can recede in
  // sync with it. (A second useScroll against the sibling's ref misresolves
  // element offsets under sticky stacking — sharing the proven value instead.)
  useMotionValueEvent(enter, "change", (v) => enterOut.set(v));
  useEffect(() => {
    enterOut.set(enter.get());
  }, [enter, enterOut]);

  const still = noPin || variant === "cover"; // physical slide (or plain flow)
  // Counter-translate the flow offset so non-cover entries play out pinned.
  // GATED at p == 0: a pending panel must rest at its flow position (below the
  // viewport) — corrected-but-invisible panels would still swallow pointer
  // events over the active section (opacity:0 hit-tests; clip-path doesn't).
  const y = useTransform(enter, (p) => (still || p <= 0 ? 0 : (p - 1) * (vh - STACK_TOP_PX)));
  const x = useTransform(enter, (p) => {
    if (still) return "0%";
    if (variant === "swipe-left") return `${(1 - p) * 100}%`;
    if (variant === "swipe-right") return `${(1 - p) * -100}%`;
    return "0%";
  });
  const opacity = useTransform(enter, (p) => {
    if (still) return 1;
    if (variant === "fade") return p;
    if (variant === "zoom-in" || variant === "zoom-out") return Math.min(1, p * 1.5);
    return 1;
  });
  const enterScale = useTransform(enter, (p) => {
    if (still) return 1;
    if (variant === "zoom-in") return 0.85 + 0.15 * p;
    if (variant === "zoom-out") return 1.15 - 0.15 * p;
    return 1;
  });
  const clipPath = useTransform(enter, (p) => {
    const v = still ? 0 : 50 * (1 - p);
    if (variant === "split-x") return `inset(0% ${v}% 0% ${v}%)`;
    if (variant === "split-y") return `inset(${v}% 0% ${v}% 0%)`;
    return "none";
  });

  // ---- Exit: gentle recede, driven by the NEXT panel's shared entry progress
  // (synced to the whole cover). Scale only (full opacity always) — the covered
  // sheet recedes under the incoming one without draining the page's colour.
  const recede = useTransform(nextEnter, [0, 1], [1, 0.97]);
  const scale = useTransform(
    [enterScale, recede],
    ([a, b]) => (a as number) * (isLast || noPin ? 1 : (b as number)),
  );

  const isSplit = variant === "split-x" || variant === "split-y";
  const style: Record<string, unknown> = { y, x, opacity, scale };
  if (isSplit) style.clipPath = clipPath;

  return (
    <motion.div
      ref={panelRef}
      className={`story-panel${noPin ? " no-pin" : ""}`}
      style={style as never}
    >
      {children}
    </motion.div>
  );
}

export function StoryStack({
  children,
  className = "",
  variants,
}: {
  children: ReactNode;
  /** "" = full-bleed page sheets; "cards" = card-shaped panels (About column). */
  className?: string;
  /** Per-panel entry transitions; falls back to a rotating default cycle. */
  variants?: StoryVariant[];
}) {
  const enabled = useStackEnabled();
  const items = Children.toArray(children); // drops null/undefined children
  const refs = useMemo(
    () => items.map(() => createRef<HTMLDivElement>()),
    // one ref per panel; count is stable per page
    [items.length],
  );
  // Shared entry-progress slots (panel i's recede reads slot i+1).
  const enters = useMemo(
    () => items.map(() => motionValue(0)),
    [items.length],
  );

  if (!enabled) return <>{children}</>;

  return (
    <div className={`story-stack ${className}`.trim()}>
      {items.map((child, i) => (
        <StoryPanel
          key={i}
          panelRef={refs[i]}
          isLast={i === items.length - 1}
          variant={variants?.[i] ?? CYCLE[i % CYCLE.length]}
          enterOut={enters[i]}
          nextEnter={enters[i + 1] || enters[i]}
        >
          {child}
        </StoryPanel>
      ))}
    </div>
  );
}
