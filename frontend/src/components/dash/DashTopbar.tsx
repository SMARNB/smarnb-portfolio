/* Shared dashboard topbar (client + admin) — brand, role pill, signed-in identity,
   animated theme toggle and logout. */
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Icon } from "../../lib/icons";
import { BrandMark } from "../layout/BrandMark";
import { useTheme } from "../../context/ThemeContext";
import type { User } from "../../lib/types";

export function DashTopbar({
  brandText,
  pill,
  user,
  onLogout,
}: {
  brandText: string;
  pill: string;
  user: User | null;
  onLogout: () => void;
}) {
  const { theme, toggle } = useTheme();
  const reduce = useReducedMotion();

  return (
    <header className="dash-topbar">
      <div className="container">
        <Link className="brand" to="/">
          <BrandMark size={30} />
          <span className="brand-text">{brandText}</span>
        </Link>
        <span className="dash-title">
          <span className="pill">{pill}</span>
        </span>
        <div className="spacer" />
        {user && (
          <span className="who">
            <b>{user.name || user.email}</b>
            <small>{user.email}</small>
          </span>
        )}
        <button className="icon-btn" aria-label="Toggle theme" onClick={toggle}>
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
        {user && (
          <button className="btn btn-ghost btn-sm" onClick={onLogout}>
            Log out
          </button>
        )}
      </div>
    </header>
  );
}
