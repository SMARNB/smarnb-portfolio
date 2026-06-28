/* Approved client reviews from the backend, prepended to the curated samples
   (port of fetchTestimonials in app.js). Offline → just the samples. */
import { useEffect, useState } from "react";
import { CONFIG } from "./config";
import { sampleTestimonials } from "./data";
import type { SampleTestimonial } from "./data";
import type { Testimonial } from "./types";

export function useTestimonials(): SampleTestimonial[] {
  const [list, setList] = useState<SampleTestimonial[]>(sampleTestimonials);

  useEffect(() => {
    let cancelled = false;
    fetch((CONFIG.apiBase || "") + "/api/testimonials", { headers: { Accept: "application/json" } })
      .then((r) => {
        if (!r.ok) throw new Error("no api");
        return r.json();
      })
      .then((remote: Testimonial[]) => {
        if (cancelled || !Array.isArray(remote) || !remote.length) return;
        const real: SampleTestimonial[] = remote.map((t) => ({
          name: t.name,
          role: t.role || "Client",
          loc: t.location || "",
          rating: t.rating || 5,
          text: t.text,
        }));
        setList(real.concat(sampleTestimonials));
      })
      .catch(() => {
        /* offline → keep samples */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return list;
}
