/* =============================================================================
   SITE CONFIG — typed port of assets/js/config.js. Single source of truth for
   brand/identity, contact, payments and sales wiring. Backend API stays
   same-origin (apiBase ""). Keep values in sync with the brand.
   ========================================================================== */

export interface PaymentMethodChip {
  id: string;
  label: string;
  group: string;
}
export interface PaymentInstruction {
  label: string;
  value: string;
  sub?: string;
  soon?: boolean;
}
export interface HeroStat {
  value: number;
  suffix: string;
  label: string;
  auto?: string;
}

export interface SiteConfig {
  name: string;
  brand: string;
  initials: string;
  role: string;
  tagline: string;
  bio: string;
  location: string;
  availability: string;
  photo: string;
  email: string;
  whatsapp: string;
  fiverr: string;
  socials: Record<string, string>;
  formspreeId: string;
  currency: string;
  currencyCode: string;
  apiBase: string;
  chat: { enabled: boolean; title: string; subtitle: string };
  payments: PaymentMethodChip[];
  paymentInstructions: { note: string; methods: PaymentInstruction[] };
  stats: HeroStat[];
  siteUrl: string;
}

export const CONFIG: SiteConfig = {
  // --- Identity ---
  name: "Muhammad Ali Raza",
  brand: "Muhammad Ali Raza",
  initials: "MAR",
  role: "Full-Stack Dev · Automation Engineer · UI/UX & Packaging Designer",
  tagline: "I design, build, and automate the products that grow your business.",
  bio:
    "I'm a multidisciplinary freelancer helping startups and founders ship " +
    "fast. From Python SaaS dashboards and Selenium automation to Figma " +
    "interfaces and premium product packaging — I take projects from idea to " +
    "delivery, on time and production-ready.",
  location: "Remote · Available Worldwide",
  availability: "Available for new projects",
  photo: "/assets/img/profile.jpg",

  // --- Contact ---
  email: "shahjee975@gmail.com",
  whatsapp: "923414527256",
  fiverr: "#",

  // --- Socials (empty string => dimmed placeholder) ---
  socials: {
    instagram: "",
    facebook: "",
    linkedin: "",
    x: "",
    github: "https://github.com/SMARNB",
  },

  // --- Sales wiring ---
  formspreeId: "xwvdkyve",
  currency: "$",
  currencyCode: "USD",
  apiBase: "", // same origin

  // --- Live chat ---
  chat: {
    enabled: true,
    title: "Chat with us",
    subtitle: "Ask about services, pricing, or start an order",
  },

  // --- Payment trust grid (only methods that can actually receive money) ---
  payments: [
    { id: "card", label: "Credit / Debit card", group: "Cards · local & international" },
    { id: "raast", label: "Raast (instant)", group: "Bank / wallet · Pakistan" },
    { id: "sadapay", label: "SadaPay", group: "Bank / wallet · Pakistan" },
    { id: "jazzcash", label: "JazzCash", group: "Bank / wallet · Pakistan" },
  ],

  // --- Manual payment details (shown to a client on an unpaid order) ---
  paymentInstructions: {
    note: "Send the exact order total, then upload your payment screenshot below (it must show the date & time) so I can confirm and start your project.",
    methods: [
      { label: "Raast", value: "0324 2225073", sub: "Instant transfer · linked to HBL & SadaPay" },
      { label: "SadaPay", value: "0324 2225073", sub: "Send to this number" },
      {
        label: "JazzCash",
        value: "Merchant ID: MC815133",
        sub: "Activating soon — please use Raast/SadaPay for now",
        soon: true,
      },
    ],
  },

  // --- Hero trust stats ---
  stats: [
    { value: 10, suffix: "", label: "Services offered", auto: "services" },
    { value: 100, suffix: "%", label: "Source & rights to you" },
    { value: 0, suffix: "%", label: "Cancellation rate" },
    { value: 24, suffix: "h", label: "Avg. response time" },
  ],

  siteUrl: "https://smarnb.onrender.com",
};
