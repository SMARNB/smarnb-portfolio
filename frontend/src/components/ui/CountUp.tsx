/* Count-up number animation that fires when scrolled into view. Used by the hero
   trust stats. Honors prefers-reduced-motion (shows the final value at once). */
import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";

export function CountUp({
  value,
  suffix = "",
  duration = 1400,
}: {
  value: number;
  suffix?: string;
  duration?: number;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const [display, setDisplay] = useState(reduce ? value : 0);
  const started = useRef(false);

  useEffect(() => {
    if (reduce) {
      setDisplay(value);
      return;
    }
    const el = ref.current;
    if (!el) return;

    const run = () => {
      if (started.current) return;
      started.current = true;
      let t0: number | null = null;
      const step = (ts: number) => {
        if (t0 === null) t0 = ts;
        const p = Math.min((ts - t0) / duration, 1);
        setDisplay(Math.round(value * (1 - Math.pow(1 - p, 3))));
        if (p < 1) requestAnimationFrame(step);
        else setDisplay(value);
      };
      requestAnimationFrame(step);
    };

    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          run();
          obs.disconnect();
        }
      },
      { threshold: 0.2 },
    );
    obs.observe(el);
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) run();

    return () => obs.disconnect();
  }, [value, duration, reduce]);

  return (
    <span ref={ref}>
      {display}
      {suffix}
    </span>
  );
}
