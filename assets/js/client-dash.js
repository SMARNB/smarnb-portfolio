/* =============================================================================
   CLIENT DASHBOARD — login/register + my projects with live progress.
   ========================================================================== */
(function () {
  "use strict";
  var C = window.SITE_CONFIG || {};
  function qs(s, p) { return (p || document).querySelector(s); }
  function qsa(s, p) { return Array.prototype.slice.call((p || document).querySelectorAll(s)); }
  function esc(s) { var d = document.createElement("div"); d.textContent = (s == null ? "" : String(s)); return d.innerHTML; }
  function money(n) { return (C.currency || "$") + Number(n || 0).toLocaleString(); }
  function fmtDate(iso) { if (!iso) return ""; try { return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); } catch (e) { return iso; } }

  var SVG = {
    check: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    plus: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
    box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    sun: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>',
    moon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg>',
  };

  var STAGES = [["received", "Received"], ["confirmed", "Confirmed"], ["in_progress", "In Progress"], ["in_review", "In Review"], ["delivered", "Delivered"]];
  function stageIndex(st) { for (var i = 0; i < STAGES.length; i++) { if (STAGES[i][0] === st) return i; } return 0; }

  var view = qs("#view"), pollTimer = null;
  var payCfg = { stripe_enabled: false };
  function loadPayConfig() { return API.get("/api/payments/config").then(function (c) { if (c) payCfg = c; }).catch(function () {}); }

  function payPanelHtml(o) {
    var pi = C.paymentInstructions || {};
    var methods = (pi.methods || []).map(function (m) {
      return '<div class="pay-method' + (m.soon ? " soon" : "") + '"><div><b>' + esc(m.label) + '</b><div class="pm-val">' + esc(m.value) + "</div>" +
        (m.sub ? '<small>' + esc(m.sub) + "</small>" : "") + "</div></div>";
    }).join("");
    var stripeBtn = payCfg.stripe_enabled
      ? '<button class="btn btn-primary btn-block" data-stripe="' + esc(o.public_id) + '">💳 Pay ' + money(o.total) + ' with card</button><div class="pay-or">or pay manually</div>'
      : "";
    return '<div class="pay-panel hidden" id="pay-' + esc(o.public_id) + '">' +
      stripeBtn +
      '<div class="pay-methods">' + methods + "</div>" +
      (pi.note ? '<p class="form-note" style="margin-top:.6rem">' + esc(pi.note) + "</p>" : "") +
      '<div class="dash-status" id="paystat-' + esc(o.public_id) + '"></div></div>';
  }

  /* theme */
  (function () {
    var btn = qs("#themeToggle"), saved = null;
    try { saved = localStorage.getItem("alira_theme"); } catch (e) {}
    var theme = saved || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    function apply(t) { document.documentElement.setAttribute("data-theme", t); if (btn) btn.innerHTML = (t === "dark" ? SVG.sun : SVG.moon); }
    apply(theme);
    if (btn) btn.addEventListener("click", function () { theme = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark"; apply(theme); try { localStorage.setItem("alira_theme", theme); } catch (e) {} });
  })();

  function topbar(user) {
    var who = qs("#who"), out = qs("#logoutBtn");
    if (user) { who.hidden = false; who.innerHTML = "<b>" + esc(user.name || user.email) + "</b><small>" + esc(user.email) + "</small>"; out.hidden = false; }
    else { who.hidden = true; out.hidden = true; }
  }
  qs("#logoutBtn").addEventListener("click", function () { API.logout(); stopPoll(); topbar(null); renderAuth("login"); });
  function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }
  function showStatus(el, type, msg) { el.textContent = msg; el.className = "dash-status show " + type; }

  /* ---- AUTH ---- */
  function renderAuth(mode) {
    mode = mode || "login";
    topbar(null);
    var reg = mode === "register";
    view.innerHTML =
      '<div class="auth-wrap"><div class="card auth-card">' +
        "<h1>" + (reg ? "Create your account" : "Welcome back") + "</h1>" +
        '<p class="lead">Track your projects, watch live progress, and place new orders.</p>' +
        '<div class="seg" role="tablist">' +
          '<button id="tab-login" aria-selected="' + (!reg) + '">Log in</button>' +
          '<button id="tab-register" aria-selected="' + reg + '">Sign up</button>' +
        "</div>" +
        '<form class="form" id="authForm" novalidate>' +
          (reg ? '<div class="field"><label for="f-name">Name</label><input class="input" id="f-name" name="name" autocomplete="name"></div>' : "") +
          '<div class="field"><label for="f-email">Email</label><input class="input" id="f-email" name="email" type="email" autocomplete="email" required></div>' +
          '<div class="field"><label for="f-pass">Password</label><input class="input" id="f-pass" name="password" type="password" autocomplete="' + (reg ? "new-password" : "current-password") + '" required minlength="6"></div>' +
          (reg ? '<div class="field"><label for="f-wa">WhatsApp <span style="color:var(--muted);font-weight:400">(optional)</span></label><input class="input" id="f-wa" name="whatsapp" autocomplete="tel"></div>' : "") +
          '<div class="dash-status" id="auth-status" role="alert"></div>' +
          '<button class="btn btn-primary btn-block" type="submit">' + (reg ? "Create account" : "Log in") + "</button>" +
        "</form>" +
        '<p class="auth-foot">' + (reg ? "Already have an account? " : "New here? ") + '<a href="#" id="swap" style="color:var(--accent-2);font-weight:600">' + (reg ? "Log in" : "Create an account") + "</a></p>" +
        '<p class="auth-foot"><a href="index.html" style="color:var(--muted)">← Back to site</a></p>' +
      "</div></div>";
    qs("#tab-login").addEventListener("click", function () { renderAuth("login"); });
    qs("#tab-register").addEventListener("click", function () { renderAuth("register"); });
    qs("#swap").addEventListener("click", function (e) { e.preventDefault(); renderAuth(reg ? "login" : "register"); });
    qs("#authForm").addEventListener("submit", function (e) {
      e.preventDefault();
      var f = e.target, status = qs("#auth-status");
      var email = f.email.value.trim(), pass = f.password.value;
      if (!email || pass.length < 6) { showStatus(status, "err", "Enter your email and a password (6+ characters)."); return; }
      var btn = qs('button[type="submit"]', f); btn.disabled = true; showStatus(status, "ok", "Please wait…");
      var p = reg
        ? API.register({ email: email, password: pass, name: f.name ? f.name.value.trim() : "", whatsapp: f.whatsapp ? f.whatsapp.value.trim() : "" })
        : API.login({ email: email, password: pass });
      p.then(function (res) { topbar(res.user); renderDashboard(); })
       .catch(function (err) { showStatus(status, "err", err.message || "Something went wrong."); btn.disabled = false; });
    });
  }

  /* ---- DASHBOARD ---- */
  function renderDashboard() {
    topbar(API.getUser());
    view.innerHTML =
      '<div class="dash-head"><div><h1>My Projects</h1><p>Live status &amp; progress on everything you\'ve ordered.</p></div>' +
      '<div style="display:flex;gap:.5rem;flex-wrap:wrap"><button class="btn btn-ghost btn-sm" id="refreshBtn">' + SVG.refresh + " Refresh</button>" +
      '<a class="btn btn-primary btn-sm" href="index.html#pricing">' + SVG.plus + " New order</a></div></div>" +
      '<div id="projects" class="projects"><p class="form-note">Loading…</p></div>';
    qs("#refreshBtn").addEventListener("click", loadProjects);
    loadProjects();
    stopPoll(); pollTimer = setInterval(loadProjects, 25000);
  }

  function loadProjects() {
    API.get("/api/orders/mine").then(renderProjects).catch(function (err) {
      if (err.status === 401) { API.logout(); renderAuth("login"); return; }
      var box = qs("#projects"); if (box) box.innerHTML = '<div class="form-status err show">Couldn\'t load your projects. ' + esc(err.message || "") + "</div>";
    });
  }

  function renderProjects(orders) {
    var box = qs("#projects"); if (!box) return;
    if (!orders || !orders.length) {
      box.innerHTML = '<div class="card empty-card"><div style="width:54px;height:54px;margin:0 auto 1rem">' + SVG.box + "</div><h3>No projects yet</h3><p>Once you place an order it'll appear here with live progress.</p><a class=\"btn btn-primary mt-4\" href=\"index.html#pricing\">Browse services</a></div>";
      return;
    }
    box.innerHTML = orders.map(projectCard).join("");
    qsa("[data-toggle]", box).forEach(function (b) { b.addEventListener("click", function () { var t = qs("#tl-" + CSS.escape(b.dataset.toggle)); if (t) t.classList.toggle("hidden"); }); });
    qsa("[data-cancel]", box).forEach(function (b) { b.addEventListener("click", function () { cancelOrder(b.dataset.cancel); }); });
    qsa("[data-pay]", box).forEach(function (b) { b.addEventListener("click", function () { var p = qs("#pay-" + CSS.escape(b.dataset.pay)); if (p) p.classList.toggle("hidden"); }); });
    qsa("[data-stripe]", box).forEach(function (b) { b.addEventListener("click", function () { startStripe(b.dataset.stripe); }); });
  }

  function startStripe(pid) {
    var st = qs("#paystat-" + CSS.escape(pid));
    if (st) showStatus(st, "ok", "Opening secure checkout…");
    API.post("/api/payments/stripe/checkout/" + encodeURIComponent(pid)).then(function (r) {
      if (r && r.url) { window.location.href = r.url; }
      else if (st) showStatus(st, "err", "Could not start checkout.");
    }).catch(function (err) { if (st) showStatus(st, "err", err.message || "Card payments aren't enabled yet."); });
  }

  function deliverablesHtml(dels) {
    if (!dels || !dels.length) return "";
    return '<div class="deliverables"><h4 class="dlv-h">Your files</h4>' + dels.map(function (d) {
      return '<div class="dlv"><div class="dlv-main"><b>' + esc(d.title || "Deliverable") + "</b>" +
        (d.note ? "<small>" + esc(d.note) + "</small>" : "") + '</div><div class="dlv-actions">' +
        (d.preview_url ? '<a class="btn btn-outline btn-sm" href="' + esc(d.preview_url) + '" target="_blank" rel="noopener">Preview</a>' : "") +
        (d.locked
          ? '<span class="dlv-lock">🔒 Unlocks after payment</span>'
          : (d.final_url ? '<a class="btn btn-primary btn-sm" href="' + esc(d.final_url) + '" target="_blank" rel="noopener">Download</a>' : "")) +
        "</div></div>";
    }).join("") + "</div>";
  }

  function milestonesHtml(o) {
    var ms = o.milestones || [];
    if (!ms.length || o.status === "cancelled") return "";
    var firstOpen = true;
    var rows = ms.map(function (m) {
      var current = !m.done && firstOpen; if (current) firstOpen = false;
      var dot = m.done ? '<span class="tk-dot done">' + SVG.check + "</span>"
        : (current ? '<span class="tk-dot current"></span>' : '<span class="tk-dot"></span>');
      return '<div class="tk-step' + (m.done ? " done" : "") + (current ? " current" : "") + '">' + dot +
        '<span class="tk-label">' + esc(m.title) + (current ? ' <small>· in progress</small>' : "") + "</span></div>";
    }).join("");
    var next = o.next_step ? '<div class="tk-next">Next up: <b>' + esc(o.next_step) + "</b></div>"
      : '<div class="tk-next done">✓ All steps complete</div>';
    return '<div class="tracker">' + rows + next + "</div>";
  }

  function projectCard(o) {
    var idx = stageIndex(o.status);
    var prog = (typeof o.progress === "number") ? o.progress : Math.round(idx / (STAGES.length - 1) * 100);
    var items = (o.items || []).map(function (i) { return esc(i.service) + " (" + esc(i.tier) + (i.qty > 1 ? " ×" + i.qty : "") + ")"; }).join(", ");
    var cancellable = (o.status === "received" || o.status === "confirmed");
    var unpaid = (o.payment_status !== "paid" && o.status !== "cancelled");
    var updates = (o.updates || []).slice().reverse();
    return '<article class="card proj-card">' +
      '<div class="proj-top"><span class="oid">' + esc(o.public_id) + "</span>" +
        '<span class="status-chip st-' + esc(o.status) + '">' + esc(o.status_label || o.status) + "</span></div>" +
      '<div class="items">' + items + " · <b>" + money(o.total) + "</b></div>" +
      '<div class="progress-row"><div class="progress"><span style="width:' + prog + '%"></span></div><span class="pct">' + prog + "%</span></div>" +
      milestonesHtml(o) +
      '<div class="meta-row">' +
        (o.due_date ? "<span>Due: <b>" + esc(o.due_date) + "</b></span>" : "") +
        (o.payment_method ? "<span>Payment: <b>" + esc(o.payment_method) + "</b> (" + esc(o.payment_status || "unpaid") + ")</span>" : "") +
        "<span>Ordered: <b>" + esc(fmtDate(o.created_at)) + "</b></span>" +
      "</div>" +
      (updates.length ? ('<button class="timeline-toggle" data-toggle="' + esc(o.public_id) + '">' + SVG.check + " View updates (" + updates.length + ")</button>" +
        '<div class="mini-timeline hidden" id="tl-' + esc(o.public_id) + '">' + updates.map(function (u) { return '<div class="mt-item"><span class="mt-dot"></span><div><p>' + esc(u.message) + "</p><small>" + esc(fmtDate(u.created_at)) + "</small></div></div>"; }).join("") + "</div>") : "") +
      deliverablesHtml(o.deliverables) +
      (unpaid
        ? '<div class="pay-row"><button class="btn btn-primary btn-sm" data-pay="' + esc(o.public_id) + '">Pay now · ' + money(o.total) + "</button>" +
          (cancellable ? '<button class="btn btn-outline btn-sm" data-cancel="' + esc(o.public_id) + '">Cancel order</button>' : "") + "</div>" + payPanelHtml(o)
        : (cancellable ? '<div style="margin-top:1rem"><button class="btn btn-outline btn-sm" data-cancel="' + esc(o.public_id) + '">Cancel order</button></div>' : "")) +
      (o.payment_status === "paid" ? '<div class="paid-badge">✓ Paid — thank you!</div>' : "") +
      "</article>";
  }

  function cancelOrder(pid) {
    if (!window.confirm("Cancel order " + pid + "? This can't be undone.")) return;
    API.post("/api/orders/" + encodeURIComponent(pid) + "/cancel").then(loadProjects).catch(function (err) { window.alert(err.message || "Could not cancel."); });
  }

  function maybeThankPaid() {
    var m = /[?&]paid=([^&]+)/.exec(location.search || ""); if (!m) return;
    try { window.history.replaceState({}, "", location.pathname); } catch (e) {}
    var v = qs("#view"); if (!v) return;
    var d = document.createElement("div"); d.className = "form-status ok show"; d.style.marginBottom = "1rem";
    d.textContent = "Payment received — thank you! Your order will update to Paid shortly.";
    v.insertBefore(d, v.firstChild);
  }

  /* ---- boot ---- */
  if (API.isAuthed()) {
    Promise.all([API.me(), loadPayConfig()])
      .then(function (res) { API.setUser(res[0]); renderDashboard(); maybeThankPaid(); })
      .catch(function () { API.logout(); renderAuth("login"); });
  } else {
    loadPayConfig();
    renderAuth("login");
  }
})();
