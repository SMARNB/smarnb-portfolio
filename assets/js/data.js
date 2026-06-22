/* =============================================================================
   SITE DATA  —  ✏️ edit your services, packages, portfolio & reviews here
   -----------------------------------------------------------------------------
   Everything below renders into the page automatically.
   Prices are placeholders based on your Fiverr gigs — adjust to taste.
   ========================================================================== */

window.SITE_DATA = {

  /* --------------------------------------------------------------------------
     SERVICES  (matches your four Fiverr gigs + a custom option)
     icon = a key from the ICONS map in app.js
  -------------------------------------------------------------------------- */
  services: [
    {
      id: "saas-dashboard",
      icon: "code",
      category: "Development",
      title: "Full-Stack SaaS Dashboards in Python",
      short:
        "Production-ready dashboards & SaaS apps — auth, billing, APIs, charts, " +
        "admin panels. Built to scale.",
      tags: ["Python", "FastAPI / Django", "PostgreSQL", "React", "Stripe", "Docker"],
      deliverables: [
        "Responsive dashboard UI",
        "Secure auth & roles",
        "REST/GraphQL APIs",
        "Database design",
        "Deployment-ready code",
      ],
      packages: [
        {
          tier: "Starter", price: 150, delivery: "5 days", revisions: 1,
          summary: "A focused single-page dashboard.",
          features: ["1 dashboard page", "Up to 4 charts/widgets", "Mock or 1 data source", "Responsive layout", "Source code"],
        },
        {
          tier: "Standard", price: 450, delivery: "10 days", revisions: 3, popular: true,
          summary: "A multi-page app with real data.",
          features: ["Up to 5 pages", "Auth & user roles", "REST API + database", "Charts & tables", "Basic admin panel", "Source code + docs"],
        },
        {
          tier: "Premium", price: 1200, delivery: "21 days", revisions: 5,
          summary: "A full SaaS, ready to launch.",
          features: ["Full SaaS app", "Auth + billing (Stripe)", "Admin + analytics", "API + integrations", "Dockerized deployment", "30-day support"],
        },
      ],
    },
    {
      id: "figma-uiux",
      icon: "pen",
      category: "Design",
      title: "Figma UI/UX for SaaS & Admin Dashboards",
      short:
        "Clean, conversion-focused interfaces — design systems, prototypes, and " +
        "pixel-perfect handoff for SaaS & admin tools.",
      tags: ["Figma", "Design System", "Prototyping", "Wireframes", "Dark/Light"],
      deliverables: [
        "Editable Figma file",
        "Design system & components",
        "Interactive prototype",
        "Developer handoff",
        "Light & dark variants",
      ],
      packages: [
        {
          tier: "Starter", price: 90, delivery: "3 days", revisions: 2,
          summary: "One key screen, polished.",
          features: ["1 dashboard screen", "Desktop layout", "Editable Figma file", "1 color theme"],
        },
        {
          tier: "Standard", price: 250, delivery: "6 days", revisions: 3, popular: true,
          summary: "A complete dashboard flow.",
          features: ["Up to 6 screens", "Components & styles", "Responsive (desktop+mobile)", "Clickable prototype", "Light & dark"],
        },
        {
          tier: "Premium", price: 600, delivery: "12 days", revisions: 5,
          summary: "A full product design system.",
          features: ["Up to 15 screens", "Full design system", "Prototype + micro-interactions", "Dev handoff specs", "Brand & icon set"],
        },
      ],
    },
    {
      id: "selenium-bots",
      icon: "bot",
      category: "Automation",
      title: "Selenium Bots for OCR & Data Scraping",
      short:
        "Automate the boring stuff — web scraping, form filling, OCR data " +
        "extraction, and scheduled bots that just work.",
      tags: ["Selenium", "Python", "OCR", "BeautifulSoup", "Pandas", "Scheduling"],
      deliverables: [
        "Custom automation script",
        "Clean exported data (CSV/Excel/JSON)",
        "OCR text extraction",
        "Anti-block handling",
        "Setup instructions",
      ],
      packages: [
        {
          tier: "Starter", price: 80, delivery: "3 days", revisions: 1,
          summary: "A simple single-site scraper.",
          features: ["1 website / source", "Up to 10 fields", "CSV or Excel export", "Basic error handling"],
        },
        {
          tier: "Standard", price: 200, delivery: "6 days", revisions: 3, popular: true,
          summary: "Multi-page bot with OCR.",
          features: ["Up to 3 sources", "Pagination & login", "OCR data extraction", "CSV/Excel/JSON export", "Setup guide"],
        },
        {
          tier: "Premium", price: 500, delivery: "12 days", revisions: 5,
          summary: "Scheduled, robust pipeline.",
          features: ["Multiple sources", "Scheduled/automated runs", "Proxy & anti-block", "Database storage", "Dashboard or report", "30-day support"],
        },
      ],
    },
    {
      id: "packaging-design",
      icon: "box",
      category: "Packaging",
      title: "Premium Commercial Product Packaging",
      short:
        "Shelf-ready packaging that sells — boxes, labels, pouches, and 3D " +
        "mockups with print-ready dielines.",
      tags: ["Packaging", "Dieline", "3D Mockup", "Print-Ready", "Branding"],
      deliverables: [
        "Print-ready files",
        "Accurate dieline",
        "Photorealistic 3D mockup",
        "Source files",
        "Brand-aligned artwork",
      ],
      packages: [
        {
          tier: "Starter", price: 60, delivery: "3 days", revisions: 2,
          summary: "One label or simple box.",
          features: ["1 packaging design", "Print-ready PDF", "1 mockup", "Standard dieline"],
        },
        {
          tier: "Standard", price: 150, delivery: "5 days", revisions: 3, popular: true,
          summary: "Full packaging with 3D mockup.",
          features: ["1 product, all panels", "Custom dieline", "2 photorealistic mockups", "Source files", "Print-ready files"],
        },
        {
          tier: "Premium", price: 350, delivery: "8 days", revisions: 5,
          summary: "A product-line system.",
          features: ["Up to 3 products", "Packaging system", "4 mockups", "Brand guidelines", "All source + print files"],
        },
      ],
    },
  ],

  /* --------------------------------------------------------------------------
     PORTFOLIO  (replace with your real projects + images in /assets/img)
     image = "" uses an auto-generated gradient thumbnail (no asset needed)
  -------------------------------------------------------------------------- */
  portfolio: [
    { id: "p1", category: "Development", title: "Analytics SaaS Dashboard", desc: "A real-time metrics dashboard with billing & multi-tenant auth.", tags: ["React", "FastAPI", "Stripe"], image: "" },
    { id: "p2", category: "Design",      title: "Fintech Admin UI Kit",     desc: "A 40-screen Figma system for a fintech operations console.",     tags: ["Figma", "Design System"], image: "" },
    { id: "p3", category: "Automation",  title: "Invoice OCR Pipeline",     desc: "Bot that scrapes portals and extracts invoice data via OCR.",     tags: ["Selenium", "OCR", "Pandas"], image: "" },
    { id: "p4", category: "Packaging",   title: "Organic Tea Box Range",    desc: "Premium retail packaging line with print-ready dielines.",       tags: ["Packaging", "3D Mockup"], image: "" },
    { id: "p5", category: "Development",  title: "Inventory Control Panel",  desc: "Internal tool with role-based access and live stock charts.",     tags: ["Django", "PostgreSQL"], image: "" },
    { id: "p6", category: "Design",      title: "Crypto Wallet Dashboard",  desc: "Dark-mode trading dashboard with interactive prototype.",         tags: ["Figma", "Prototype"], image: "" },
    { id: "p7", category: "Automation",  title: "Lead-Gen Scraper Suite",   desc: "Scheduled multi-source scraper feeding a CRM, anti-block.",       tags: ["Selenium", "Proxies"], image: "" },
    { id: "p8", category: "Packaging",   title: "Skincare Pouch Series",    desc: "Cosmetic pouch designs with photorealistic mockups.",            tags: ["Packaging", "Branding"], image: "" },
  ],

  /* --------------------------------------------------------------------------
     PROCESS
  -------------------------------------------------------------------------- */
  process: [
    { icon: "chat",     title: "Discovery",  desc: "We talk through your goals, scope, and timeline — free, no pressure." },
    { icon: "doc",      title: "Proposal",   desc: "You get a clear quote, milestones, and exactly what you'll receive." },
    { icon: "code",     title: "Build",      desc: "I do the work with regular updates so you're never in the dark." },
    { icon: "check",    title: "Review",     desc: "We refine together with the revisions included in your package." },
    { icon: "rocket",   title: "Delivery",   desc: "You get final files, source, and support — delivered on time." },
  ],

  /* --------------------------------------------------------------------------
     WHY ME
  -------------------------------------------------------------------------- */
  perks: [
    { icon: "clock",  title: "On-time, every time",  desc: "99% on-time delivery with clear milestones." },
    { icon: "shield", title: "NDA-friendly",         desc: "Your idea is safe. Happy to sign an NDA." },
    { icon: "code",   title: "You own everything",   desc: "Full source files and rights handed over." },
    { icon: "chat",   title: "Clear communication",  desc: "Regular updates, no jargon, no ghosting." },
  ],

  /* --------------------------------------------------------------------------
     SKILLS  (proficiency bars in About)
  -------------------------------------------------------------------------- */
  skills: [
    { name: "Python / Backend",     level: 95 },
    { name: "Selenium / Automation",level: 92 },
    { name: "React / Frontend",     level: 88 },
    { name: "Figma / UI-UX",        level: 90 },
    { name: "Packaging / Print",    level: 85 },
    { name: "Databases & APIs",     level: 90 },
  ],

  /* --------------------------------------------------------------------------
     TESTIMONIALS  (replace with your real Fiverr reviews)
  -------------------------------------------------------------------------- */
  testimonials: [
    { name: "Omar Al-Rashid", role: "SaaS Founder",      loc: "Dubai, UAE 🇦🇪",        rating: 5, text: "Delivered a full dashboard ahead of schedule. Clean code, clear communication. Already hired again." },
    { name: "Mei Ling Tan",   role: "Product Manager",   loc: "Singapore 🇸🇬",          rating: 5, text: "The Figma UI was exactly what we needed — pixel perfect and easy for our devs to build from." },
    { name: "Lukas Berger",   role: "E-commerce Owner",  loc: "Berlin, Germany 🇩🇪",    rating: 5, text: "The scraping bot saves us hours every day. Reliable, well documented, and it just works." },
    { name: "Ayesha Khan",    role: "Brand Manager",     loc: "Karachi, Pakistan 🇵🇰",  rating: 5, text: "Our packaging looks premium on the shelf. The 3D mockups helped us pitch to retailers." },
    { name: "David Cohen",    role: "Startup CTO",       loc: "Austin, USA 🇺🇸",        rating: 5, text: "Took a vague idea and turned it into a working product. Professional from start to finish." },
    { name: "Sofia Romano",   role: "Marketing Lead",    loc: "Milan, Italy 🇮🇹",       rating: 5, text: "Automation pipeline runs flawlessly on schedule. Highly recommend for any data work." },
  ],

  /* --------------------------------------------------------------------------
     FAQ
  -------------------------------------------------------------------------- */
  faq: [
    { q: "How do I start a project?", a: "Pick a package and click Order to add it to your cart, then check out — your request comes straight to me. For anything custom, use the Custom Request form or message me on WhatsApp." },
    { q: "What happens after I place an order?", a: "You'll get an order ID you can use to track status here on the site, and I'll confirm details with you by email or WhatsApp before starting. Payment is arranged on confirmation (Fiverr, invoice, or direct)." },
    { q: "Can you handle custom or larger projects?", a: "Absolutely. Most of my work is custom. Send me your scope through the Custom Request form and I'll reply with a tailored quote and timeline." },
    { q: "Do I get the source files?", a: "Yes — every package includes full source/working files and the rights to use them. You own what you pay for." },
    { q: "How many revisions are included?", a: "Each package lists its included revisions. Need more? We can always add them — I want you happy with the result." },
    { q: "What are your payment terms?", a: "Flexible. I work through Fiverr, direct invoice, or a simple milestone split for larger projects. We'll agree on terms before any work begins." },
  ],

  /* --------------------------------------------------------------------------
     PERSONAL PROJECTS  (CodeWatch featured — ✏️ add your own below)
  -------------------------------------------------------------------------- */
  personalProjects: [
    {
      id: "codewatch",
      featured: true,
      title: "CodeWatch",
      subtitle: "AI Surveillance & Face-Liveness System",
      role: "Full-Stack & Computer Vision Engineer",
      period: "Final Year Project",
      desc:
        "An AI-powered passive surveillance platform. Real-time face recognition " +
        "(InsightFace) is gated by a MiniFASNet anti-spoofing liveness check, so a " +
        "printed photo, phone screen, or video replay can't fool a known identity. " +
        "Adds YOLO person detection, dress-code compliance, movement tracking, " +
        "blacklist & visitor management, violation logging and analytics.",
      highlights: [
        "RGB presentation-attack-detection gate — blocks photo/screen/replay spoofs at ~3.6 ms/face (TorchScript-fused)",
        "Multi-frame liveness voting with once-per-track caching and fail-open for distant faces",
        "Modular CV engine: detection, recognition, tracking, dedup, dress-code & reports",
        "Django REST API backend + React frontend over a live multi-camera pipeline",
      ],
      tags: ["Python", "PyTorch", "InsightFace", "YOLO", "OpenCV", "Django REST", "React"],
      link: "https://github.com/SMARNB/CodeWatch",
      linkLabel: "View on GitHub",
      category: "AI / Computer Vision",
    },
    // ✏️ Add more of your own projects here (copy the shape below):
    {
      id: "automation-suite",
      title: "Automation & Scraping Toolkit",
      subtitle: "Reusable Selenium + OCR pipelines",
      role: "Creator",
      period: "Open source",
      desc:
        "A personal collection of battle-tested Selenium spiders and OCR extractors " +
        "I reuse across client jobs — login & pagination handling, proxy rotation, " +
        "and clean CSV/Excel/JSON exports.",
      highlights: [
        "Anti-block patterns: rotating proxies, human-like delays",
        "OCR extraction for scanned PDFs & images",
        "Pluggable exporters and scheduled runs",
      ],
      tags: ["Python", "Selenium", "OCR", "Pandas"],
      link: "https://github.com/SMARNB",
      linkLabel: "More on GitHub",
      category: "Automation",
    },
  ],

  /* --------------------------------------------------------------------------
     EXPERIENCE / TIMELINE  (✏️ adjust dates, roles & education to match yours)
  -------------------------------------------------------------------------- */
  experience: [
    {
      role: "Freelance Full-Stack Developer & Designer",
      org: "Fiverr · Self-employed",
      period: "2023 — Present",
      desc:
        "Delivering Python SaaS dashboards, Selenium/OCR automation, Figma UI/UX and " +
        "premium product packaging for clients worldwide — on time, production-ready.",
      tags: ["Python", "React", "Selenium", "Figma"],
      current: true,
    },
    {
      role: "CodeWatch — AI Surveillance System",
      org: "Final Year Project",
      period: "2025",
      desc:
        "Designed and built an end-to-end computer-vision platform: face recognition with " +
        "anti-spoofing liveness detection, person & dress-code detection, and a Django + React stack.",
      tags: ["PyTorch", "Computer Vision", "Django"],
    },
    {
      role: "BS Computer Science",
      org: "University",          // ✏️ replace with your university name
      period: "2021 — 2025",       // ✏️ adjust
      desc:
        "Focused on software engineering, machine learning and computer vision. " +
        "Built multiple full-stack and automation projects alongside the degree.",
      tags: ["Algorithms", "Machine Learning", "Databases"],
    },
  ],
};
