/* =============================================================================
   SPA NAVIGATION — instant page swaps with NO full browser reload.
   -----------------------------------------------------------------------------
   The site is multi-page (index.html, store.html). Navigating between them
   normally triggers a hard browser reload (white flash, scroll reset, the chat
   widget blinks). This intercepts same-origin links between the public pages,
   fetches the target, and swaps ONLY <main> — the persistent shell (header,
   footer, chat widget, cart drawer, modals) stays mounted and keeps its state.
   app.js exposes window.PortfolioApp.mountMain() to (re)render the new content.

   Progressive enhancement: if anything is missing or fails, it falls back to a
   normal navigation, so links always work.
   ========================================================================== */
(function () {
  "use strict";
  if (!window.history || !window.fetch || !window.DOMParser) return;

  var busy = false;

  // Treat "/" and "/index.html" as the same page so Home links and homepage
  // in-page anchors don't trigger a needless swap.
  function norm(pathname) { return (pathname === "/" || pathname === "") ? "/index.html" : pathname; }
  function key(url) { return norm(url.pathname) + url.search; }

  // What's actually rendered. On popstate the URL has already changed, so we
  // compare against this rather than location.
  var current = key(location);

  function resolve(a, e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return null;
    if (!a || (a.target && a.target !== "_self") || a.hasAttribute("download")) return null;
    var raw = a.getAttribute("href") || "";
    if (!raw || raw[0] === "#" || /^(mailto:|tel:|javascript:)/i.test(raw)) return null;
    var url;
    try { url = new URL(a.href, location.href); } catch (err) { return null; }
    if (url.origin !== location.origin) return null;
    var p = url.pathname.toLowerCase();
    // Only the public pages — leave dashboards (/app, /admin), API and files alone.
    if (!(p === "/" || p.endsWith("/index.html") || p.endsWith("/store.html"))) return null;
    return url;
  }

  function scrollToTarget(url) {
    if (url.hash) {
      var t = document.querySelector(url.hash);
      if (t) t.scrollIntoView({ behavior: "auto" });  // instant; missing → leave as-is (app handles #svc-)
      return;
    }
    window.scrollTo(0, 0);
  }

  function paint(doc, url) {
    var newMain = doc.querySelector("#main");
    var curMain = document.querySelector("#main");
    if (!newMain || !curMain || !(window.PortfolioApp && window.PortfolioApp.mountMain)) {
      location.href = url.href;            // can't enhance → real navigation
      return;
    }
    document.title = doc.title;
    curMain.replaceWith(newMain);          // swap ONLY the content; shell stays put
    current = key(url);
    window.PortfolioApp.mountMain();       // re-render the new <main> (no reload)
    scrollToTarget(url);
  }

  function navigate(href, push) {
    var url;
    try { url = new URL(href, location.href); } catch (e) { location.href = href; return; }
    // Already on this page → just move to the hash / top, no swap.
    if (key(url) === current) {
      if (push) history.pushState({ spa: 1 }, "", url.href);
      if (url.hash) { var el = document.querySelector(url.hash); if (el) el.scrollIntoView({ behavior: "smooth" }); }
      else window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (busy) return;
    busy = true;
    fetch(url.href, { headers: { "X-Requested-With": "spa" }, credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error("bad status"); return r.text(); })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        if (push) history.pushState({ spa: 1 }, "", url.href);
        var run = function () { paint(doc, url); };
        if (document.startViewTransition) document.startViewTransition(run); else run();
      })
      .catch(function () { location.href = url.href; })  // fallback: real navigation
      .then(function () { busy = false; });
  }

  // Delegated click handler — bound to document once, survives <main> swaps.
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var url = resolve(a, e);
    if (!url) return;
    e.preventDefault();
    navigate(url.href, true);
  });

  window.addEventListener("popstate", function () { navigate(location.href, false); });

  // Allow programmatic in-app navigation (e.g. service teaser "View packages").
  window.SPA = { navigate: function (href) { navigate(href, true); } };
})();
