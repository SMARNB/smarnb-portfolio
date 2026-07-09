/* StoryStack — the scroll-story used on Home / Services / Work / About: each child
   becomes a "sheet" that pins below the floating header while the next one slides
   up over it; the covered sheet gently scales down and dims (driven by the next
   sheet's approach, via framer-motion useScroll on the next panel's rect).

   Grounded in classic sticky stacking (each panel `position: sticky` at a shared
   top inside one flow container), so the browser does the pinning and the effect
   costs no scroll listeners beyond framer's rAF-batched rect reads.

   Safety rails:
   - Desktop-only: enabled at ≥900px fine-pointer viewports and without
     prefers-reduced-motion — otherwise children render in plain flow.
   - A panel taller than the viewport budget skips pinning (`no-pin`) so its lower
     content can never be covered before it was seen; the flow still reads well.
   - The last panel never shrinks (nothing ever covers it). */
import { Children, createRef, useEffect, useMemo, useState } from "react";
import type { ReactNode, RefObject } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";

/** Keep in sync with --stack-top in global.css (header 62px + gap). */
const STACK_TOP_PX = 78;

function useStackEnabled(): boolean {
  const reduce = useReducedMotion();
  const [capable, setCapable] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 900px) and (hover: hover) and (pointer: fine)");
    const update = () => setCapable(mq.matches);
    update();
    mq.addEventListener?.("change", update);
    return () => mq.removeEventListener?.("change", update);
  }, []);
  return capable && !reduce;
}

function StoryPanel({
  panelRef,
  nextRef,
  isLast,
  children,
}: {
  panelRef: RefObject<HTMLDivElement>;
  nextRef: RefObject<HTMLDivElement>; // = panelRef for the last panel (unused)
  isLast: boolean;
  children: ReactNode;
}) {
  // Panels taller than the viewport budget must not pin.
  const [noPin, setNoPin] = useState(false);
  useEffect(() => {
    const el = panelRef.current;
    if (!el) return;
    const check = () =>
      setNoPin(el.offsetHeight > window.innerHeight - STACK_TOP_PX - 24);
    check();
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(check) : null;
    ro?.observe(el);
    window.addEventListener("resize", check, { passive: true });
    return () => {
      ro?.disconnect();
      window.removeEventListener("resize", check);
    };
  }, [panelRef]);

  // Outgoing motion, driven by the NEXT panel's top travelling up the viewport.
  const { scrollYProgress } = useScroll({
    target: nextRef,
    offset: ["start 96%", "start 30%"],
  });
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.955]);
  const opacity = useTransform(scrollYProgress, [0, 1], [1, 0.45]);

  const animated = !isLast && !noPin;
  return (
    <motion.div
      ref={panelRef}
      className={`story-panel${noPin ? " no-pin" : ""}`}
      style={animated ? { scale, opacity } : undefined}
    >
      {children}
    </motion.div>
  );
}

export function StoryStack({
  children,
  className = "",
}: {
  children: ReactNode;
  /** "" = full-bleed page sheets; "cards" = card-shaped panels (About column). */
  className?: string;
}) {
  const enabled = useStackEnabled();
  const items = Children.toArray(children); // drops null/undefined children
  const refs = useMemo(
    () => items.map(() => createRef<HTMLDivElement>()),
    // one ref per panel; count is stable per page
    [items.length],
  );

  if (!enabled) return <>{children}</>;

  return (
    <div className={`story-stack ${className}`.trim()}>
      {items.map((child, i) => (
        <StoryPanel
          key={i}
          panelRef={refs[i]}
          nextRef={refs[i + 1] || refs[i]}
          isLast={i === items.length - 1}
        >
          {child}
        </StoryPanel>
      ))}
    </div>
  );
}
