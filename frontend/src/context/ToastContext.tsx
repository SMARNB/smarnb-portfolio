/* Lightweight toast notifications (port of the toast() in app.js) with a small
   enter/leave animation via AnimatePresence. */
import { createContext, useCallback, useContext, useRef, useState } from "react";
import type { ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Icon } from "../lib/icons";

interface Toast {
  id: number;
  icon: string;
  msg: string;
}
interface ToastCtx {
  toast: (msg: string, icon?: string) => void;
}
const Ctx = createContext<ToastCtx>({ toast: () => {} });

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const seq = useRef(0);

  const toast = useCallback((msg: string, icon = "check") => {
    const id = ++seq.current;
    setToasts((t) => [...t, { id, icon, msg }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 2600);
  }, []);

  return (
    <Ctx.Provider value={{ toast }}>
      {children}
      <div className="toasts" aria-live="polite" aria-atomic="false">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              className="toast"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            >
              <span className="ic">
                <Icon name={t.icon} />
              </span>
              <span>{t.msg}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </Ctx.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => useContext(Ctx);
