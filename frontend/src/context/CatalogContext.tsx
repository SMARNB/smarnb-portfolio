/* Services catalog — starts from the built-in data, then merges the live backend
   catalog (port of fetchAndMergeServices in app.js). Once the developer has
   imported the built-ins ("managed"), the DB becomes authoritative; otherwise DB
   services are merged onto the built-ins (DB overrides by slug/id). Offline → the
   built-in list is kept so the page never blanks. */
import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { CONFIG } from "../lib/config";
import { services as builtinServices } from "../lib/data";
import type { Service } from "../lib/data";
import type { PublicCatalog, ServiceOut } from "../lib/types";

interface CatalogCtx {
  services: Service[];
}
const Ctx = createContext<CatalogCtx>({ services: builtinServices });

function mapDbService(s: ServiceOut): Service {
  return {
    id: s.slug,
    icon: s.icon || "spark",
    category: s.category || "Development",
    title: s.title,
    short: s.short || "",
    tags: s.tags || [],
    deliverables: s.deliverables || [],
    packages: s.packages || [],
  };
}

export function CatalogProvider({ children }: { children: ReactNode }) {
  const [services, setServices] = useState<Service[]>(builtinServices);

  useEffect(() => {
    let cancelled = false;
    fetch((CONFIG.apiBase || "") + "/api/services", { headers: { Accept: "application/json" } })
      .then((r) => {
        if (!r.ok) throw new Error("no api");
        return r.json();
      })
      .then((res: PublicCatalog | ServiceOut[]) => {
        if (cancelled) return;
        const list = Array.isArray(res) ? res : res.services || [];
        if (!Array.isArray(list)) return;
        const managed = !Array.isArray(res) && res.managed;
        if (managed) {
          if (!list.length) return; // safety: never blank the page
          setServices(list.map(mapDbService));
          return;
        }
        if (!list.length) return;
        // Merge DB services onto the built-ins (override by id, else append).
        setServices((prev) => {
          const next = prev.slice();
          const idx: Record<string, number> = {};
          next.forEach((s, i) => (idx[s.id] = i));
          list.forEach((s) => {
            const mapped = mapDbService(s);
            if (idx[s.slug] != null) next[idx[s.slug]] = mapped;
            else next.push(mapped);
          });
          return next;
        });
      })
      .catch(() => {
        /* offline / static-only → keep built-in services */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return <Ctx.Provider value={{ services }}>{children}</Ctx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const useCatalog = () => useContext(Ctx);
