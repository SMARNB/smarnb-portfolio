/* Shared primary-nav definitions. Each entry is a real React-Router route (a
   distinct, crawlable page) — no more single-page #hash anchors. */
export interface NavItem {
  label: string;
  to: string;
}

export const PRIMARY_NAV: NavItem[] = [
  { label: "Home", to: "/" },
  { label: "Services", to: "/services" },
  { label: "Work", to: "/work" },
  { label: "Projects", to: "/projects" },
  { label: "Blog", to: "/blog" },
  { label: "About", to: "/about" },
  { label: "Store", to: "/store" },
  { label: "Contact", to: "/contact" },
];

// Mobile shows the same routes (the full-screen menu has room for all of them).
export const MOBILE_NAV: NavItem[] = PRIMARY_NAV;
