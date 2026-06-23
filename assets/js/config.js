/* =============================================================================
   SITE CONFIG  —  ✏️ EDIT THIS FILE FIRST
   -----------------------------------------------------------------------------
   This is the single source of truth for your personal/brand details.
   Change the values below and the whole site updates. Nothing else required.
   ========================================================================== */

window.SITE_CONFIG = {
  // --- Identity -------------------------------------------------------------
  name: "Muhammad Ali Raza",
  brand: "Muhammad Ali Raza",     // logo/wordmark text (shown in header & footer)
  initials: "MAR",                // shown in the small logo mark
  role: "Full-Stack Dev · Automation Engineer · UI/UX & Packaging Designer",
  tagline: "I design, build, and automate the products that grow your business.",
  bio:
    "I'm a multidisciplinary freelancer helping startups and founders ship " +
    "fast. From Python SaaS dashboards and Selenium automation to Figma " +
    "interfaces and premium product packaging — I take projects from idea to " +
    "delivery, on time and production-ready.",
  location: "Remote · Available Worldwide",
  availability: "Available for new projects",   // shows in the hero status pill
  photo: "assets/img/profile.jpg",              // profile photo (used in About + SEO)

  // --- Contact --------------------------------------------------------------
  email: "shahjee975@gmail.com",
  // WhatsApp number in FULL international format, digits only (no +, spaces, or dashes).
  // Example for US +1 (415) 555-0123  ->  "14155550123"
  whatsapp: "923414527256",       // WhatsApp (international format, digits only)
  fiverr: "#",                    // TODO: your Fiverr profile URL

  // --- Social links (leave "" to hide a link) -------------------------------
  socials: {
    linkedin: "",                            // TODO: your LinkedIn URL
    github: "https://github.com/SMARNB",     // your GitHub
    dribbble: "",                            // TODO
    instagram: "",                           // TODO
    upwork: "",                              // TODO
  },

  // --- Sales center wiring --------------------------------------------------
  // Formspree gives you a free form endpoint that emails you each order/request.
  // 1) Sign up at https://formspree.io  2) Create a form  3) Paste the ID here.
  // The ID is the part after /f/ in your endpoint, e.g. "xpzgkqab".
  // Leave as "" to skip email delivery (orders still save locally + WhatsApp works).
  formspreeId: "xwvdkyve",        // Formspree form (orders & messages also email you)

  currency: "$",
  currencyCode: "USD",

  // --- App backend (FastAPI) ------------------------------------------------
  // "" = same origin (the backend serves this site at the same domain).
  // For a split deploy (static site on Netlify, API on Render) set this to your
  // API URL, e.g. "https://your-app.onrender.com" (and add it to the CSP).
  apiBase: "",

  // --- Payment methods ------------------------------------------------------
  // Shown in the Payments section + selectable at checkout. The choice is saved
  // with the order; you then send a payment link/instructions to confirm.
  // To go LIVE with a gateway (Stripe etc.), see backend/PAYMENTS.md.
  payments: [
    { id: "jazzcash",      label: "JazzCash",                         group: "Local · Pakistan" },
    { id: "easypaisa",     label: "Easypaisa",                        group: "Local · Pakistan" },
    { id: "bank_pk",       label: "Bank transfer",                    group: "Local · Pakistan" },
    { id: "jazzcash_bnpl", label: "JazzCash — Pay Later (Yeylo)",     group: "Buy now, pay later" },
    { id: "baadmay",       label: "BaadMay — Pay Later",              group: "Buy now, pay later" },
    { id: "stripe",        label: "Credit / Debit card (Stripe)",     group: "International" },
    { id: "paypal",        label: "PayPal",                           group: "International" },
    { id: "wise",          label: "Wise",                             group: "International" },
    { id: "crypto",        label: "Crypto (USDT / BTC)",              group: "International" },
  ],

  // --- Trust stats (shown in hero) ------------------------------------------
  // ✏️ HONEST numbers only. These default to facts that are true for you today
  // (4 services, source always included, 0% cancellations, fast replies).
  // As you complete real orders, bump these up — don't inflate them.
  stats: [
    { value: 4,   suffix: "",  label: "Services offered", auto: "services" },
    { value: 100, suffix: "%", label: "Source & rights to you" },
    { value: 0,   suffix: "%", label: "Cancellation rate" },
    { value: 24,  suffix: "h", label: "Avg. response time" },
  ],

  // --- SEO ------------------------------------------------------------------
  siteUrl: "https://example.com",  // TODO: your final domain (used for SEO tags)
};
