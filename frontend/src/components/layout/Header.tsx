/* Site header — brand, fit-based responsive nav (inline links only while they
   fit, hamburger otherwise), theme toggle, track/cart actions + cart badge. */
import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { CONFIG } from "../../lib/config";
import { Icon } from "../../lib/icons";
import { useTheme } from "../../context/ThemeContext";
import { useCart } from "../../context/CartContext";
import { useUI } from "../../context/UIContext";
import { PRIMARY_NAV } from "./nav";

function navActive(to: string, pathname: string): boolean {
  if (to === "/") return pathname === "/";
  return pathname === to || pathname.startsWith(to + "/");
}

export function Header({ onMenu, menuOpen }: { onMenu: () => void; menuOpen: boolean }) {
  const { theme, toggle } = useTheme();
  const { count } = useCart();
  const { openCart, openTrack } = useUI();
  const { pathname } = useLocation();
  const reduce = useReducedMotion();

  const headerRef = useRef<HTMLElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const [scrolled, setScrolled] = useState(false);
  const [expanded, setExpanded] = useState(true);

  // Header background on scroll.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Fit-based nav: show inline links only while they actually fit. Measured
  // robustly so a mistimed first measurement — e.g. right after returning from a
  // dashboard route, before fonts/CSS have settled — self-corrects instead of
  // getting stuck on the hamburger. Re-runs on rAF, on font load, on any container
  // resize (ResizeObserver), and after a couple of short delays.
  useEffect(() => {
    const nav = navRef.current;
    if (!nav) return;
    let raf = 0;
    const measure = () => {
      cancelAnimationFrame(raf);
      setExpanded(true); // reveal links so scrollWidth reflects their natural width
      raf = requestAnimationFrame(() => {
        const el = navRef.current;
        if (!el || el.clientWidth === 0) return; // not laid out yet — don't collapse
        setExpanded(el.scrollWidth <= el.clientWidth + 1);
      });
    };
    measure();
    const t1 = window.setTimeout(measure, 120);
    const t2 = window.setTimeout(measure, 450);
    window.addEventListener("resize", measure, { passive: true });
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(measure) : null;
    ro?.observe(nav);
    if (document.fonts?.ready) document.fonts.ready.then(measure).catch(() => {});
    return () => {
      cancelAnimationFrame(raf);
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      window.removeEventListener("resize", measure);
      ro?.disconnect();
    };
  }, []);

  return (
    <header
      ref={headerRef}
      className={`header${scrolled ? " scrolled" : ""}${expanded ? " nav-expanded" : ""}`}
      id="header"
    >
      <div className="container nav" ref={navRef as React.RefObject<HTMLDivElement>}>
        <Link className="brand" to="/" aria-label="Home">
          <span className="mark">{CONFIG.initials}</span>
          <span className="brand-text">{CONFIG.brand}</span>
        </Link>

        <nav className="nav-links" aria-label="Primary">
          {PRIMARY_NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={navActive(item.to, pathname) ? "active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="nav-actions">
          <Link className="icon-btn" to="/app" aria-label="Client login / my projects" title="My projects">
            <Icon name="user" size={20} />
          </Link>
          <button className="icon-btn" id="themeToggle" aria-label="Toggle light/dark theme" onClick={toggle}>
            <AnimatePresence mode="wait" initial={false}>
              <motion.span
                key={theme}
                initial={reduce ? false : { rotate: -90, opacity: 0, scale: 0.6 }}
                animate={{ rotate: 0, opacity: 1, scale: 1 }}
                exit={reduce ? undefined : { rotate: 90, opacity: 0, scale: 0.6 }}
                transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                style={{ display: "grid", placeItems: "center" }}
              >
                <Icon name={theme === "dark" ? "sun" : "moon"} size={20} />
              </motion.span>
            </AnimatePresence>
          </button>
          <button className="icon-btn" aria-label="Track your order" title="Track order" onClick={() => openTrack()}>
            <Icon name="doc" size={20} />
          </button>
          <button className="icon-btn" aria-label="Open cart" onClick={openCart}>
            <Icon name="cart" size={20} />
            <span className={`cart-count${count > 0 ? " show" : ""}`} aria-hidden="true">
              {count}
            </span>
          </button>
          <button
            className="icon-btn menu-toggle"
            aria-label="Open menu"
            aria-expanded={menuOpen}
            aria-controls="mobileMenu"
            onClick={onMenu}
          >
            <Icon name={menuOpen ? "close" : "menu"} size={20} />
          </button>
        </div>
      </div>
    </header>
  );
}
