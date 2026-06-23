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

  // --- Social links ---------------------------------------------------------
  // ✏️ EDIT HERE: paste your full profile URL between the quotes for each one.
  //    • A link with a URL  → its icon shows in the footer automatically.
  //    • A link left as ""  → that icon is hidden (no broken/empty links).
  //    Nothing else to change — the footer icons update from these values.
  socials: {
    instagram: "",   // ← paste here, e.g. "https://instagram.com/yourhandle"
    facebook:  "",   // ← paste here, e.g. "https://facebook.com/yourpage"
    linkedin:  "",   // ← paste here, e.g. "https://linkedin.com/in/yourname"
    x:         "",   // ← paste here, e.g. "https://x.com/yourhandle"   (Twitter/X)
    github:    "https://github.com/SMARNB",   // ← already set to your GitHub
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

  // --- Live chat + assistant ------------------------------------------------
  // The floating chat widget. The bot answers instantly from your services
  // catalog; you can take over live from the developer dashboard's Inbox.
  // Requires the backend to be running (it degrades to WhatsApp/email if not).
  chat: {
    enabled: true,
    title: "Chat with us",
    subtitle: "Ask about services, pricing, or start an order",
  },

  // --- Payment methods (the trust-signal grid on the homepage) --------------
  // Shown in the Payments section. The actual "pay" details live in
  // paymentInstructions below (shown to a client on their order).
  payments: [
    { id: "raast",    label: "Raast (instant)",       group: "Local · Pakistan" },
    { id: "sadapay",  label: "SadaPay",               group: "Local · Pakistan" },
    { id: "jazzcash", label: "JazzCash",              group: "Local · Pakistan" },
    { id: "card",     label: "Credit / Debit card",   group: "International" },
    { id: "paypal",   label: "PayPal",                group: "International" },
    { id: "wise",     label: "Wise",                  group: "International" },
    { id: "crypto",   label: "Crypto (USDT / BTC)",   group: "International" },
  ],

  // --- Manual payment details (shown to a client on their order's "Pay now") -
  // ✏️ Update these as your accounts change. These appear ONLY in the client
  // dashboard for a specific unpaid order — not publicly on the homepage.
  paymentInstructions: {
    note: "Send the exact order total, then upload your receipt screenshot in the chat (bottom-right) so I can confirm and start your project.",
    methods: [
      { label: "Raast",   value: "0324 2225073", sub: "Instant transfer · linked to HBL & SadaPay" },
      { label: "SadaPay", value: "0324 2225073", sub: "Send to this number" },
      { label: "JazzCash", value: "Merchant ID: MC815133", sub: "Activating soon — please use Raast/SadaPay for now", soon: true },
    ],
  },

  // --- Trust stats (shown in hero) ------------------------------------------
  // ✏️ HONEST numbers only. These default to facts that are true for you today
  // (4 services, source always included, 0% cancellations, fast replies).
  // As you complete real orders, bump these up — don't inflate them.
  stats: [
    { value: 10,  suffix: "",  label: "Services offered", auto: "services" },
    { value: 100, suffix: "%", label: "Source & rights to you" },
    { value: 0,   suffix: "%", label: "Cancellation rate" },
    { value: 24,  suffix: "h", label: "Avg. response time" },
  ],

  // --- SEO ------------------------------------------------------------------
  siteUrl: "https://example.com",  // TODO: your final domain (used for SEO tags)
};
