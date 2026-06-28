/* Shared primary-nav definitions (identical across Home & Store, as in the
   vanilla site). Hash links route through the SPA and scroll to the section. */
export interface NavItem {
  label: string;
  to: string; // react-router path, may include a hash
}

export const PRIMARY_NAV: NavItem[] = [
  { label: "Home", to: "/" },
  { label: "Store", to: "/store" },
  { label: "Services", to: "/store#services" },
  { label: "Pricing", to: "/store#pricing" },
  { label: "Work", to: "/#work" },
  { label: "About", to: "/#about" },
  { label: "Contact", to: "/#contact" },
];

export const MOBILE_NAV: NavItem[] = [
  { label: "Home", to: "/" },
  { label: "Store", to: "/store" },
  { label: "Services", to: "/store#services" },
  { label: "Pricing", to: "/store#pricing" },
  { label: "Products", to: "/store#products" },
  { label: "Work", to: "/#work" },
  { label: "Projects", to: "/#projects" },
  { label: "About", to: "/#about" },
  { label: "FAQ", to: "/#faq" },
  { label: "Contact", to: "/#contact" },
];
