/* =============================================================================
   DEVELOPER (ADMIN) DASHBOARD — orders, progress, deliverables, services.
   ========================================================================== */
(function () {
  "use strict";
  var C = window.SITE_CONFIG || {};
  function qs(s, p) { return (p || document).querySelector(s); }
  function qsa(s, p) { return Array.prototype.slice.call((p || document).querySelectorAll(s)); }
  function esc(s) { var d = document.createElement("div"); d.textContent = (s == null ? "" : String(s)); return d.innerHTML; }
  function money(n) { return (C.currency || "$") + Number(n || 0).toLocaleString(); }
  function fmtDate(iso) { if (!iso) return ""; try { return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); } catch (e) { return iso; } }
  function csv(s) { return String(s || "").split(",").map(function (x) { return x.trim(); }).filter(Boolean); }

  var SVG = {
    refresh: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
    plus: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    sun: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>',
    moon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg>',
  };
  var STATUSES = [["received", "Received"], ["confirmed", "Confirmed"], ["in_progress", "In Progress"], ["in_review", "In Review"], ["delivered", "Delivered"], ["cancelled", "Cancelled"]];
  var ICON_CHOICES = ["spark", "code", "server", "layout", "bot", "eye", "pen", "box", "rocket", "chat", "doc", "shield", "clock", "card"];

  var view = qs("#view"), pollTimer = null, badgeTimer = null, convTimer = null;
  var state = { orders: [], stats: null, filter: "all", selected: null, tab: "orders",
                services: null, inboxList: null, selectedConv: null, reviews: null };

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
  qs("#logoutBtn").addEventListener("click", function () { API.logout(); stopPoll(); stopBadges(); topbar(null); renderLogin(); });
  function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } if (convTimer) { clearInterval(convTimer); convTimer = null; } }
  function stopBadges() { if (badgeTimer) { clearInterval(badgeTimer); badgeTimer = null; } }

  /* ---- LOGIN ---- */
  function renderLogin(err) {
    topbar(null); stopPoll();
    view.innerHTML =
      '<div class="auth-wrap"><div class="card auth-card"><h1>Developer login</h1>' +
      '<p class="lead">Private area — only the developer account can sign in.</p>' +
      '<form class="form" id="loginForm" novalidate>' +
      '<div class="field"><label for="l-email">Email</label><input class="input" id="l-email" name="email" type="email" required autocomplete="email"></div>' +
      '<div class="field"><label for="l-pass">Password</label><input class="input" id="l-pass" name="password" type="password" required autocomplete="current-password"></div>' +
      '<div class="dash-status ' + (err ? "show err" : "") + '" id="login-status">' + (err ? esc(err) : "") + "</div>" +
      '<button class="btn btn-primary btn-block" type="submit">Log in</button></form>' +
      '<p class="auth-foot"><a href="index.html" style="color:var(--muted)">← Back to site</a></p></div></div>';
    qs("#loginForm").addEventListener("submit", function (e) {
      e.preventDefault();
      var f = e.target, btn = qs("button", f); btn.disabled = true;
      API.login({ email: f.email.value.trim(), password: f.password.value }).then(function (res) {
        if (res.user.role !== "admin") { API.logout(); btn.disabled = false; loginErr("That account isn't an admin."); return; }
        startDashboard();
      }).catch(function (err) { btn.disabled = false; loginErr(err.message || "Login failed."); });
    });
  }
  function loginErr(m) { var s = qs("#login-status"); if (s) { s.textContent = m; s.className = "dash-status show err"; } }

  /* ---- SHELL + TABS ---- */
  function renderShell() {
    topbar(API.getUser());
    view.innerHTML =
      '<div class="dash-head"><div><h1>Developer Dashboard</h1><p>Orders, chat, reviews &amp; services — your private control room.</p></div></div>' +
      '<div class="admin-tabs">' +
        '<button data-tab="orders" class="active">Orders</button>' +
        '<button data-tab="inbox">Inbox <span class="tab-badge" id="inboxBadge" hidden>0</span></button>' +
        '<button data-tab="reviews">Reviews <span class="tab-badge" id="reviewsBadge" hidden>0</span></button>' +
        '<button data-tab="services">Services</button>' +
      '</div>' +
      '<div id="tabBody"></div>';
    qsa(".admin-tabs button").forEach(function (b) { b.addEventListener("click", function () { showTab(b.dataset.tab); }); });
    var initial = { "#services": "services", "#inbox": "inbox", "#reviews": "reviews" }[location.hash] || "orders";
    showTab(initial);
    stopBadges(); pollBadges(); badgeTimer = setInterval(pollBadges, 30000);
  }

  function showTab(tab) {
    state.tab = tab;
    qsa(".admin-tabs button").forEach(function (b) { b.classList.toggle("active", b.dataset.tab === tab); });
    stopPoll();
    if (tab === "orders") { renderOrdersTab(); refresh(); pollTimer = setInterval(refresh, 25000); }
    else if (tab === "inbox") { renderInboxTab(); }
    else if (tab === "reviews") { renderReviewsTab(); }
    else { renderServicesTab(); }
  }

  /* Lightweight badge polling (unread chats + pending reviews) across tabs. */
  function pollBadges() {
    API.get("/api/admin/chat/conversations").then(function (list) {
      var unread = list.reduce(function (n, c) { return n + (c.unread || 0); }, 0);
      var b = qs("#inboxBadge"); if (b) { b.hidden = !unread; b.textContent = unread > 99 ? "99+" : unread; }
      if (state.tab === "inbox" && state.inboxList) { state.inboxList = list; if (!state.selectedConv) renderConvList(); }
    }).catch(function () {});
    API.get("/api/admin/testimonials").then(function (list) {
      var pending = list.filter(function (t) { return t.status === "pending"; }).length;
      var b = qs("#reviewsBadge"); if (b) { b.hidden = !pending; b.textContent = pending; }
    }).catch(function () {});
  }

  /* ---- ORDERS TAB ---- */
  function renderOrdersTab() {
    qs("#tabBody").innerHTML =
      '<div style="display:flex;justify-content:flex-end;margin-bottom:1rem"><button class="btn btn-ghost btn-sm" id="refreshBtn">' + SVG.refresh + " Refresh</button></div>" +
      '<div id="stats" class="stat-grid"></div>' +
      '<div class="filter-chips" id="filters"></div>' +
      '<div class="admin-grid"><div class="order-rows" id="orderRows"></div>' +
      '<div id="manage"><div class="card manage"><div class="empty">Select an order on the left to manage it.</div></div></div></div>';
    qs("#refreshBtn").addEventListener("click", refresh);
  }

  function refresh() {
    if (state.tab !== "orders") return Promise.resolve();
    return Promise.all([API.get("/api/admin/stats"), API.get("/api/admin/orders")]).then(function (res) {
      state.stats = res[0]; state.orders = res[1];
      if (state.tab === "orders" && qs("#stats")) { renderStats(); renderFilters(); renderRows(); }
    }).catch(function (err) {
      if (err.status === 401 || err.status === 403) { API.logout(); renderLogin("Session expired — please log in again."); }
    });
  }

  function renderStats() {
    var s = state.stats || {};
    var cards = [["Total orders", s.total_orders, false], ["Active", s.active_orders, false], ["Delivered", s.delivered_orders, false], ["Revenue (paid)", money(s.revenue), true], ["Clients", s.clients, false]];
    qs("#stats").innerHTML = cards.map(function (c) { return '<div class="card stat-card"><div class="v' + (c[2] ? " grad" : "") + '">' + esc(c[1] == null ? 0 : c[1]) + '</div><div class="k">' + esc(c[0]) + "</div></div>"; }).join("");
  }

  function renderFilters() {
    var counts = (state.stats && state.stats.by_status) || {};
    var chips = [["all", "All"]].concat(STATUSES);
    qs("#filters").innerHTML = chips.map(function (c) {
      var n = c[0] === "all" ? state.orders.length : (counts[c[0]] || 0);
      return '<button data-f="' + c[0] + '" class="' + (state.filter === c[0] ? "active" : "") + '">' + esc(c[1]) + " (" + n + ")</button>";
    }).join("");
    qsa("#filters button").forEach(function (b) { b.addEventListener("click", function () { state.filter = b.dataset.f; renderFilters(); renderRows(); }); });
  }

  function renderRows() {
    var rows = qs("#orderRows");
    var list = state.orders.filter(function (o) { return state.filter === "all" || o.status === state.filter; });
    if (!list.length) { rows.innerHTML = '<p class="form-note">No orders' + (state.filter !== "all" ? " in this status" : " yet") + ".</p>"; return; }
    rows.innerHTML = list.map(function (o) {
      var prog = (typeof o.progress === "number") ? o.progress : 0;
      return '<button class="order-row' + (state.selected === o.public_id ? " active" : "") + '" data-id="' + esc(o.public_id) + '">' +
        '<div class="r1"><span class="oid">' + esc(o.public_id) + '</span><span class="status-chip st-' + esc(o.status) + '">' + esc(o.status_label || o.status) + "</span></div>" +
        '<div class="who">' + esc(o.customer_name || o.customer_email) + " · " + money(o.total) + (o.payment_status === "paid" ? " · paid" : "") + "</div>" +
        '<div class="r2"><div class="progress"><span style="width:' + prog + '%"></span></div><span class="pct" style="font-size:.8rem">' + prog + "%</span></div></button>";
    }).join("");
    qsa("#orderRows .order-row").forEach(function (b) {
      b.addEventListener("click", function () {
        state.selected = b.dataset.id;
        var o = state.orders.filter(function (x) { return x.public_id === b.dataset.id; })[0];
        renderRows(); renderManage(o);
      });
    });
  }

  function renderManage(o) {
    var items = (o.items || []).map(function (i) { return esc(i.service) + " (" + esc(i.tier) + (i.qty > 1 ? " ×" + i.qty : "") + ")"; }).join(", ");
    var updates = (o.updates || []).slice().reverse();
    var dels = o.deliverables || [];
    qs("#manage").innerHTML = '<div class="card manage">' +
      "<h3>" + esc(o.public_id) + "</h3>" +
      '<p class="sub">' + esc(o.customer_name) + " &lt;" + esc(o.customer_email) + "&gt;" + (o.customer_whatsapp ? " · " + esc(o.customer_whatsapp) : "") +
        "<br>" + items + " · <b>" + money(o.total) + "</b>" + (o.payment_method ? " · " + esc(o.payment_method) : "") + "</p>" +
      '<div class="dash-status" id="m-status"></div>' +
      '<div class="field"><label>Status</label><div class="status-grid" id="m-statuses">' +
        STATUSES.map(function (s) { return '<button type="button" data-s="' + s[0] + '" class="' + (o.status === s[0] ? "sel" : "") + '">' + esc(s[1]) + "</button>"; }).join("") + "</div></div>" +
      '<div class="field"><label>Progress</label><div class="range-row"><input type="range" id="m-prog" min="0" max="100" step="5" value="' + (o.progress || 0) + '"><output id="m-progOut">' + (o.progress || 0) + "%</output></div></div>" +
      '<div class="two"><div class="field"><label for="m-due">Due date</label><input class="input" type="date" id="m-due" value="' + (o.due_date || "") + '"></div>' +
      '<div class="field"><label for="m-pay">Payment</label><select class="select" id="m-pay">' +
        ["unpaid", "paid", "refunded"].map(function (p) { return '<option value="' + p + '"' + (o.payment_status === p ? " selected" : "") + ">" + p.charAt(0).toUpperCase() + p.slice(1) + "</option>"; }).join("") +
      "</select></div></div>" +
      '<button class="btn btn-primary btn-block" id="m-save">Save changes</button>' +
      '<hr class="divider" style="margin:1.3rem 0">' +
      '<div class="field"><label for="m-msg">Post an update to the client</label><textarea class="textarea" id="m-msg" placeholder="e.g. Wireframes done, building the API now…"></textarea></div>' +
      '<button class="btn btn-ghost btn-block" id="m-post">Post update</button>' +
      (updates.length ? '<div class="admin-updates">' + updates.map(function (u) { return '<div class="u">' + esc(u.message) + "<small>" + esc(fmtDate(u.created_at)) + (u.status ? " · " + esc(u.status) : "") + "</small></div>"; }).join("") + "</div>" : "") +
      '<hr class="divider" style="margin:1.3rem 0">' +
      '<label style="font-weight:600;font-size:.88rem">Deliverables <span style="color:var(--muted);font-weight:400">(preview always visible · final unlocks when Paid)</span></label>' +
      (dels.length ? '<div class="dlv-admin-list">' + dels.map(function (d) {
        return '<div class="dlv-admin"><div><b>' + esc(d.title || "Deliverable") + "</b><small>" + (d.preview_url ? "preview ✓ " : "") + (d.final_url ? "final ✓" : "no final") + "</small></div>" +
          '<button class="btn btn-outline btn-sm" data-deldel="' + d.id + '">Remove</button></div>';
      }).join("") + "</div>" : '<p class="form-note">No files attached yet.</p>') +
      '<div class="two"><div class="field"><label for="d-title">Title</label><input class="input" id="d-title" placeholder="Final design files"></div>' +
      '<div class="field"><label for="d-preview">Preview URL</label><input class="input" id="d-preview" placeholder="https://… watermarked/demo"></div></div>' +
      '<div class="two"><div class="field"><label for="d-final">Final URL (gated)</label><input class="input" id="d-final" placeholder="https://… real product"></div>' +
      '<div class="field"><label for="d-note">Note</label><input class="input" id="d-note" placeholder="optional"></div></div>' +
      '<button class="btn btn-ghost btn-block" id="d-add">Add deliverable</button>' +
      "</div>";

    var sel = o.status;
    qsa("#m-statuses button").forEach(function (b) { b.addEventListener("click", function () { sel = b.dataset.s; qsa("#m-statuses button").forEach(function (x) { x.classList.toggle("sel", x.dataset.s === sel); }); }); });
    var prog = qs("#m-prog"), progOut = qs("#m-progOut");
    prog.addEventListener("input", function () { progOut.textContent = prog.value + "%"; });

    qs("#m-save").addEventListener("click", function () {
      var payload = { status: sel, progress: parseInt(prog.value, 10), payment_status: qs("#m-pay").value };
      var due = qs("#m-due").value; if (due) payload.due_date = due;
      mStatus("ok", "Saving…");
      API.patch("/api/admin/orders/" + encodeURIComponent(o.public_id), payload).then(function (u) {
        mergeOrder(u); state.selected = u.public_id; renderRows(); renderManage(u); refreshStats(); mStatus("ok", "Saved.");
      }).catch(function (err) { mStatus("err", err.message || "Save failed."); });
    });
    qs("#m-post").addEventListener("click", function () {
      var msg = qs("#m-msg").value.trim();
      if (!msg) { mStatus("err", "Write a message first."); return; }
      mStatus("ok", "Posting…");
      API.post("/api/admin/orders/" + encodeURIComponent(o.public_id) + "/updates", { message: msg, progress: parseInt(prog.value, 10), status: sel })
        .then(function (u) { mergeOrder(u); renderRows(); renderManage(u); mStatus("ok", "Update posted."); })
        .catch(function (err) { mStatus("err", err.message || "Failed."); });
    });
    qs("#d-add").addEventListener("click", function () {
      var title = qs("#d-title").value.trim(), preview = qs("#d-preview").value.trim(), final = qs("#d-final").value.trim();
      if (!title && !preview && !final) { mStatus("err", "Add a title and at least one link."); return; }
      mStatus("ok", "Adding file…");
      API.post("/api/admin/orders/" + encodeURIComponent(o.public_id) + "/deliverables",
        { title: title, preview_url: preview, final_url: final, note: qs("#d-note").value.trim() })
        .then(function (u) { mergeOrder(u); renderManage(u); mStatus("ok", "Deliverable added."); })
        .catch(function (err) { mStatus("err", err.message || "Failed."); });
    });
    qsa("[data-deldel]").forEach(function (b) {
      b.addEventListener("click", function () {
        API.del("/api/admin/deliverables/" + b.dataset.deldel)
          .then(function () { return API.get("/api/admin/orders/" + encodeURIComponent(o.public_id)); })
          .then(function (u) { mergeOrder(u); renderManage(u); mStatus("ok", "Removed."); })
          .catch(function (err) { mStatus("err", err.message || "Failed."); });
      });
    });
  }
  function mStatus(type, msg) { var s = qs("#m-status"); if (s) { s.textContent = msg; s.className = "dash-status show " + type; } }
  function mergeOrder(u) { for (var i = 0; i < state.orders.length; i++) { if (state.orders[i].public_id === u.public_id) { state.orders[i] = u; return; } } state.orders.unshift(u); }
  function refreshStats() { API.get("/api/admin/stats").then(function (s) { state.stats = s; if (qs("#stats")) { renderStats(); renderFilters(); } }).catch(function () {}); }

  /* ---- SERVICES TAB ---- */
  function renderServicesTab() {
    qs("#tabBody").innerHTML =
      '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;margin-bottom:1rem">' +
        '<p class="form-note" style="max-width:44rem;margin:0">These are the services shown on your site. Add, edit, hide or delete any of them here — changes appear on the next site load.</p>' +
        '<button class="btn btn-primary btn-sm" id="svcAdd">' + SVG.plus + " Add service</button></div>" +
      '<div id="svcImport"></div>' +
      '<div id="svcForm"></div>' +
      '<div class="svc-list" id="svcList"><p class="form-note">Loading…</p></div>';
    qs("#svcAdd").addEventListener("click", function () { showServiceForm(null); });
    loadServices();
  }

  function builtinList() { return (window.SITE_DATA && window.SITE_DATA.services) || []; }
  function builtinToService(b) {
    return { title: b.title, category: b.category || "Development", icon: b.icon || "spark",
      short: b.short || "", tags: b.tags || [], packages: b.packages || [],
      deliverables: b.deliverables || [], active: true, sort_order: 0, slug: b.id };
  }

  function loadServices() {
    API.get("/api/admin/services").then(renderServiceList).catch(function (err) {
      if (err.status === 401 || err.status === 403) { API.logout(); renderLogin("Session expired."); return; }
      qs("#svcList").innerHTML = '<div class="form-status err show">' + esc(err.message || "Failed to load.") + "</div>";
    });
  }

  function renderImportBanner(list) {
    var box = qs("#svcImport"); if (!box) return;
    var have = {}; list.forEach(function (s) { have[s.slug] = true; });
    var missing = builtinList().filter(function (b) { return !have[b.id]; });
    if (!missing.length) { box.innerHTML = ""; return; }
    box.innerHTML =
      '<div class="card" style="border:1px solid var(--accent);background:var(--grad-soft);margin-bottom:1.2rem">' +
      '<b>Bring your built-in services into the dashboard</b>' +
      '<p style="color:var(--muted);font-size:.92rem;margin:.4rem 0 .9rem">Your site has <b>' + missing.length +
      '</b> built-in service(s) that aren\'t managed here yet. Import them once to edit, hide, reorder or delete them like any other.</p>' +
      '<button class="btn btn-primary btn-sm" id="svcImportBtn">' + SVG.plus + " Import " + missing.length + " built-in service(s)</button></div>";
    qs("#svcImportBtn").addEventListener("click", function () {
      var btn = qs("#svcImportBtn"); btn.disabled = true; btn.textContent = "Importing…";
      API.post("/api/admin/services/import", { services: missing.map(builtinToService) })
        .then(function () { loadServices(); })
        .catch(function (err) { btn.disabled = false; window.alert(err.message || "Import failed."); });
    });
  }

  function renderServiceList(list) {
    state.services = list;
    renderImportBanner(list);
    var box = qs("#svcList");
    if (!list.length) { box.innerHTML = '<p class="form-note">No services yet — click “Add service”, or import your built-ins above.</p>'; return; }
    box.innerHTML = list.map(function (s) {
      return '<div class="svc-item' + (s.active ? "" : " off") + '"><div><div class="t">' + esc(s.title) + '</div><div class="c">' + esc(s.category) + " · " + (s.packages ? s.packages.length : 0) + " package(s)" + (s.active ? "" : " · hidden") + "</div></div>" +
        '<div style="display:flex;gap:.5rem"><button class="btn btn-outline btn-sm" data-svcedit="' + s.id + '">Edit</button><button class="btn btn-outline btn-sm" data-svcdel="' + s.id + '">Delete</button></div></div>';
    }).join("");
    qsa("[data-svcedit]", box).forEach(function (b) { b.addEventListener("click", function () { showServiceForm(list.filter(function (x) { return String(x.id) === b.dataset.svcedit; })[0]); }); });
    qsa("[data-svcdel]", box).forEach(function (b) {
      b.addEventListener("click", function () {
        if (!window.confirm("Delete this service?")) return;
        API.del("/api/admin/services/" + b.dataset.svcdel).then(loadServices).catch(function (err) { window.alert(err.message || "Failed."); });
      });
    });
  }

  function showServiceForm(svc) {
    var pk = (svc && svc.packages) || [];
    function pkRow(i, tier) {
      var p = pk[i] || {};
      return '<div class="card" style="padding:1rem;margin-bottom:.6rem"><b style="font-size:.85rem">' + tier + "</b>" +
        '<div class="two" style="margin-top:.5rem"><div class="field"><label>Price (' + (C.currency || "$") + ")</label><input class=\"input\" id=\"p-price-" + i + '" type="number" min="0" value="' + (p.price || "") + '"></div>' +
        '<div class="field"><label>Delivery</label><input class="input" id="p-del-' + i + '" value="' + esc(p.delivery || "") + '" placeholder="e.g. 5 days"></div></div>' +
        '<div class="field"><label>Summary</label><input class="input" id="p-sum-' + i + '" value="' + esc(p.summary || "") + '"></div>' +
        '<div class="field"><label>Features (comma-separated)</label><input class="input" id="p-feat-' + i + '" value="' + esc((p.features || []).join(", ")) + '"></div></div>';
    }
    qs("#svcForm").innerHTML = '<div class="card" style="margin-bottom:1.2rem"><h3 style="font-size:1.1rem;margin-bottom:1rem">' + (svc ? "Edit service" : "Add a service") + "</h3>" +
      '<div class="dash-status" id="svc-status"></div>' +
      '<div class="two"><div class="field"><label>Title</label><input class="input" id="s-title" value="' + esc(svc ? svc.title : "") + '" placeholder="e.g. Discord Bot Development"></div>' +
      '<div class="field"><label>Category</label><input class="input" id="s-cat" value="' + esc(svc ? svc.category : "Development") + '" placeholder="Development / Design / Automation…"></div></div>' +
      '<div class="two"><div class="field"><label>Icon</label><select class="select" id="s-icon">' + ICON_CHOICES.map(function (ic) { return '<option' + (svc && svc.icon === ic ? " selected" : "") + ">" + ic + "</option>"; }).join("") + "</select></div>" +
      '<div class="field"><label>Tags (comma-separated)</label><input class="input" id="s-tags" value="' + esc(svc ? (svc.tags || []).join(", ") : "") + '"></div></div>' +
      '<div class="field"><label>Short description</label><textarea class="textarea" id="s-short" style="min-height:70px">' + esc(svc ? svc.short : "") + "</textarea></div>" +
      '<label style="font-weight:600;font-size:.88rem">Packages <span style="color:var(--muted);font-weight:400">(fill the tiers you offer; blank price = skipped)</span></label>' +
      '<div style="margin-top:.5rem">' + pkRow(0, "Basic") + pkRow(1, "Standard (popular)") + pkRow(2, "Premium") + "</div>" +
      '<label class="field" style="flex-direction:row;align-items:center;gap:.5rem;margin:.4rem 0 1rem"><input type="checkbox" id="s-active" ' + (!svc || svc.active ? "checked" : "") + "> Active (visible on site)</label>" +
      '<div style="display:flex;gap:.6rem"><button class="btn btn-primary" id="s-save">' + (svc ? "Save changes" : "Create service") + '</button><button class="btn btn-ghost" id="s-cancel">Cancel</button></div></div>';
    qs("#svcForm").scrollIntoView({ behavior: "smooth", block: "nearest" });
    qs("#s-cancel").addEventListener("click", function () { qs("#svcForm").innerHTML = ""; });
    qs("#s-save").addEventListener("click", function () {
      var title = qs("#s-title").value.trim();
      if (!title) { svcStatus("err", "Title is required."); return; }
      var tiers = ["Basic", "Standard", "Premium"], packages = [];
      tiers.forEach(function (tier, i) {
        var price = parseFloat(qs("#p-price-" + i).value);
        if (!price && price !== 0) return;
        if (isNaN(price)) return;
        packages.push({ tier: tier, price: price, delivery: qs("#p-del-" + i).value.trim(), revisions: 2,
          summary: qs("#p-sum-" + i).value.trim(), features: csv(qs("#p-feat-" + i).value), popular: i === 1 });
      });
      var payload = { title: title, category: qs("#s-cat").value.trim() || "Development", icon: qs("#s-icon").value,
        short: qs("#s-short").value.trim(), tags: csv(qs("#s-tags").value), packages: packages,
        active: qs("#s-active").checked, sort_order: 0 };
      svcStatus("ok", "Saving…");
      var p = svc ? API.patch("/api/admin/services/" + svc.id, payload) : API.post("/api/admin/services", payload);
      p.then(function () { qs("#svcForm").innerHTML = ""; loadServices(); }).catch(function (err) { svcStatus("err", err.message || "Failed."); });
    });
  }
  function svcStatus(type, msg) { var s = qs("#svc-status"); if (s) { s.textContent = msg; s.className = "dash-status show " + type; } }

  /* ---- INBOX (live chat) TAB ---- */
  function authedBlob(path) {
    return fetch((C.apiBase || "") + path, { headers: { Authorization: "Bearer " + API.getToken() } })
      .then(function (r) { if (!r.ok) throw new Error("load failed"); return r.blob(); });
  }
  function mdLite(s) { var h = esc(s); h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>"); return h.replace(/\n/g, "<br>"); }

  function renderInboxTab() {
    qs("#tabBody").innerHTML =
      '<div class="admin-grid"><div class="order-rows" id="convRows"><p class="form-note">Loading…</p></div>' +
      '<div id="convThread"><div class="card manage"><div class="empty">Select a conversation to read &amp; reply. The bot handles chats until you jump in.</div></div></div></div>';
    loadConversations();
  }

  function loadConversations() {
    API.get("/api/admin/chat/conversations").then(function (list) {
      state.inboxList = list; renderConvList();
      if (state.selectedConv) loadConvThread(state.selectedConv);
    }).catch(function (err) {
      if (err.status === 401 || err.status === 403) { API.logout(); renderLogin("Session expired."); return; }
      var box = qs("#convRows"); if (box) box.innerHTML = '<div class="form-status err show">' + esc(err.message || "Failed.") + "</div>";
    });
  }

  function renderConvList() {
    var box = qs("#convRows"); if (!box) return;
    var list = state.inboxList || [];
    if (!list.length) { box.innerHTML = '<p class="form-note">No conversations yet.</p>'; return; }
    box.innerHTML = list.map(function (c) {
      var chip = c.unread ? '<span class="status-chip" style="background:var(--accent-3);color:#fff">' + c.unread + " new</span>"
        : (c.needs_human ? '<span class="status-chip st-received">needs you</span>' : "");
      return '<button class="order-row' + (state.selectedConv === c.public_id ? " active" : "") + '" data-cid="' + esc(c.public_id) + '">' +
        '<div class="r1"><span class="oid">' + esc(c.customer_name || c.customer_email || "Visitor") + "</span>" + chip + "</div>" +
        '<div class="who">' + esc(c.last_message || "…") + "</div>" +
        '<div class="r2" style="justify-content:space-between"><small style="color:var(--muted)">' + esc(fmtDate(c.last_message_at)) + "</small>" +
        (c.human_takeover ? '<small style="color:var(--accent-2)">live</small>' : '<small style="color:var(--muted-2)">bot</small>') + "</div></button>";
    }).join("");
    qsa("#convRows .order-row").forEach(function (b) { b.addEventListener("click", function () { openConv(b.dataset.cid); }); });
  }

  function openConv(cid) {
    state.selectedConv = cid; renderConvList();
    if (convTimer) clearInterval(convTimer);
    loadConvThread(cid);
    convTimer = setInterval(function () { if (state.tab === "inbox" && state.selectedConv === cid) loadConvThread(cid); }, 5000);
  }

  function loadConvThread(cid) {
    API.get("/api/admin/chat/conversations/" + encodeURIComponent(cid)).then(renderConvThread).catch(function () {});
  }

  function renderAdmMsg(m) {
    var who = m.sender === "dev" ? "me" : "them";
    var label = m.sender === "bot" ? '<span class="adm-who">Bot</span>'
      : (m.sender === "client" ? '<span class="adm-who">Client</span>' : "");
    var content;
    if (m.attachment) {
      var a = m.attachment;
      if ((a.content_type || "").indexOf("image/") === 0) {
        content = '<img class="adm-att" data-att="' + a.id + '" alt="' + esc(a.filename) + '">';
      } else {
        content = '<button class="btn btn-outline btn-sm" data-attfile="' + a.id + '">📄 ' + esc(a.filename) + "</button>";
      }
    } else { content = mdLite(m.body); }
    return '<div class="adm-msg ' + who + (m.sender === "bot" ? " bot" : "") + '">' + label + '<div class="adm-bubble">' + content + "</div></div>";
  }

  function renderConvThread(th) {
    var manage = qs("#convThread"); if (!manage) return;
    state.selectedConv = th.public_id;
    (state.inboxList || []).forEach(function (c) { if (c.public_id === th.public_id) c.unread = 0; });
    var msgs = (th.messages || []).map(renderAdmMsg).join("");
    manage.innerHTML = '<div class="card manage">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap">' +
        "<h3 style=\"margin:0\">" + esc(th.customer_name || "Visitor") + "</h3>" +
        '<button class="btn btn-outline btn-sm" id="botToggle">Bot: ' + (th.human_takeover ? "paused" : "active") + "</button></div>" +
      '<p class="sub">' + esc(th.customer_email || "no email on file") + (th.needs_human ? ' · <b style="color:var(--accent-3)">asked for a human</b>' : "") + "</p>" +
      '<div class="adm-chat" id="admChat">' + msgs + "</div>" +
      '<div class="dash-status" id="conv-status"></div>' +
      '<div class="field"><textarea class="textarea" id="conv-msg" placeholder="Reply to the client…"></textarea></div>' +
      '<label style="display:flex;align-items:center;gap:.5rem;font-size:.84rem;color:var(--muted);margin-bottom:.6rem"><input type="checkbox" id="conv-botresume"> Let the bot keep auto-answering after my reply</label>' +
      '<button class="btn btn-primary btn-block" id="conv-send">Send reply</button></div>';
    loadAdmAttachments();
    var chat = qs("#admChat"); if (chat) chat.scrollTop = chat.scrollHeight;
    renderConvList();
    qs("#conv-send").addEventListener("click", function () { sendDevReply(th.public_id); });
    qs("#botToggle").addEventListener("click", function () {
      API.post("/api/admin/chat/conversations/" + encodeURIComponent(th.public_id) + "/bot", {})
        .then(function () { loadConvThread(th.public_id); }).catch(function () {});
    });
  }

  function loadAdmAttachments() {
    qsa("#admChat img[data-att]").forEach(function (img) {
      authedBlob("/api/admin/chat/attachments/" + img.dataset.att).then(function (b) {
        var u = URL.createObjectURL(b); img.src = u; img.style.cursor = "pointer";
        img.addEventListener("click", function () { window.open(u, "_blank"); });
      }).catch(function () {});
    });
    qsa("#admChat [data-attfile]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        authedBlob("/api/admin/chat/attachments/" + btn.dataset.attfile)
          .then(function (b) { window.open(URL.createObjectURL(b), "_blank"); })
          .catch(function () { window.alert("Could not load file."); });
      });
    });
  }

  function sendDevReply(cid) {
    var ta = qs("#conv-msg"), msg = (ta.value || "").trim();
    if (!msg) { convStatus("err", "Write a reply first."); return; }
    var resume = qs("#conv-botresume").checked;
    convStatus("ok", "Sending…");
    API.post("/api/admin/chat/conversations/" + encodeURIComponent(cid) + "/messages", { body: msg, let_bot_resume: resume })
      .then(function () { ta.value = ""; loadConvThread(cid); pollBadges(); convStatus("ok", "Sent."); })
      .catch(function (err) { convStatus("err", err.message || "Failed."); });
  }
  function convStatus(type, msg) { var s = qs("#conv-status"); if (s) { s.textContent = msg; s.className = "dash-status show " + type; } }

  /* ---- REVIEWS TAB ---- */
  function renderReviewsTab() {
    qs("#tabBody").innerHTML =
      '<p class="form-note" style="margin-bottom:1rem">Reviews submitted from your site. Approve to publish them; reject or delete spam.</p>' +
      '<div id="revList"><p class="form-note">Loading…</p></div>';
    loadReviews();
  }
  function loadReviews() {
    API.get("/api/admin/testimonials").then(renderReviews).catch(function (err) {
      if (err.status === 401 || err.status === 403) { API.logout(); renderLogin("Session expired."); return; }
      qs("#revList").innerHTML = '<div class="form-status err show">' + esc(err.message || "Failed.") + "</div>";
    });
  }
  function renderReviews(list) {
    state.reviews = list; var box = qs("#revList");
    if (!list.length) { box.innerHTML = '<p class="form-note">No reviews submitted yet.</p>'; return; }
    var rank = { pending: 0, approved: 1, rejected: 2 };
    list = list.slice().sort(function (a, b) { return (rank[a.status] || 0) - (rank[b.status] || 0); });
    box.innerHTML = list.map(function (t) {
      var stars = ""; for (var i = 0; i < (t.rating || 0); i++) stars += "★";
      var chipClass = t.status === "approved" ? "st-delivered" : (t.status === "rejected" ? "st-cancelled" : "st-received");
      return '<div class="rev-item card">' +
        '<div class="rev-top"><div><b>' + esc(t.name) + '</b> <span style="color:var(--muted)">' + esc(t.role || "") + (t.location ? " · " + esc(t.location) : "") + "</span>" +
        '<div style="color:var(--warn);letter-spacing:2px">' + stars + "</div></div>" +
        '<span class="status-chip ' + chipClass + '">' + esc(t.status) + "</span></div>" +
        '<p style="margin:.5rem 0">“' + esc(t.text) + "”</p>" +
        '<div style="display:flex;gap:.5rem;flex-wrap:wrap">' +
          (t.status !== "approved" ? '<button class="btn btn-primary btn-sm" data-rev-approve="' + t.id + '">Approve</button>' : "") +
          (t.status !== "rejected" ? '<button class="btn btn-outline btn-sm" data-rev-reject="' + t.id + '">Reject</button>' : "") +
          '<button class="btn btn-outline btn-sm" data-rev-del="' + t.id + '">Delete</button></div></div>';
    }).join("");
    qsa("[data-rev-approve]", box).forEach(function (b) { b.addEventListener("click", function () { setReview(b.dataset.revApprove, "approved"); }); });
    qsa("[data-rev-reject]", box).forEach(function (b) { b.addEventListener("click", function () { setReview(b.dataset.revReject, "rejected"); }); });
    qsa("[data-rev-del]", box).forEach(function (b) { b.addEventListener("click", function () { if (window.confirm("Delete this review permanently?")) delReview(b.dataset.revDel); }); });
  }
  function setReview(id, status) {
    API.patch("/api/admin/testimonials/" + id, { status: status }).then(function () { loadReviews(); pollBadges(); })
      .catch(function (err) { window.alert(err.message || "Failed."); });
  }
  function delReview(id) {
    API.del("/api/admin/testimonials/" + id).then(function () { loadReviews(); pollBadges(); })
      .catch(function (err) { window.alert(err.message || "Failed."); });
  }

  function startDashboard() { renderShell(); }

  /* ---- boot ---- */
  if (API.isAuthed()) {
    API.me().then(function (me) {
      API.setUser(me);
      if (me.role !== "admin") { API.logout(); renderLogin("That account isn't an admin."); }
      else startDashboard();
    }).catch(function () { API.logout(); renderLogin(); });
  } else {
    renderLogin();
  }
})();
