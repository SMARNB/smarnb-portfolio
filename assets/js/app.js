/* =============================================================================
   APP  —  rendering, interactions, animations, sales flow, a11y
   ========================================================================== */
(function () {
  "use strict";

  var C = window.SITE_CONFIG, D = window.SITE_DATA, S = window.Store;

  /* ---- tiny helpers ------------------------------------------------------ */
  function qs(s, p) { return (p || document).querySelector(s); }
  function qsa(s, p) { return Array.prototype.slice.call((p || document).querySelectorAll(s)); }
  function money(n) { return C.currency + Number(n).toLocaleString(); }
  function on(el, ev, fn) { if (el) el.addEventListener(ev, fn); }
  function esc(s) { var d = document.createElement("div"); d.textContent = (s == null ? "" : String(s)); return d.innerHTML; }
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var mobileMenuClose = null; // set by initMobileMenu; used by the fit-based nav

  /* ---- icon set (inline SVG, currentColor) ------------------------------- */
  var P = {
    code: '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    pen: '<path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/>',
    bot: '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="8" cy="16" r="1.4"/><circle cx="16" cy="16" r="1.4"/><path d="M12 7v4M12 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM2 14h1M21 14h1"/>',
    box: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
    chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    doc: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/>',
    check: '<polyline points="20 6 9 17 4 12"/>',
    rocket: '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>',
    clock: '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>',
    arrow: '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
    cart: '<circle cx="9" cy="21" r="1.5"/><circle cx="19" cy="21" r="1.5"/><path d="M2.5 3H5l2.7 13.4a1.5 1.5 0 0 0 1.5 1.2h9.7a1.5 1.5 0 0 0 1.5-1.2L22 7H6"/>',
    close: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    menu: '<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>',
    sun: '<circle cx="12" cy="12" r="4.5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/>',
    moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
    star: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    minus: '<line x1="5" y1="12" x2="19" y2="12"/>',
    mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="2.5 6 12 13 21.5 6"/>',
    whatsapp: '<path fill="currentColor" stroke="none" d="M20 11.9a8 8 0 0 1-11.9 7L3 20l1.2-4.9A8 8 0 1 1 20 11.9zM12 5.6a6.3 6.3 0 0 0-5.4 9.6l-.7 2.6 2.7-.7A6.3 6.3 0 1 0 12 5.6zm3.7 8c-.2.5-1 1-1.4 1-.4.1-.8.1-1.3-.1-.3-.1-.7-.2-1.2-.5a6.7 6.7 0 0 1-2.5-2.6c-.2-.3-.6-.9-.6-1.6 0-.7.4-1.1.5-1.2.2-.2.4-.2.5-.2h.4c.1 0 .3 0 .5.4l.5 1.2c0 .1.1.2 0 .4l-.3.4-.2.2c-.1.1-.2.2 0 .4.2.4.6.9 1 1.2.6.5 1 .6 1.2.7.1 0 .3 0 .4-.1l.5-.6c.2-.2.3-.1.5-.1l1.2.6c.2.1.3.2.4.2.1.2.1.5-.1.9z"/>',
    chevron: '<polyline points="6 9 12 15 18 9"/>',
    trash: '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    spark: '<path d="M12 2l2.4 6.5L21 11l-6.6 2.5L12 20l-2.4-6.5L3 11l6.6-2.5z"/>',
    eye: '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/>',
    server: '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><line x1="7" y1="7.5" x2="7.01" y2="7.5"/><line x1="7" y1="16.5" x2="7.01" y2="16.5"/>',
    layout: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>',
    card: '<rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>',
    top: '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    cartBig: '<circle cx="9" cy="21" r="1.5"/><circle cx="19" cy="21" r="1.5"/><path d="M2.5 3H5l2.7 13.4a1.5 1.5 0 0 0 1.5 1.2h9.7a1.5 1.5 0 0 0 1.5-1.2L22 7H6"/>',
    github: '<path fill="currentColor" stroke="none" d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.36 1.09 2.94.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.6 9.6 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2z"/>',
    linkedin: '<path fill="currentColor" stroke="none" d="M4.98 3.5A2.5 2.5 0 1 1 5 8.5a2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05 4 0 4.75 2.65 4.75 6.1V21H17.6v-5.4c0-1.3 0-2.95-1.8-2.95s-2.05 1.4-2.05 2.85V21H9z"/>',
    dribbble: '<circle cx="12" cy="12" r="9.5"/><path d="M5 7c4 4 9 5 14 4M3 12.5c5-1 10 0 13 4M9 3c3 4 5 9 5 18"/>',
    instagram: '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor" stroke="none"/>',
    facebook: '<path fill="currentColor" stroke="none" d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.4h-1.2c-1.2 0-1.6.8-1.6 1.5V12h2.7l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/>',
    x: '<path fill="currentColor" stroke="none" d="M18.9 2H22l-7.1 8.1L23.3 22h-6.6l-5.2-6.8L5.5 22H2.4l7.6-8.7L1.1 2h6.8l4.6 6.2L18.9 2zm-1.2 18h1.8L7.1 3.9H5.2L17.7 20z"/>',
  };
  function icon(name, attrs) {
    var inner = P[name] || "";
    var filled = ["star", "whatsapp", "github", "linkedin", "instagram", "facebook", "x"].indexOf(name) !== -1;
    var base = filled
      ? 'fill="currentColor" stroke="none"'
      : 'fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"';
    return '<svg viewBox="0 0 24 24" width="24" height="24" ' + base + ' ' + (attrs || "") + ' aria-hidden="true">' + inner + "</svg>";
  }

  var CAT_GRAD = {
    Development: "linear-gradient(135deg,#7c5cff,#22d3ee)",
    Design: "linear-gradient(135deg,#f472b6,#7c5cff)",
    Automation: "linear-gradient(135deg,#22d3ee,#34d399)",
    Packaging: "linear-gradient(135deg,#fbbf24,#f472b6)",
  };
  var CAT_ICON = { Development: "code", Design: "pen", Automation: "bot", Packaging: "box" };

  /* =========================================================================
     1. CONTENT FROM CONFIG
  ========================================================================= */
  function fillConfig() {
    qsa("[data-name]").forEach(function (e) { e.textContent = C.name; });
    qsa("[data-brand]").forEach(function (e) { e.textContent = C.brand; });
    qsa("[data-initials]").forEach(function (e) { e.textContent = C.initials; });
    qsa("[data-role]").forEach(function (e) { e.textContent = C.role; });
    qsa("[data-tagline]").forEach(function (e) { e.textContent = C.tagline; });
    qsa("[data-bio]").forEach(function (e) { e.textContent = C.bio; });
    qsa("[data-location]").forEach(function (e) { e.textContent = C.location; });
    qsa("[data-availability]").forEach(function (e) { e.textContent = C.availability; });
    qsa("[data-year]").forEach(function (e) { e.textContent = new Date().getFullYear(); });

    // contact links
    qsa("[data-email-link]").forEach(function (e) { e.href = "mailto:" + C.email; });
    qsa("[data-email-text]").forEach(function (e) { e.textContent = C.email; });
    var wa = (C.whatsapp || "").replace(/\D/g, "");
    qsa("[data-wa-link]").forEach(function (e) { e.href = "https://wa.me/" + wa; });
    qsa("[data-wa-text]").forEach(function (e) { e.textContent = "+" + wa; });

    // socials — the icon ALWAYS shows; a filled URL makes it clickable, an empty
    // one stays as a dimmed placeholder (so you can see what's wired up).
    var smap = { instagram: "instagram", facebook: "facebook", linkedin: "linkedin", x: "x", github: "github" };
    Object.keys(smap).forEach(function (k) {
      qsa('[data-social="' + k + '"]').forEach(function (a) {
        a.innerHTML = icon(smap[k]);
        var url = C.socials && C.socials[k];
        if (url) {
          a.href = url; a.target = "_blank"; a.rel = "noopener";
          a.removeAttribute("aria-disabled"); a.classList.remove("social-empty");
        } else {
          a.removeAttribute("href");
          a.setAttribute("aria-disabled", "true");
          a.classList.add("social-empty");
          a.title = "Add your " + k + " link in assets/js/config.js → socials";
        }
      });
    });

    // profile photo (About + anywhere with [data-photo])
    qsa("[data-photo]").forEach(function (img) {
      if (C.photo) { img.src = C.photo; img.alt = C.name; }
      else { img.remove(); }
    });
    if (C.photo) qsa("[data-photo-note]").forEach(function (n) { n.remove(); });
  }

  /* =========================================================================
     2. RENDERERS
  ========================================================================= */
  function renderServices() {
    var grid = qs("#servicesGrid"); if (!grid) return;
    grid.innerHTML = D.services.map(function (s, i) {
      var min = Math.min.apply(null, s.packages.map(function (p) { return p.price; }));
      return '<article class="card service-card reveal" style="--d:' + (i * 80) + 'ms">' +
        '<div class="from">from <b>' + money(min) + '</b></div>' +
        '<div class="ic">' + icon(s.icon) + "</div>" +
        "<h3>" + esc(s.title) + "</h3>" +
        "<p>" + esc(s.short) + "</p>" +
        '<div class="tag-row">' + s.tags.slice(0, 4).map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") + "</div>" +
        '<button class="card-link js-view-packages" data-service="' + s.id + '">View packages ' + icon("arrow") + "</button>" +
        "</article>";
    }).join("");
    qsa(".js-view-packages", grid).forEach(function (b) {
      on(b, "click", function () { selectService(b.dataset.service, true); });
    });
    observeReveal(grid); // re-arm the reveal animation for freshly-rendered cards
  }

  function renderPriceTabs() {
    var tabs = qs("#priceTabs"); if (!tabs) return;
    tabs.innerHTML = D.services.map(function (s, i) {
      return '<button class="price-tab" role="tab" id="tab-' + s.id + '" aria-controls="priceGrid" aria-selected="' + (i === 0) + '" data-service="' + s.id + '">' + esc(shortTitle(s.title)) + "</button>";
    }).join("");
    qsa(".price-tab", tabs).forEach(function (b) {
      on(b, "click", function () { selectService(b.dataset.service, false); });
    });
  }
  function shortTitle(t) {
    return t.replace(/ in Python$/, "").replace(/^Full-Stack /, "").replace(/ for SaaS & Admin Dashboards/, "").replace(/ for OCR & Data Scraping/, "").replace(/^Premium Commercial /, "");
  }

  function renderPricing(serviceId) {
    var grid = qs("#priceGrid"); if (!grid) return;
    var s = D.services.find(function (x) { return x.id === serviceId; }) || D.services[0];
    grid.innerHTML = s.packages.map(function (p) {
      return '<article class="card price-card reveal' + (p.popular ? " popular" : "") + '">' +
        (p.popular ? '<span class="badge-pop">Most popular</span>' : "") +
        '<div class="tier">' + esc(p.tier) + "</div>" +
        '<div class="amount">' + money(p.price) + " <small>starting</small></div>" +
        '<p class="summary">' + esc(p.summary) + "</p>" +
        '<div class="price-meta"><span>⏱ <b>' + esc(p.delivery) + "</b></span><span>↻ <b>" + p.revisions + "</b> revisions</span></div>" +
        '<ul class="feat-list">' + p.features.map(function (f) { return "<li>" + icon("check") + "<span>" + esc(f) + "</span></li>"; }).join("") + "</ul>" +
        '<button class="btn ' + (p.popular ? "btn-primary" : "btn-outline") + ' btn-block js-order" ' +
        'data-service="' + s.id + '" data-tier="' + esc(p.tier) + '" data-price="' + p.price + '" data-delivery="' + esc(p.delivery) + '" data-title="' + esc(s.title) + '">' +
        icon("cart") + " Order " + esc(p.tier) + "</button>" +
        "</article>";
    }).join("");
    qsa(".js-order", grid).forEach(function (b) {
      on(b, "click", function () {
        S.addItem({ serviceId: b.dataset.service, service: b.dataset.title, tier: b.dataset.tier, price: +b.dataset.price, delivery: b.dataset.delivery });
        toast(icon("check"), b.dataset.tier + " package added to cart");
        openPanel(cartDrawer);
      });
    });
    observeReveal(grid);
  }

  function selectService(id, scroll) {
    qsa(".price-tab").forEach(function (t) { t.setAttribute("aria-selected", String(t.dataset.service === id)); });
    renderPricing(id);
    if (scroll) { var el = qs("#pricing"); if (el) el.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" }); }
  }

  function renderPortfolio(filter) {
    var grid = qs("#workGrid"); if (!grid) return;
    var items = (filter && filter !== "All") ? D.portfolio.filter(function (p) { return p.category === filter; }) : D.portfolio;
    grid.innerHTML = items.map(function (p, i) {
      var thumb = p.image
        ? '<img class="ph" src="' + esc(p.image) + '" alt="' + esc(p.title) + '" loading="lazy" width="600" height="375">'
        : '<span class="ph" style="background:' + CAT_GRAD[p.category] + '"></span>' + icon(CAT_ICON[p.category], 'class="cat-ic"');
      return '<article class="card work-card reveal" style="--d:' + (i * 60) + 'ms" data-id="' + p.id + '" tabindex="0" role="button" aria-label="View ' + esc(p.title) + '">' +
        '<div class="work-thumb">' + thumb + '<span class="hover-go">' + icon("arrow") + "</span></div>" +
        '<div class="work-body"><span class="cat">' + esc(p.category) + "</span><h3>" + esc(p.title) + "</h3><p>" + esc(p.desc) + "</p>" +
        '<div class="tag-row">' + p.tags.map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") + "</div></div>" +
        "</article>";
    }).join("");
    qsa(".work-card", grid).forEach(function (card) {
      function open() { openProject(card.dataset.id); }
      on(card, "click", open);
      on(card, "keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    });
    observeReveal(grid);
  }

  function renderFilters() {
    var row = qs("#workFilters"); if (!row) return;
    var cats = ["All"].concat(D.portfolio.map(function (p) { return p.category; }).filter(function (v, i, a) { return a.indexOf(v) === i; }));
    row.innerHTML = cats.map(function (c, i) {
      return '<button class="filter-btn' + (i === 0 ? " active" : "") + '" data-filter="' + c + '">' + esc(c) + "</button>";
    }).join("");
    qsa(".filter-btn", row).forEach(function (b) {
      on(b, "click", function () {
        qsa(".filter-btn", row).forEach(function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        renderPortfolio(b.dataset.filter);
      });
    });
  }

  function renderProcess() {
    var el = qs("#processSteps"); if (!el) return;
    el.innerHTML = D.process.map(function (s, i) {
      return '<div class="step reveal" style="--d:' + (i * 80) + 'ms"><span class="num">' + (i + 1) + '</span><div class="ic">' + icon(s.icon) + "</div><h3>" + esc(s.title) + "</h3><p>" + esc(s.desc) + "</p></div>";
    }).join("");
  }

  function renderPerks() {
    var el = qs("#perksGrid"); if (!el) return;
    el.innerHTML = D.perks.map(function (p, i) {
      return '<div class="perk reveal" style="--d:' + (i * 70) + 'ms"><div class="ic">' + icon(p.icon) + "</div><div><h3>" + esc(p.title) + "</h3><p>" + esc(p.desc) + "</p></div></div>";
    }).join("");
  }

  function renderSkills() {
    var el = qs("#skillsList"); if (!el) return;
    el.innerHTML = D.skills.map(function (s) {
      return '<div class="skill"><div class="skill-head"><span>' + esc(s.name) + "</span><span>" + s.level + '%</span></div><div class="skill-bar"><span class="skill-fill" data-level="' + s.level + '"></span></div></div>';
    }).join("");
  }

  function renderTestimonials() {
    var el = qs("#testimonialsGrid"); if (!el) return;
    el.innerHTML = D.testimonials.map(function (t, i) {
      var stars = ""; for (var k = 0; k < t.rating; k++) stars += icon("star");
      var initials = t.name.split(" ").map(function (w) { return w[0]; }).join("").slice(0, 2);
      var sub = esc(t.role) + (t.loc ? " · " + esc(t.loc) : "");
      return '<article class="card tcard reveal" style="--d:' + (i * 60) + 'ms"><div class="stars">' + stars + "</div><p>“" + esc(t.text) + '”</p><div class="tperson"><span class="av">' + esc(initials) + "</span><span><b>" + esc(t.name) + "</b><small>" + sub + "</small></span></div></article>";
    }).join("");
    observeReveal(el); // re-arm reveal for cards rendered after the async fetch
  }

  function renderFAQ() {
    var el = qs("#faqList"); if (!el) return;
    el.innerHTML = D.faq.map(function (f, i) {
      return '<div class="faq-item"><button class="faq-q" aria-expanded="false" aria-controls="faq-a-' + i + '"><span>' + esc(f.q) + "</span>" + icon("chevron", 'class="chev"') + '</button><div class="faq-a" id="faq-a-' + i + '" role="region"><div><p>' + esc(f.a) + "</p></div></div></div>";
    }).join("");
    qsa(".faq-item", el).forEach(function (item) {
      var q = qs(".faq-q", item);
      on(q, "click", function () {
        var open = item.classList.toggle("open");
        q.setAttribute("aria-expanded", String(open));
      });
    });
  }

  function renderMarquee() {
    var el = qs("#marqueeTrack"); if (!el) return;
    var tech = ["Python", "FastAPI", "Django", "React", "Selenium", "OCR", "Figma", "PostgreSQL", "Docker", "Stripe", "Pandas", "UI/UX", "Packaging", "3D Mockups"];
    var row = tech.map(function (t) { return "<span>" + icon("spark", 'style="display:inline;width:14px;height:14px;vertical-align:-2px;color:var(--accent-2)"') + " " + esc(t) + "</span>"; }).join("");
    el.innerHTML = row + row; // duplicate for seamless loop
  }

  function renderFooterServices() {
    var el = qs("#footerServices"); if (!el) return;
    el.innerHTML = D.services.map(function (s) {
      return '<li><a href="#pricing" data-service="' + s.id + '" class="js-foot-service">' + esc(shortTitle(s.title)) + "</a></li>";
    }).join("");
    qsa(".js-foot-service", el).forEach(function (a) {
      on(a, "click", function (e) { e.preventDefault(); selectService(a.dataset.service, true); });
    });
  }

  function renderPayments() {
    var el = qs("#paymentsGrid"); if (!el) return;
    var groups = {};
    (C.payments || []).forEach(function (p) { (groups[p.group] = groups[p.group] || []).push(p); });
    el.className = "pay-groups";
    el.innerHTML = Object.keys(groups).map(function (g) {
      return '<div class="pay-group"><h4>' + esc(g) + "</h4>" +
        groups[g].map(function (p) { return '<div class="pay-chip">' + icon("card") + "<span>" + esc(p.label) + "</span></div>"; }).join("") +
        "</div>";
    }).join("");
  }

  function applyServices() {
    renderServices();
    renderPriceTabs();
    var active = qs('.price-tab[aria-selected="true"]');
    renderPricing(active ? active.dataset.service : D.services[0].id);
    fillServiceSelect();
    buildHeroStats();
    animateCounters(); // re-run so "Services offered" reflects the new total
  }

  function mapDbService(s) {
    return {
      id: s.slug, icon: s.icon || "spark", category: s.category || "Development",
      title: s.title, short: s.short || "", tags: s.tags || [],
      deliverables: s.deliverables || [], packages: s.packages || [],
    };
  }

  // Pull the catalog from the backend. Once the developer has imported the
  // built-ins ("managed"), the DB is authoritative (so hiding/deleting works).
  // Before that, DB services are merged onto the built-ins (DB overrides by id).
  function fetchAndMergeServices() {
    fetch((C.apiBase || "") + "/api/services", { headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error("no api"); return r.json(); })
      .then(function (res) {
        var list = (res && res.services) || (Array.isArray(res) ? res : []);
        if (!Array.isArray(list)) return;
        if (res && res.managed) {
          if (!list.length) return;            // safety: never blank the page
          D.services = list.map(mapDbService);
          applyServices();
          return;
        }
        if (!list.length) return;
        var idx = {}; D.services.forEach(function (s, i) { idx[s.id] = i; });
        var changed = false;
        list.forEach(function (s) {
          var mapped = mapDbService(s);
          if (idx[s.slug] != null) { D.services[idx[s.slug]] = mapped; }
          else { D.services.push(mapped); }
          changed = true;
        });
        if (changed) applyServices();
      })
      .catch(function () { /* offline / static-only → keep data.js services */ });
  }

  // Pull approved client reviews and show them ahead of the sample ones.
  function fetchTestimonials() {
    fetch((C.apiBase || "") + "/api/testimonials", { headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error("no api"); return r.json(); })
      .then(function (list) {
        if (!Array.isArray(list) || !list.length) return;
        var real = list.map(function (t) {
          return { name: t.name, role: t.role || "Client", loc: t.location || "", rating: t.rating || 5, text: t.text };
        });
        D.testimonials = real.concat(D.testimonials);
        renderTestimonials();
      })
      .catch(function () { /* offline / static-only → keep sample reviews */ });
  }

  function initReviewForm() {
    var form = qs("#reviewForm"); if (!form) return;
    var status = qs("#rv-status");
    function setStatus(type, msg) { if (status) { status.textContent = msg; status.className = "form-status show " + type; } }
    // star rating widget
    var ratingInput = qs("#rv-rating");
    qsa(".star-pick button", form).forEach(function (b) {
      on(b, "click", function () {
        var v = b.dataset.v; if (ratingInput) ratingInput.value = v;
        qsa(".star-pick button", form).forEach(function (x) { x.classList.toggle("on", Number(x.dataset.v) <= Number(v)); });
        b.setAttribute("aria-checked", "true");
      });
    });
    on(form, "submit", function (e) {
      e.preventDefault();
      if (form.company && form.company.value) return; // honeypot
      var payload = {
        name: (form.name.value || "").trim(),
        role: (form.role.value || "").trim(),
        location: (form.location.value || "").trim(),
        rating: parseInt(ratingInput && ratingInput.value, 10) || 5,
        text: (form.text.value || "").trim(),
        company: "",
      };
      if (payload.name.length < 2 || payload.text.length < 10) { setStatus("err", "Please add your name and a few words."); return; }
      var btn = qs("button[type=submit]", form); if (btn) btn.disabled = true;
      setStatus("", "Sending…");
      fetch((C.apiBase || "") + "/api/testimonials", {
        method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (!res.ok) throw new Error((res.d && res.d.detail) || "Could not submit.");
          setStatus("ok", res.d.message || "Thank you! Your review will appear once approved.");
          form.reset(); if (ratingInput) ratingInput.value = "5";
          qsa(".star-pick button", form).forEach(function (x) { x.classList.add("on"); });
        })
        .catch(function (err) { setStatus("err", err.message || "Could not submit — is the backend running?"); })
        .then(function () { if (btn) btn.disabled = false; });
    });
  }

  function fillServiceSelect() {
    var sel = qs("#cf-service"); if (!sel) return;
    sel.innerHTML = '<option value="">Select a service…</option>' +
      D.services.map(function (s) { return '<option>' + esc(shortTitle(s.title)) + "</option>"; }).join("") +
      '<option>Custom / Something else</option>';
  }

  /* =========================================================================
     3. OVERLAY / PANEL MANAGER (drawer + modals) with a11y
  ========================================================================= */
  var overlay = qs("#overlay");
  var cartDrawer = qs("#cartDrawer");
  var checkoutModal = qs("#checkoutModal");
  var trackModal = qs("#trackModal");
  var projectModal = qs("#projectModal");
  var stack = [];
  var lastFocus = null;
  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex]:not([tabindex="-1"])';

  function openPanel(panel) {
    if (!panel || stack.indexOf(panel) !== -1) return;
    if (!stack.length) { lastFocus = document.activeElement; document.body.style.overflow = "hidden"; }
    stack.push(panel);
    overlay.classList.add("open");
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    var first = qs(FOCUSABLE, panel);
    if (first) setTimeout(function () { first.focus(); }, 60);
  }
  function closePanel(panel) {
    panel = panel || stack[stack.length - 1];
    if (!panel) return;
    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
    stack = stack.filter(function (p) { return p !== panel; });
    if (!stack.length) {
      overlay.classList.remove("open");
      document.body.style.overflow = "";
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
  }
  on(overlay, "click", function () { closePanel(); });
  qsa("[data-close]").forEach(function (b) { on(b, "click", function () { closePanel(); }); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && stack.length) closePanel();
    if (e.key === "Tab" && stack.length) trapTab(e);
  });
  function trapTab(e) {
    var panel = stack[stack.length - 1];
    var f = qsa(FOCUSABLE, panel).filter(function (el) { return el.offsetParent !== null; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  /* =========================================================================
     4. CART
  ========================================================================= */
  function renderCart() {
    var body = qs("#cartBody"), foot = qs("#cartFoot"), count = S.cartCount();
    qsa("[data-cart-count]").forEach(function (b) {
      b.textContent = count; b.classList.toggle("show", count > 0);
    });
    var cart = S.getCart();
    if (!cart.length) {
      body.innerHTML = '<div class="empty-state">' + icon("cartBig") + "<p>Your cart is empty.</p><p style=\"font-size:.85rem\">Browse the packages and add a service to get started.</p></div>";
      foot.hidden = true;
      return;
    }
    foot.hidden = false;
    body.innerHTML = cart.map(function (i) {
      return '<div class="cart-line"><div><h4>' + esc(i.service) + '</h4><div class="meta">' + esc(i.tier) + " · " + esc(i.delivery) + "</div>" +
        '<div class="qty" style="margin-top:.6rem"><button data-dec="' + i.key + '" aria-label="Decrease quantity">' + icon("minus") + "</button><span>" + i.qty + '</span><button data-inc="' + i.key + '" aria-label="Increase quantity">' + icon("plus") + "</button></div></div>" +
        '<div style="text-align:right;display:flex;flex-direction:column;justify-content:space-between"><span class="price">' + money(i.price * i.qty) + '</span><button class="remove" data-rm="' + i.key + '">Remove</button></div></div>';
    }).join("");
    foot.innerHTML = '<div class="cart-foot-row"><span>Subtotal</span><span class="total">' + money(S.cartTotal()) + "</span></div>" +
      '<p class="form-note">Final price confirmed before any payment. No charge until you approve.</p>' +
      '<button class="btn btn-primary btn-block" id="checkoutBtn">' + icon("arrow") + " Checkout</button>" +
      '<button class="btn btn-ghost btn-block" data-close>Keep browsing</button>';

    qsa("[data-inc]", body).forEach(function (b) { on(b, "click", function () { var c = S.getCart().find(function (x) { return x.key === b.dataset.inc; }); S.setQty(b.dataset.inc, c.qty + 1); }); });
    qsa("[data-dec]", body).forEach(function (b) { on(b, "click", function () { var c = S.getCart().find(function (x) { return x.key === b.dataset.dec; }); S.setQty(b.dataset.dec, c.qty - 1); }); });
    qsa("[data-rm]", body).forEach(function (b) { on(b, "click", function () { S.removeItem(b.dataset.rm); }); });
    on(qs("#checkoutBtn"), "click", openCheckout);
    qsa("[data-close]", foot).forEach(function (b) { on(b, "click", function () { closePanel(); }); });
  }

  /* =========================================================================
     5. CHECKOUT
  ========================================================================= */
  function paymentOptions() {
    var groups = {};
    (C.payments || []).forEach(function (p) { (groups[p.group] = groups[p.group] || []).push(p); });
    var html = '<option value="">Select how you\'d like to pay…</option>';
    Object.keys(groups).forEach(function (g) {
      html += '<optgroup label="' + esc(g) + '">';
      groups[g].forEach(function (p) { html += '<option value="' + esc(p.label) + '">' + esc(p.label) + "</option>"; });
      html += "</optgroup>";
    });
    return html;
  }

  function openCheckout() {
    if (!S.getCart().length) { toast(icon("cart"), "Your cart is empty"); return; }
    var body = qs("#checkoutBody");
    var cart = S.getCart();
    body.innerHTML =
      '<div class="order-summary">' +
        cart.map(function (i) { return '<div class="row"><span>' + esc(i.service) + " · " + esc(i.tier) + " ×" + i.qty + "</span><span>" + money(i.price * i.qty) + "</span></div>"; }).join("") +
        '<div class="row total"><span>Total</span><span>' + money(S.cartTotal()) + "</span></div>" +
      "</div>" +
      '<form class="form" id="checkoutForm" novalidate>' +
        '<div class="two"><div class="field"><label for="co-name">Name <span class="req">*</span></label><input class="input" id="co-name" name="name" required autocomplete="name"></div>' +
        '<div class="field"><label for="co-email">Email <span class="req">*</span></label><input class="input" id="co-email" name="email" type="email" required autocomplete="email"></div></div>' +
        '<div class="field"><label for="co-wa">WhatsApp <span style="color:var(--muted);font-weight:400">(optional)</span></label><input class="input" id="co-wa" name="whatsapp" autocomplete="tel"></div>' +
        '<div class="field"><label for="co-notes">Project details</label><textarea class="textarea" id="co-notes" name="notes" placeholder="Anything I should know — links, references, deadlines…"></textarea></div>' +
        '<div class="field"><label for="co-pay">Preferred payment method</label><select class="select" id="co-pay" name="payment">' + paymentOptions() + "</select></div>" +
        '<input class="hp" tabindex="-1" autocomplete="off" name="_gotcha" aria-hidden="true">' +
        '<div class="form-status" id="co-status" role="alert"></div>' +
        '<button class="btn btn-primary btn-block" type="submit">' + icon("check") + " Place order</button>" +
        '<p class="form-note">By placing this order you\'re sending me a request — I\'ll confirm the details and payment with you before starting. No payment is taken on this site.</p>' +
      "</form>";
    qs("#checkoutTitle").textContent = "Checkout";
    openPanel(checkoutModal);
    on(qs("#checkoutForm"), "submit", submitCheckout);
  }

  function submitCheckout(e) {
    e.preventDefault();
    var f = e.target, status = qs("#co-status");
    if (f._gotcha.value) return; // honeypot tripped (bot)
    // NB: a control named "name" is shadowed by HTMLFormElement.name — use .elements
    var name = f.elements["name"].value.trim(), email = f.email.value.trim();
    if (!name || !validEmail(email)) { showStatus(status, "err", "Please add your name and a valid email."); return; }
    var customer = {
      name: name, email: email, whatsapp: f.whatsapp.value.trim(),
      notes: f.notes.value.trim(), payment_method: f.payment.value,
    };
    var btn = qs('button[type="submit"]', f);
    if (btn) btn.disabled = true;
    showStatus(status, "ok", "Placing your order…");
    // Try the backend first (so it lands in your dashboard); fall back to local + Formspree.
    S.placeOrderViaApi(customer)
      .then(function (order) { showOrderSuccess(order); })
      .catch(function () { showOrderSuccess(S.placeOrder(customer)); })
      .then(function () { if (btn) btn.disabled = false; });
  }

  function showOrderSuccess(order) {
    var body = qs("#checkoutBody");
    qs("#checkoutTitle").textContent = "Order received";
    var waLink = S.whatsappLink(S.orderSummaryText(order));
    var emailNote = C.formspreeId
      ? "A copy has been emailed to me — I'll reply soon."
      : "Tap below to send me the order on WhatsApp so I can confirm.";
    body.innerHTML =
      '<div style="text-align:center">' +
        '<div class="success-icon">' + icon("check") + "</div>" +
        "<h3>Thank you!</h3>" +
        '<p class="lead" style="margin:.5rem auto 0">Your order request is in. ' + esc(emailNote) + "</p>" +
        '<div class="order-id-box"><small>Your order ID — save it to track</small><div class="id">' + esc(order.id) + "</div></div>" +
        (order.payment_method ? '<p class="form-note" style="margin:.2rem auto 0">Payment via <b>' + esc(order.payment_method) + "</b> — I'll send you the details to complete it.</p>" : "") +
      "</div>" +
      '<a class="btn btn-primary btn-block" href="' + esc(waLink) + '" target="_blank" rel="noopener">' + icon("whatsapp") + " Confirm on WhatsApp</a>" +
      '<button class="btn btn-ghost btn-block mt-2" id="goTrack">' + icon("doc") + " Track this order</button>" +
      '<button class="btn btn-outline btn-block mt-2" data-close>Done</button>';
    renderCart();
    on(qs("#goTrack"), "click", function () { closePanel(checkoutModal); openTrack(order.id); });
    qsa("[data-close]", body).forEach(function (b) { on(b, "click", function () { closePanel(); }); });
  }

  /* =========================================================================
     6. ORDER TRACKING
  ========================================================================= */
  var STAGES = [
    { key: "Received", note: "Order received." },
    { key: "Confirmed", note: "Details confirmed & started." },
    { key: "In Progress", note: "Work is underway." },
    { key: "In Review", note: "Ready for your review." },
    { key: "Delivered", note: "Final files delivered." },
  ];

  function openTrack(prefillId) {
    openPanel(trackModal);
    if (prefillId) { qs("#trackInput").value = prefillId; doTrack(); }
    else renderRecentOrders();
  }

  function renderRecentOrders() {
    var box = qs("#trackResult");
    var orders = S.getOrders();
    if (!orders.length) { box.innerHTML = '<p class="form-note">No orders found in this browser yet. Place an order and it\'ll appear here.</p>'; return; }
    box.innerHTML = '<h4 style="margin-bottom:.6rem">Your recent orders</h4><div class="recent-orders">' +
      orders.slice(0, 6).map(function (o) {
        return '<div class="recent-order" data-id="' + o.id + '" tabindex="0" role="button"><span class="oid">' + esc(o.id) + '</span><span class="status-chip">' + esc(o.status) + "</span></div>";
      }).join("") + "</div>";
    qsa(".recent-order", box).forEach(function (r) {
      function go() { qs("#trackInput").value = r.dataset.id; doTrack(); }
      on(r, "click", go);
      on(r, "keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
    });
  }

  function doTrack() {
    var box = qs("#trackResult");
    var id = qs("#trackInput").value.trim();
    if (!id) { renderRecentOrders(); return; }
    id = id.toUpperCase();
    box.innerHTML = '<p class="form-note">Looking up ' + esc(id) + "…</p>";
    fetch((C.apiBase || "") + "/api/orders/" + encodeURIComponent(id), { headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error("nf"); return r.json(); })
      .then(function (server) { renderTrackResult(normalizeServerOrder(server)); })
      .catch(function () {
        var order = S.getOrder(id);
        if (order) renderTrackResult(order);
        else box.innerHTML = '<div class="form-status err show">No order found for “' + esc(id) + '”. Check the ID, or it may have been placed on a different device.</div>';
      });
  }

  function normalizeServerOrder(s) {
    return {
      id: s.public_id,
      items: (s.items || []).map(function (i) { return { service: i.service, tier: i.tier, price: i.price, qty: i.qty }; }),
      total: s.total,
      status: s.status_label || s.status,
      progress: s.progress,
      payment_method: s.payment_method,
      timeline: (s.updates || []).map(function (u) { return { status: u.status, note: u.message, at: u.created_at }; }),
    };
  }

  function fmtDate(iso) {
    if (!iso) return "";
    try { return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); }
    catch (e) { return iso; }
  }

  function renderTrackResult(order) {
    var box = qs("#trackResult");
    var statusStr = String(order.status || "Received");
    var cancelled = statusStr.toLowerCase() === "cancelled";
    var currentIdx = STAGES.findIndex(function (s) { return s.key.toLowerCase() === statusStr.toLowerCase(); });
    if (currentIdx < 0) currentIdx = 0;
    var prog = (typeof order.progress === "number") ? order.progress
      : Math.round(currentIdx / (STAGES.length - 1) * 100);
    var items = (order.items || []).map(function (i) { return esc(i.service) + " (" + esc(i.tier) + ")"; }).join(", ");

    var html = '<div class="order-id-box" style="text-align:left"><small>Order</small>' +
      '<div class="id" style="font-size:1.2rem">' + esc(order.id) + "</div>" +
      '<p class="form-note" style="margin-top:.3rem">' + items + " · " + money(order.total) + "</p></div>";

    if (cancelled) {
      html += '<div class="form-status err show">This order was cancelled.</div>';
    } else {
      html += '<div style="margin:1rem 0 1.2rem"><div style="display:flex;justify-content:space-between;font-size:.82rem;color:var(--muted);margin-bottom:.4rem">' +
        '<span>Progress</span><span style="color:var(--text);font-weight:800">' + prog + '%</span></div>' +
        '<div style="height:10px;border-radius:999px;background:var(--surface-2);overflow:hidden;border:1px solid var(--border)">' +
        '<span style="display:block;height:100%;width:' + prog + '%;background:var(--grad);border-radius:999px"></span></div></div>';
      html += '<div class="timeline">' + STAGES.map(function (s, i) {
        var cls = i < currentIdx ? "done" : (i === currentIdx ? "current done" : "");
        return '<div class="tl-step ' + cls + '"><span class="tl-dot">' + (i <= currentIdx ? icon("check") : "") +
          '</span><div class="tl-body"><b>' + esc(s.key) + "</b><small>" + esc(s.note) + "</small></div></div>";
      }).join("") + "</div>";
    }

    if (order.timeline && order.timeline.length) {
      html += '<div style="margin-top:1rem;padding-top:1rem;border-top:1px solid var(--border)"><b style="font-size:.9rem">Latest updates</b>';
      order.timeline.slice().reverse().slice(0, 6).forEach(function (u) {
        html += '<div style="margin-top:.6rem;font-size:.88rem"><span>' + esc(u.note || "") + "</span>" +
          '<small style="display:block;color:var(--muted-2);font-size:.74rem;margin-top:.1rem">' + esc(fmtDate(u.at)) + "</small></div>";
      });
      html += "</div>";
    }

    html += '<p class="form-note" style="margin-top:1rem">Questions about this order? ' +
      '<a href="' + esc(S.whatsappLink("Hi! About my order " + order.id + "…")) +
      '" target="_blank" rel="noopener" style="color:var(--accent-2);font-weight:600">Message me</a>.</p>';
    box.innerHTML = html;
  }

  /* =========================================================================
     7. PROJECT MODAL
  ========================================================================= */
  function openProject(id) {
    var p = D.portfolio.find(function (x) { return x.id === id; }); if (!p) return;
    var body = qs("#projectBody");
    var thumb = p.image
      ? '<img src="' + esc(p.image) + '" alt="' + esc(p.title) + '" style="border-radius:var(--r);width:100%">'
      : '<div style="height:180px;border-radius:var(--r);background:' + CAT_GRAD[p.category] + ';display:grid;place-items:center">' + icon(CAT_ICON[p.category], 'style="width:54px;height:54px;color:#fff"') + "</div>";
    qs("#projectTitle").textContent = p.title;
    body.innerHTML = thumb +
      '<span class="cat" style="display:inline-block;margin-top:1rem;color:var(--accent-2);font-weight:700;text-transform:uppercase;font-size:.76rem;letter-spacing:.06em">' + esc(p.category) + "</span>" +
      "<h3 style=\"margin:.3rem 0 .5rem\">" + esc(p.title) + "</h3>" +
      "<p class=\"lead\">" + esc(p.desc) + "</p>" +
      '<div class="tag-row" style="margin:1rem 0 1.4rem">' + p.tags.map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") + "</div>" +
      '<button class="btn btn-primary btn-block" id="projCta">' + icon("spark") + " Start a similar project</button>";
    openPanel(projectModal);
    on(qs("#projCta"), "click", function () {
      closePanel(projectModal);
      var sel = qs("#cf-service"); var msg = qs("#cf-message");
      if (sel) { var opt = Array.prototype.find.call(sel.options, function (o) { return o.value && p.category.indexOf(o.value) > -1; }); }
      if (msg) msg.value = "I'm interested in a project similar to “" + p.title + "”. ";
      var el = qs("#contact"); if (el) el.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" });
      setTimeout(function () { var n = qs("#cf-name"); if (n) n.focus(); }, 500);
    });
  }

  /* =========================================================================
     8. CUSTOM REQUEST / CONTACT FORM
  ========================================================================= */
  function initContactForm() {
    var form = qs("#customForm"); if (!form) return;
    on(form, "submit", function (e) {
      e.preventDefault();
      var status = qs("#cf-status");
      if (form._gotcha.value) return; // honeypot tripped (bot)
      var name = form.elements["name"].value.trim(), email = form.email.value.trim(), message = form.message.value.trim();
      if (!name || !validEmail(email) || !message) { showStatus(status, "err", "Please fill in your name, a valid email, and your message."); return; }
      var payload = {
        _subject: "New project inquiry — " + C.brand,
        name: name, email: email, whatsapp: form.whatsapp.value.trim(),
        service: form.service.value, budget: form.budget.value, timeline: form.timeline.value,
        message: message,
        _gotcha: form._gotcha.value, // Formspree server-side honeypot
      };
      var btn = qs('button[type="submit"]', form);
      if (C.formspreeId) {
        btn.disabled = true; showStatus(status, "ok", "Sending…");
        S.sendMessage(payload).then(function () {
          showStatus(status, "ok", "Thanks " + name + "! Your request is on its way — I'll reply by email soon.");
          form.reset();
        }).catch(function () {
          showStatus(status, "err", "Couldn't send right now. Please email or WhatsApp me directly (buttons on the left).");
        }).then(function () { btn.disabled = false; });
      } else {
        // No email endpoint configured → fall back to WhatsApp / mailto
        var text = "New inquiry from " + name + " (" + email + ")\nService: " + payload.service + "\nBudget: " + payload.budget + "\nTimeline: " + payload.timeline + "\n\n" + message;
        showStatus(status, "ok", "Opening WhatsApp to send your message…");
        window.open(S.whatsappLink(text), "_blank", "noopener");
      }
    });
  }

  /* =========================================================================
     9. UTILITIES
  ========================================================================= */
  function validEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }
  function showStatus(el, type, msg) { el.textContent = msg; el.className = "form-status show " + type; }

  var toastWrap = qs("#toasts");
  function toast(iconHtml, msg) {
    var t = document.createElement("div");
    t.className = "toast";
    t.innerHTML = '<span class="ic">' + iconHtml + "</span><span></span>";
    t.lastChild.textContent = msg; // user-safe
    toastWrap.appendChild(t);
    setTimeout(function () { t.classList.add("leaving"); setTimeout(function () { t.remove(); }, 320); }, 2600);
  }

  /* =========================================================================
     10. SCROLL EFFECTS: reveal, counters, skills, header, scrollspy, top
  ========================================================================= */
  var revealObs;
  function observeReveal(scope) {
    if (reduceMotion) { qsa(".reveal", scope).forEach(function (e) { e.classList.add("in"); }); return; }
    if (!revealObs) {
      revealObs = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); revealObs.unobserve(en.target); } });
      }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    }
    qsa(".reveal", scope).forEach(function (e) { if (!e.classList.contains("in")) revealObs.observe(e); });
  }

  function animateCounters() {
    qsa("[data-count]").forEach(function (el) {
      var target = parseFloat(el.dataset.count), suffix = el.dataset.suffix || "", dur = 1400, t0 = null;
      if (reduceMotion) { el.textContent = target + suffix; return; }
      function step(ts) {
        if (!t0) t0 = ts; var p = Math.min((ts - t0) / dur, 1);
        el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + suffix;
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
      setTimeout(function () { el.textContent = target + suffix; }, dur + 250); // safety: ensure final value shows even if rAF is throttled
    });
  }

  function buildHeroStats() {
    var wrap = qs("#heroStats"); if (!wrap) return;
    wrap.innerHTML = C.stats.map(function (s) {
      var val = (s.auto === "services" && D.services) ? D.services.length : s.value;
      return '<div class="stat"><div class="stat-num"><span data-count="' + val + '" data-suffix="' + (s.suffix || "") + '">0</span></div><div class="stat-label">' + esc(s.label) + "</div></div>";
    }).join("");
  }

  function initObservers() {
    observeReveal(document);
    // counters when hero stats visible
    var hs = qs("#heroStats");
    if (hs) {
      var counted = false;
      var runCounters = function () { if (counted) return; counted = true; animateCounters(); };
      var o = new IntersectionObserver(function (en) { if (en[0].isIntersecting) { runCounters(); o.disconnect(); } }, { threshold: 0.2 });
      o.observe(hs);
      var rct = hs.getBoundingClientRect();                 // already visible on load → run now
      if (rct.top < window.innerHeight && rct.bottom > 0) runCounters();
    }
    // skill bars
    var sk = qs("#skillsList");
    if (sk) {
      var so = new IntersectionObserver(function (en) {
        if (en[0].isIntersecting) { qsa(".skill-fill", sk).forEach(function (f) { f.style.width = f.dataset.level + "%"; }); so.disconnect(); }
      }, { threshold: 0.3 });
      so.observe(sk);
    }
    // scrollspy
    var sections = qsa("section[id]");
    var navlinks = qsa(".nav-links a");
    if (sections.length && navlinks.length) {
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            navlinks.forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === "#" + en.target.id); });
          }
        });
      }, { rootMargin: "-45% 0px -50% 0px" });
      sections.forEach(function (s) { spy.observe(s); });
    }
  }

  function initHeader() {
    var header = qs("#header"), toTop = qs("#toTop");
    function onScroll() {
      var y = window.scrollY;
      header.classList.toggle("scrolled", y > 12);
      if (toTop) toTop.classList.toggle("show", y > 600);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    if (toTop) on(toTop, "click", function () { window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" }); });
  }

  /* ---- mobile menu ------------------------------------------------------- */
  function initMobileMenu() {
    var btn = qs("#menuToggle"), menu = qs("#mobileMenu");
    if (!btn || !menu) return;
    function toggle(force) {
      var open = typeof force === "boolean" ? force : !menu.classList.contains("open");
      menu.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", String(open));
      btn.innerHTML = icon(open ? "close" : "menu");
      document.body.style.overflow = open ? "hidden" : "";
    }
    mobileMenuClose = function () { toggle(false); };
    on(btn, "click", function () { toggle(); });
    qsa("a", menu).forEach(function (a) { on(a, "click", function () { toggle(false); }); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") toggle(false); });
  }

  /* ---- fit-based nav: show the inline links only while they actually fit --- */
  function initResponsiveNav() {
    var header = qs("#header"), nav = header && qs(".nav", header);
    if (!header || !nav) return;
    var ticking = false;
    function update() {
      ticking = false;
      header.classList.add("nav-expanded");            // assume the links fit…
      if (nav.scrollWidth > nav.clientWidth + 1) {
        header.classList.remove("nav-expanded");        // …they don't → hamburger
      } else {
        var mm = qs("#mobileMenu");                      // …they do → close stray mobile menu
        if (mobileMenuClose && mm && mm.classList.contains("open")) mobileMenuClose();
      }
    }
    function onResize() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
    window.addEventListener("resize", onResize, { passive: true });
    update();
  }

  /* ---- theme ------------------------------------------------------------- */
  function initTheme() {
    var btn = qs("#themeToggle");
    var saved = null;
    try { saved = localStorage.getItem("alira_theme"); } catch (e) {}
    var theme = saved || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    apply(theme);
    function apply(t) {
      document.documentElement.setAttribute("data-theme", t);
      if (btn) btn.innerHTML = icon(t === "dark" ? "sun" : "moon");
    }
    on(btn, "click", function () {
      theme = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      apply(theme);
      try { localStorage.setItem("alira_theme", theme); } catch (e) {}
    });
  }

  /* ---- smooth anchor scrolling ------------------------------------------ */
  function initAnchors() {
    qsa('a[href^="#"]').forEach(function (a) {
      on(a, "click", function (e) {
        var id = a.getAttribute("href");
        if (id.length < 2) return;
        var target = qs(id);
        if (target) { e.preventDefault(); target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" }); history.replaceState(null, "", id); }
      });
    });
  }

  /* =========================================================================
     PERSONAL PROJECTS + EXPERIENCE
  ========================================================================= */
  function gradFor(cat) { return CAT_GRAD[cat] || "linear-gradient(135deg,#7c5cff,#22d3ee)"; }

  function renderPersonalProjects() {
    var wrap = qs("#projectsGrid"); if (!wrap || !D.personalProjects) return;
    var feat = D.personalProjects.filter(function (p) { return p.featured; });
    var rest = D.personalProjects.filter(function (p) { return !p.featured; });

    var html = feat.map(function (p) {
      return '<article class="card project-feature reveal">' +
        '<div class="pf-visual" style="background:' + gradFor(p.category) + '">' +
          icon("eye", 'class="pf-bigicon"') +
          '<span class="pf-cat">' + esc(p.category) + "</span>" +
          '<span class="pf-name">' + esc(p.title) + "</span>" +
        "</div>" +
        '<div class="pf-body">' +
          '<span class="eyebrow">Featured project</span>' +
          "<h3>" + esc(p.title) + ' <span class="pf-sub">— ' + esc(p.subtitle) + "</span></h3>" +
          '<p class="pf-meta">' + esc(p.role) + " · " + esc(p.period) + "</p>" +
          '<p class="lead">' + esc(p.desc) + "</p>" +
          '<ul class="feat-list">' + p.highlights.map(function (h) { return "<li>" + icon("check") + "<span>" + esc(h) + "</span></li>"; }).join("") + "</ul>" +
          '<div class="tag-row">' + p.tags.map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") + "</div>" +
          '<a class="btn btn-primary mt-4" href="' + esc(p.link) + '" target="_blank" rel="noopener">' + icon("github") + " " + esc(p.linkLabel || "View project") + "</a>" +
        "</div>" +
      "</article>";
    }).join("");

    if (rest.length) {
      html += '<div class="grid cols-2" style="margin-top:1.25rem">' + rest.map(function (p) {
        return '<article class="card reveal">' +
          '<span class="cat" style="color:var(--accent-2);font-weight:700;text-transform:uppercase;font-size:.74rem;letter-spacing:.06em">' + esc(p.category) + "</span>" +
          '<h3 style="font-size:1.15rem;margin:.35rem 0">' + esc(p.title) + "</h3>" +
          '<p style="color:var(--muted);font-size:.93rem">' + esc(p.desc) + "</p>" +
          '<div class="tag-row">' + p.tags.map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") + "</div>" +
          '<a class="card-link" href="' + esc(p.link) + '" target="_blank" rel="noopener">' + esc(p.linkLabel || "View") + " " + icon("arrow") + "</a>" +
        "</article>";
      }).join("") + "</div>";
    }
    wrap.innerHTML = html;
    observeReveal(wrap);
  }

  function renderExperience() {
    var el = qs("#experienceList"); if (!el || !D.experience) return;
    el.innerHTML = D.experience.map(function (x, i) {
      return '<div class="xp-item reveal' + (x.current ? " current" : "") + '" style="--d:' + (i * 80) + 'ms">' +
        '<span class="xp-dot"></span>' +
        '<div class="xp-card">' +
          '<div class="xp-head"><div><h3>' + esc(x.role) + "</h3><p class=\"xp-org\">" + esc(x.org) + "</p></div>" +
          '<span class="xp-period">' + esc(x.period) + "</span></div>" +
          '<p class="xp-desc">' + esc(x.desc) + "</p>" +
          '<div class="tag-row">' + (x.tags || []).map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") + "</div>" +
        "</div>" +
      "</div>";
    }).join("");
    observeReveal(el);
  }

  /* =========================================================================
     INIT
  ========================================================================= */
  function init() {
    if ("scrollRestoration" in history) { try { history.scrollRestoration = "manual"; } catch (e) {} }
    fillConfig();
    buildHeroStats();
    renderServices();
    renderPriceTabs(); renderPricing(D.services[0].id);
    renderFilters(); renderPortfolio("All");
    renderProcess(); renderPerks(); renderSkills();
    renderTestimonials(); renderFAQ(); renderMarquee(); renderFooterServices();
    renderPersonalProjects(); renderExperience(); renderPayments();
    fillServiceSelect();
    fetchAndMergeServices(); // pull any services added from the dashboard
    fetchTestimonials();     // pull approved client reviews from the backend
    initReviewForm();        // "leave a review" submission

    initContactForm();
    renderCart();
    S.onChange(renderCart);

    // open cart / track buttons
    qsa("[data-open-cart]").forEach(function (b) { on(b, "click", function () { openPanel(cartDrawer); }); });
    qsa("[data-open-track]").forEach(function (b) { on(b, "click", function () { openTrack(); }); });
    on(qs("#trackBtn"), "click", doTrack);
    var ti = qs("#trackInput");
    if (ti) on(ti, "keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); doTrack(); } });

    initHeader(); initMobileMenu(); initResponsiveNav(); initTheme(); initAnchors(); initObservers();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
