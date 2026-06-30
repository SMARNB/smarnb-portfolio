/* Kick off the public data fetches in parallel the moment the app's JS executes,
   so /api/services and /api/testimonials race together instead of waterfalling
   from two separate component effects (mounted at different points in the tree).
   Each resolves to parsed JSON, or null on offline/error so callers fall back to
   their built-in data. Imported for its side effect at the app entry (main.tsx). */
import { CONFIG } from "./config";

const base = CONFIG.apiBase || "";
const opts: RequestInit = { headers: { Accept: "application/json" } };

function getJSON<T>(path: string): Promise<T | null> {
  return fetch(base + path, opts)
    .then((r) => (r.ok ? (r.json() as Promise<T>) : null))
    .catch(() => null);
}

export const servicesPromise = getJSON<unknown>("/api/services");
export const testimonialsPromise = getJSON<unknown>("/api/testimonials");
