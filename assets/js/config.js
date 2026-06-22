/* =============================================================================
   SITE CONFIG  —  ✏️ EDIT THIS FILE FIRST
   -----------------------------------------------------------------------------
   This is the single source of truth for your personal/brand details.
   Change the values below and the whole site updates. Nothing else required.
   ========================================================================== */

window.SITE_CONFIG = {
  // --- Identity -------------------------------------------------------------
  name: "Muhammad Ali Raza",
  brand: "ALIRA",                 // short logo/wordmark text
  initials: "AR",                 // shown in the logo mark
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
  whatsapp: "0000000000",         // TODO: replace with your WhatsApp number
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
  formspreeId: "",                // TODO: e.g. "xpzgkqab"

  currency: "$",
  currencyCode: "USD",

  // --- Trust stats (shown in hero / about) ----------------------------------
  stats: [
    { value: 120, suffix: "+", label: "Projects delivered" },
    { value: 95,  suffix: "+", label: "Happy clients" },
    { value: 99,  suffix: "%", label: "On-time delivery" },
    { value: 5,   suffix: "★", label: "Average rating", decimals: 0 },
  ],

  // --- SEO ------------------------------------------------------------------
  siteUrl: "https://example.com",  // TODO: your final domain (used for SEO tags)
};
