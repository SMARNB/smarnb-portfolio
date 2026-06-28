/* Mount Lenis inertial smooth scrolling for the lifetime of the component.
   Disabled when the user prefers reduced motion. */
import { useEffect } from "react";
import Lenis from "lenis";
import { useReducedMotion } from "framer-motion";
import { setLenis } from "./lenis";

export function useSmoothScroll(): void {
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) {
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
