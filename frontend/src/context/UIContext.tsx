/* Overlay panel manager — cart drawer + checkout / track / project modals.
   Mirrors the stack-based panel manager in app.js: one shared dimmed overlay,
   body scroll-lock while open, Escape closes the top panel. Panels reuse the
   existing CSS (.drawer.open / .modal.open / .overlay.open). */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

export type Panel =
  | { type: "cart" }
  | { type: "checkout" }
  | { type: "track"; id?: string }
  | { type: "project"; id: string };

interface UICtx {
  stack: Panel[];
  top: Panel | null;
  isOpen: (type: Panel["type"]) => boolean;
  open: (panel: Panel) => void;
  close: (type?: Panel["type"]) => void;
  closeAll: () => void;
  openCart: () => void;
  openCheckout: () => void;
  openTrack: (id?: string) => void;
  openProject: (id: string) => void;
}
const Ctx = createContext<UICtx | null>(null);

export function UIProvider({ children }: { children: ReactNode }) {
  const [stack, setStack] = useState<Panel[]>([]);

  const open = useCallback((panel: Panel) => {
    setStack((s) => (s.some((p) => p.type === panel.type) ? s : [...s, panel]));
  }, []);

  const close = useCallback((type?: Panel["type"]) => {
    setStack((s) => {
      if (!s.length) return s;
      if (!type) return s.slice(0, -1);
      return s.filter((p) => p.type !== type);
    });
  }, []);

  const closeAll = useCallback(() => setStack([]), []);

  // Body scroll-lock while any panel is open.
  useEffect(() => {
    document.body.style.overflow = stack.length ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [stack.length]);

  // Escape closes the top panel.
  useEffect(() => {
    if (!stack.length) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setStack((s) => s.slice(0, -1));
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [stack.length]);

  const value = useMemo<UICtx>(
    () => ({
      stack,
      top: stack[stack.length - 1] || null,
      isOpen: (type) => stack.some((p) => p.type === type),
      open,
      close,
      closeAll,
      openCart: () => open({ type: "cart" }),
      openCheckout: () => open({ type: "checkout" }),
      openTrack: (id?: string) => open({ type: "track", id }),
      openProject: (id: string) => open({ type: "project", id }),
    }),
    [stack, open, close, closeAll],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useUI(): UICtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useUI must be used within UIProvider");
  return ctx;
}
