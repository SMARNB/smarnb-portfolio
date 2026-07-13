/* Mount Lenis inertial smooth scrolling for the lifetime of the component.
   Disabled when the user prefers reduced motion. */
import { useEffect } from "react";
import Lenis from "lenis";
import { useReducedMotion } from "framer-motion";
import { setLenis } from "./lenis";

/* On iOS, native momentum scroll is smoother than Lenis and Lenis only smooths
   the mouse WHEEL anyway (touch already uses native inertia) — so on iPhone its
   per-frame RAF is pure overhead that adds main-thread churn to the scroll-story
   and makes the scroll-linked transforms recompute more often. Skip it on iOS.
   Same probe as the other iOS fixes (global.css / StoryStack). */
const IOS =
  typeof CSS !== "undefined" && !!CSS.supports && CSS.supports("-webkit-touch-callout", "none");

export function useSmoothScroll(): void {
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce || IOS) {
      setLenis(null);
      return;
    }
    const lenis = new Lenis({
      duration: 1.1,
      easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });
    setLenis(lenis);

    let raf = 0;
    const loop = (time: number) => {
      lenis.raf(time);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      lenis.destroy();
      setLenis(null);
    };
  }, [reduce]);
}
