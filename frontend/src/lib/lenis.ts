/* Lenis smooth-scroll singleton + helpers. Public pages mount it for inertial
   "Apple-style" scrolling; we keep a module ref so anchor links and the
   back-to-top button can drive it. All callers degrade gracefully when Lenis
   isn't running (e.g. prefers-reduced-motion). */
import Lenis from "lenis";

let lenis: Lenis | null = null;

export function setLenis(instance: Lenis | null): void {
  lenis = instance;
}
export function getLenis(): Lenis | null {
  return lenis;
}

const prefersReduced = () =>
  window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Smooth-scroll to an element or to the top. Falls back to native behavior. */
export function scrollToTarget(target: HTMLElement | number, opts?: { immediate?: boolean }): void {
  const immediate = opts?.immediate || prefersReduced();
  if (lenis) {
    lenis.scrollTo(target, { immediate });
    return;
  }
  if (typeof target === "number") {
    window.scrollTo({ top: target, behavior: immediate ? "auto" : "smooth" });
  } else {
    target.scrollIntoView({ behavior: immediate ? "auto" : "smooth" });
  }
}

export function scrollToHash(hash: string, immediate = false): boolean {
  if (!hash || hash.length < 2) return false;
  let el: HTMLElement | null = null;
  try {
    el = document.querySelector<HTMLElement>(hash);
  } catch {
    el = null;
  }
  if (!el) return false;
  scrollToTarget(el, { immediate });
  return true;
}
