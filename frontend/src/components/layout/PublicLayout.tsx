/* Public layout (Home + Store): persistent shell — header, footer, chat widget,
   cart drawer + modals — with iOS-style cross-route transitions and Lenis smooth
   scrolling. The shell stays mounted across route changes; only the page swaps. */
import { useEffect, useRef, useState } from "react";
import { useLocation, useOutlet } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { CatalogProvider } from "../../context/CatalogContext";
import { CartProvider } from "../../context/CartContext";
import { ToastProvider } from "../../context/ToastContext";
import { UIProvider, useUI } from "../../context/UIContext";
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

      <main id="main">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={location.pathname}
            initial={reduce ? false : { opacity: 0, y: 12, scale: 0.995 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduce ? undefined : { opacity: 0, y: -8, scale: 0.995 }}
            transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
          >
            {outlet}
          </motion.div>
        </AnimatePresence>
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
