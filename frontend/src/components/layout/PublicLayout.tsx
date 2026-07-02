/* Public layout (Home + Store): persistent shell — header, footer, chat widget,
   cart drawer + modals — with iOS-style cross-route transitions and Lenis smooth
   scrolling. The shell stays mounted across route changes; only the page swaps. */
import { useEffect, useRef, useState } from "react";
import { useLocation, useOutlet } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { CatalogProvider } from "../../context/CatalogContext";
import { CartProvider } from "../../context/CartContext";
import { ToastProvider } from "../../context/ToastContext";
import { UIProvider, useUI } from "../../context/UIContext";
import { useToast } from "../../context/ToastContext";
import { API } from "../../lib/api";
import { useSmoothScroll } from "../../lib/useLenis";
import { scrollToHash, scrollToTarget } from "../../lib/lenis";
import { Header } from "./Header";
import { MobileMenu } from "./MobileMenu";
import { Footer } from "./Footer";
import { BackToTop } from "./BackToTop";
import { CartDrawer } from "../panels/CartDrawer";
import { CheckoutModal } from "../panels/CheckoutModal";
import { TrackModal } from "../panels/TrackModal";
import { ProjectModal } from "../panels/ProjectModal";
import { ChatWidget } from "../chat/ChatWidget";

export function PublicLayout() {
  return (
    <CatalogProvider>
      <CartProvider>
        <ToastProvider>
          <UIProvider>
            <Shell />
          </UIProvider>
        </ToastProvider>
      </CartProvider>
    </CatalogProvider>
  );
}

function Shell() {
  useSmoothScroll();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const outlet = useOutlet();
  const reduce = useReducedMotion();
  const { stack, close } = useUI();

  // Close the mobile menu on route change.
  useEffect(() => setMenuOpen(false), [location.pathname]);

  return (
    <>
      <Header onMenu={() => setMenuOpen((o) => !o)} menuOpen={menuOpen} />
      <MobileMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
      <ScrollManager />
      <SafepayReturn />

      <main id="main">
        {/* Keyed remount per route → a clean enter-fade and a guaranteed content
            swap on every navigation. (AnimatePresence mode="wait" could deadlock
            when an entering page didn't complete its exit, freezing the content.) */}
        <motion.div
          key={location.pathname}
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        >
          {outlet}
        </motion.div>
      </main>

      <Footer />
      <BackToTop />

      {/* Overlay + panels */}
      <div
        className={`overlay${stack.length ? " open" : ""}`}
        onClick={() => close()}
        aria-hidden={!stack.length}
      />
      <CartDrawer />
      <CheckoutModal />
      <TrackModal />
      <ProjectModal />

      <ChatWidget />
    </>
  );
}

/* After a Safepay hosted-checkout redirect the buyer lands back here with ?sfpy=<id>.
   Verify the payment server-side (the browser can't fake it — this also marks the
   order paid), confirm to the buyer, and jump them to order tracking. */
function SafepayReturn() {
  const { toast } = useToast();
  const { openTrack } = useUI();
  const done = useRef(false);

  useEffect(() => {
    if (done.current) return;
    const m = /[?&]sfpy=([^&]+)/.exec(window.location.search || "");
    if (!m) return;
    done.current = true;
    const id = decodeURIComponent(m[1]);
    try {
      window.history.replaceState({}, "", window.location.pathname);
    } catch {
      /* ignore */
    }
    API.get<{ paid?: boolean }>("/api/payments/safepay/verify/" + encodeURIComponent(id))
      .then((r) => {
        if (r && r.paid) {
          toast("Payment received for " + id + " ✅", "check");
          openTrack(id);
        } else {
          toast("Payment for " + id + " is still processing.", "doc");
        }
      })
      .catch(() => toast("We couldn't confirm the payment yet — it may still be processing.", "doc"));
  }, [toast, openTrack]);

  return null;
}

/* Scroll to the hash target (or top) on every navigation. Instant when the page
   changed, smooth for in-page anchor jumps — mirrors the old SPA behavior. */
function ScrollManager() {
  const { pathname, hash } = useLocation();
  const prevPath = useRef(pathname);

  useEffect(() => {
    const changedPage = prevPath.current !== pathname;
    prevPath.current = pathname;
    const t = window.setTimeout(
      () => {
        if (hash) {
          const ok = scrollToHash(hash, changedPage);
          if (!ok && changedPage) scrollToTarget(0, { immediate: true });
        } else {
          scrollToTarget(0, { immediate: changedPage });
        }
      },
      changedPage ? 70 : 0,
    );
    return () => clearTimeout(t);
  }, [pathname, hash]);

  return null;
}
