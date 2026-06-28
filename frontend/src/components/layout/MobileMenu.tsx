/* Full-screen mobile nav (shown when the inline links don't fit). Closes on any
   link tap and on Escape. */
import { useEffect } from "react";
import { Link } from "react-router-dom";
import { MOBILE_NAV } from "./nav";

export function MobileMenu({ open, onClose }: { open: boolean; onClose: () => void }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  return (
    <nav className={`mobile-menu${open ? " open" : ""}`} id="mobileMenu" aria-label="Mobile">
      {MOBILE_NAV.map((item) => (
        <Link key={item.to} to={item.to} onClick={onClose}>
          {item.label}
        </Link>
      ))}
      <Link to="/app" onClick={onClose}>
        My Projects (Client login)
      </Link>
      <Link className="btn btn-primary" to="/#contact" onClick={onClose}>
        Start a project
      </Link>
    </nav>
  );
}
