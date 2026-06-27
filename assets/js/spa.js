/* =============================================================================
   SPA NAVIGATION — instant page swaps with NO full browser reload.
   -----------------------------------------------------------------------------
   The site is multi-page (index.html, store.html) but navigating between them
   normally triggers a hard browser reload (white flash, scroll reset). This
   intercepts same-origin links between the public pages, fetches the target,
   swaps <body>, and re-runs the page scripts so the app re-initialises against
   the new DOM — like an SPA, but keeping real URLs and separate HTML files.

   Progressive enhancement: if anything fails (or fetch/history unsupported),
   it falls back to a normal navigation, so links always work.
   ========================================================================== */
(function () {
  "use strict";
  if (!window.history || !window.fetch || !window.DOMParser) return;

  // Page scripts that must re-run on each navigation (DOM-dependent or globals).
  // spa.js itself is deliberately excluded so this stays a single instance.
  var PAGE_SCRIPT = /assets\/js\/(config|data|store|app|chat)\.js/;
  var busy = false;

  // Treat "/" and "/index.html" as the same page so Home links and in-page
  // anchors on the homepage don't trigger a needless swap.
  function norm(pathname) {
    return (pathname === "/" || pathname === "") ? "/index.html" : pathname;
  }
  function key(url) { return norm(url.pathname) + url.search; }

  // Track what's actually rendered. On popstate the URL has already changed, so
  // we can't compare against location — we compare against this instead.
  var current = key(location);

  function isPageScript(src) { return PAGE_SCRIPT.test(src || ""); }

  // Decide whether a click should be handled as an in-app navigation.
  function resolve(a, e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return null;
    if (!a || (a.target && a.target !== "_self") || a.hasAttribute("download")) return null;
    var raw = a.getAttribute("href") || "";
    if (!raw || raw[0] === "#" || /^(mailto:|tel:|javascript:)/i.test(raw)) return null; // anchors/protocols
    var url;
    try { url = new URL(a.href, location.href); } catch (err) { return null; }
    if (url.origin !== location.origin) return null;                 // external
    var p = url.pathname.toLowerCase();
    // Only the public pages — leave dashboards (/app, /admin), API and files alone.
    if (!(p === "/" || p.endsWith("/index.html") || p.endsWith("/store.html"))) return null;
    return url;
  }

  function pageScriptSrcs(doc) {
    var out = [];
    Array.prototype.forEach.call(doc.querySelectorAll("script[src]"), function (s) {
      var src = s.getAttribute("src");
      if (isPageScript(src)) out.push(src);
    });
    return out;
  }

  // Remove the live document's page scripts, then load the new ones in order so
  // they execute fresh (config → data → store → app → chat).
  function rerunScripts(srcs, done) {
    Array.prototype.forEach.call(document.querySelectorAll("script[src]"), function (s) {
      if (isPageScript(s.getAttribute("src")) || isPageScript(s.src)) {
        if (s.parentNode) s.parentNode.removeChild(s);
      }
    });
    (function next(i) {
      if (i >= srcs.length) { if (done) done(); return; }
      var el = document.createElement("script");
      el.src = srcs[i];
      el.onload = el.onerror = function () { next(i + 1); };
      document.body.appendChild(el);
    })(0);
  }

  function scrollToTarget(url) {
    // Instant (not smooth) — a fresh page landing shouldn't animate a long scroll.
    if (url.hash) {
      var t = document.querySelector(url.hash);
      if (t) { t.scrollIntoView({ behavior: "auto" }); return; }
    }
    window.scrollTo(0, 0);
  }

  function paint(doc, url) {
    document.title = doc.title;
    document.body.innerHTML = doc.body.innerHTML;
    current = key(url);                            // remember what's now rendered
    if (!url.hash) window.scrollTo(0, 0);          // instant top for plain page loads
    // Re-run the page scripts, then land on the target AFTER the app has rendered
    // (dynamic sections above the anchor change the offset otherwise).
    rerunScripts(pageScriptSrcs(doc), function () { scrollToTarget(url); });
  }

  function navigate(href, push) {
    var url;
    try { url = new URL(href, location.href); } catch (e) { location.href = href; return; }
    // Same page already rendered → just move to the hash / top, no swap needed.
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
        if (document.startViewTransition) document.startViewTransition(run);
        else run();
      })
      .catch(function () { location.href = url.href; })  // fallback: real navigation
      .then(function () { busy = false; });
  }

  // Delegated click handler survives body swaps (bound to document, once).
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var url = resolve(a, e);
    if (!url) return;
    e.preventDefault();
    navigate(url.href, true);
  });

  // Back/forward → swap without a reload.
  window.addEventListener("popstate", function () {
    navigate(location.href, false);
  });

  // Let other scripts trigger an in-app navigation (e.g. programmatic redirects).
  window.SPA = { navigate: function (href) { navigate(href, true); } };
})();
