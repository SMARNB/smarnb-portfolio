/* Scrollspy — tracks which section[id] is centered in the viewport so the nav can
   highlight the matching link (port of the scrollspy in app.js mountObservers).
   Re-runs when `deps` change (e.g. on route change, when sections differ). */
import { useEffect, useState } from "react";

export function useScrollSpy(deps: unknown[] = []): string {
  const [activeId, setActiveId] = useState("");

  useEffect(() => {
    const sections = Array.from(document.querySelectorAll<HTMLElement>("section[id]"));
    if (!sections.length) {
      setActiveId("");
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) setActiveId((en.target as HTMLElement).id);
        });
      },
      { rootMargin: "-45% 0px -50% 0px" },
    );
    sections.forEach((s) => obs.observe(s));
    return () => obs.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return activeId;
}
