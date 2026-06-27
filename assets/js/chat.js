/* =============================================================================
   CHAT WIDGET — floating assistant + live chat.
   The bot answers instantly (from your services catalog); the developer can take
   over live from the dashboard Inbox. Accepts image/PDF uploads. Degrades to
   WhatsApp/email when the backend isn't reachable. No third-party scripts.
   ========================================================================== */
(function () {
  "use strict";
  var C = window.SITE_CONFIG || {};
  var CHAT = C.chat || {};
  if (CHAT.enabled === false) return;

  var BASE = C.apiBase || "";
  var LS_KEY = "alira_chat";
  var POLL_OPEN = 4000, POLL_IDLE = 20000;

  var S = { open: false, conv: null, secret: null, started: false, starting: false,
            sending: false, msgs: [], quick: [], human: false, needsHuman: false,
            timer: null, lastSeen: 0, unread: 0, down: false };

  /* ---- helpers ---- */
  function esc(s) { var d = document.createElement("div"); d.textContent = (s == null ? "" : String(s)); return d.innerHTML; }
  function md(s) {
    var h = esc(s);
    h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    h = h.replace(/\n/g, "<br>");
    return h;
  }
  function ce(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function load() { try { return JSON.parse(localStorage.getItem(LS_KEY) || "null"); } catch (e) { return null; } }
  function save() { try { localStorage.setItem(LS_KEY, JSON.stringify({ conv: S.conv, secret: S.secret })); } catch (e) {} }
  function token() { try { return (window.API && window.API.getToken && window.API.getToken()) || ""; } catch (e) { return ""; } }
  function user() { try { return (window.API && window.API.getUser && window.API.getUser()) || null; } catch (e) { return null; } }

  function api(method, path, body, isForm) {
    var headers = { Accept: "application/json" };
    if (S.secret) headers["X-Chat-Secret"] = S.secret;
    var t = token(); if (t) headers["Authorization"] = "Bearer " + t;
    var opt = { method: method, headers: headers };
    if (body !== undefined) {
      if (isForm) { opt.body = body; }
      else { headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
    }
    return fetch(BASE + path, opt).then(function (r) {
      return r.text().then(function (txt) {
        var data = null; if (txt) { try { data = JSON.parse(txt); } catch (e) { data = txt; } }
        if (!r.ok) { var d = data && data.detail; var e = new Error(typeof d === "string" ? d : "Request failed"); e.status = r.status; throw e; }
        return data;
      });
    });
  }

  /* ---- DOM ---- */
  var launcher, panel, body, qbar, input, sendBtn, fileInput, takeoverPill, dot;

  var ICON_CHAT = '<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 8.5 8.5 0 0 1-3.8-.9L3 21l1.9-5.7A8.38 8.38 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.38 8.38 0 0 1 21 11.5z"/></svg>';
  var ICON_CLOSE = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  var ICON_SEND = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';
  var ICON_CLIP = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>';

  function build() {
    launcher = ce("button", "chat-launcher", ICON_CHAT);
    launcher.setAttribute("aria-label", "Open chat");
    dot = ce("span", "chat-dot"); dot.hidden = true; launcher.appendChild(dot);
    launcher.addEventListener("click", toggle);

    panel = ce("div", "chat-panel");
    panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "Chat");
    panel.hidden = true;
    panel.innerHTML =
      '<div class="chat-head"><div class="chat-head-main"><span class="chat-avatar">' +
        (C.initials || "AI") + '</span><div><b>' + esc(CHAT.title || "Chat with us") + '</b>' +
        '<small id="chat-sub">' + esc(CHAT.subtitle || "We usually reply fast") + '</small></div></div>' +
        '<button class="chat-x" aria-label="Close chat">' + ICON_CLOSE + '</button></div>' +
      '<div class="chat-body" id="chat-body"></div>' +
      '<div class="chat-quick" id="chat-quick"></div>' +
      '<form class="chat-input" id="chat-form">' +
        '<button type="button" class="chat-clip" id="chat-clip" aria-label="Attach a file (image or PDF)">' + ICON_CLIP + '</button>' +
        '<input type="file" id="chat-file" accept="image/png,image/jpeg,image/gif,image/webp,application/pdf" hidden>' +
        '<textarea id="chat-text" rows="1" placeholder="Type a message…" aria-label="Message"></textarea>' +
        '<button type="submit" class="chat-send" id="chat-send" aria-label="Send">' + ICON_SEND + '</button>' +
      '</form>' +
      '<div class="chat-foot">Files: images &amp; PDF only · powered by ' + esc(C.brand || "us") + '</div>';

    document.body.appendChild(launcher);
    document.body.appendChild(panel);

    body = panel.querySelector("#chat-body");
    qbar = panel.querySelector("#chat-quick");
    input = panel.querySelector("#chat-text");
    sendBtn = panel.querySelector("#chat-send");
    fileInput = panel.querySelector("#chat-file");
    takeoverPill = panel.querySelector("#chat-sub");

    panel.querySelector(".chat-x").addEventListener("click", toggle);
    panel.querySelector("#chat-form").addEventListener("submit", function (e) { e.preventDefault(); sendText(); });
    panel.querySelector("#chat-clip").addEventListener("click", function () { fileInput.click(); });
    fileInput.addEventListener("change", onFile);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendText(); }
    });
    input.addEventListener("input", autoGrow);

    var saved = load();
    if (saved && saved.conv && saved.secret) { S.conv = saved.conv; S.secret = saved.secret; S.started = true; }
  }

  function autoGrow() { input.style.height = "auto"; input.style.height = Math.min(input.scrollHeight, 110) + "px"; }

  /* ---- rendering ---- */
  function attUrl(a) { return BASE + "/api/chat/" + encodeURIComponent(S.conv) + "/attachments/" + a.id + "?s=" + encodeURIComponent(S.secret || ""); }

  function renderMsgs() {
    if (!body) return;
    body.innerHTML = S.msgs.map(function (m) {
      var side = m.sender === "client" ? "me" : "them";
      var who = m.sender === "dev" ? '<span class="chat-by">' + esc(C.name || "Developer") + "</span>" : "";
      var content = "";
      if (m.attachment) {
        var a = m.attachment;
        if ((a.content_type || "").indexOf("image/") === 0) {
          content = '<a href="' + attUrl(a) + '" target="_blank" rel="noopener"><img class="chat-img" src="' + attUrl(a) + '" alt="' + esc(a.filename) + '"></a>';
        } else {
          content = '<a class="chat-file" href="' + attUrl(a) + '" target="_blank" rel="noopener">📄 ' + esc(a.filename) + "</a>";
        }
      } else {
        content = md(m.body);
      }
      return '<div class="chat-msg ' + side + (m.sender === "bot" ? " bot" : "") + '">' + who + '<div class="bubble">' + content + "</div></div>";
    }).join("");
    body.scrollTop = body.scrollHeight;
  }

  function renderQuick() {
    if (!qbar) return;
    qbar.innerHTML = (S.quick || []).map(function (q) {
      return '<button type="button" class="chat-chip">' + esc(q) + "</button>";
    }).join("");
    Array.prototype.forEach.call(qbar.querySelectorAll(".chat-chip"), function (b) {
      b.addEventListener("click", function () { sendText(b.textContent); });
    });
  }

  function typing(on) {
    var t = body.querySelector(".chat-typing");
    if (on && !t) { var d = ce("div", "chat-msg them"); d.innerHTML = '<div class="bubble chat-typing"><span></span><span></span><span></span></div>'; body.appendChild(d); body.scrollTop = body.scrollHeight; }
    else if (!on && t) { t.parentNode.remove(); }
  }

  function applyThread(res) {
    if (!res) return;
    S.msgs = res.messages || [];
    S.quick = res.quick_replies || [];
    S.human = !!res.human_takeover;
    S.needsHuman = !!res.needs_human;
    if (takeoverPill) takeoverPill.textContent = S.human ? (C.name || "Developer") + " is in the chat" : (CHAT.subtitle || "We usually reply fast");
    renderMsgs(); renderQuick();
    S.lastSeen = S.msgs.length;
    S.unread = 0; if (dot) dot.hidden = true;
  }

  /* ---- actions ---- */
  function ensureStarted() {
    if (S.started && S.conv) return fetchThread();
    if (S.starting) return Promise.resolve();
    S.starting = true;
    var u = user();
    return api("POST", "/api/chat/start", { name: (u && u.name) || "", email: (u && u.email) || "" })
      .then(function (res) {
        S.conv = res.public_id; S.secret = res.secret; S.started = true; S.down = false; save();
        applyThread(res);
      })
      .catch(function () { S.down = true; renderFallback(); })
      .then(function () { S.starting = false; });
  }

  function fetchThread() {
    if (!S.conv) return Promise.resolve();
    return api("GET", "/api/chat/" + encodeURIComponent(S.conv))
      .then(function (res) { S.down = false; if (!S.open) { flagUnread(res); } else { applyThread(res); } })
      .catch(function (e) { if (e.status === 403 || e.status === 404) { reset(); } else { S.down = true; } });
  }

  function flagUnread(res) {
    var msgs = res.messages || [];
    var incoming = msgs.filter(function (m) { return m.sender !== "client"; }).length;
    if (msgs.length > S.lastSeen && incoming) { S.unread = msgs.length - S.lastSeen; if (dot) { dot.hidden = false; dot.textContent = S.unread > 9 ? "9+" : String(S.unread); } }
    S.msgs = msgs;
  }

  function sendText(text) {
    var msg = (text != null ? text : input.value).trim();
    if (!msg || S.sending) return;
    if (S.down || !S.started) { ensureStarted(); return; }
    S.sending = true; input.value = ""; autoGrow();
    // optimistic echo
    S.msgs.push({ sender: "client", body: msg }); renderMsgs(); S.quick = []; renderQuick();
    typing(true);
    api("POST", "/api/chat/" + encodeURIComponent(S.conv) + "/messages", { body: msg })
      .then(function (res) { typing(false); applyThread(res); })
      .catch(function (e) { typing(false); if (e.status === 403 || e.status === 404) { reset(); } toast(e.message || "Couldn't send."); })
      .then(function () { S.sending = false; });
  }

  function onFile() {
    var f = fileInput.files && fileInput.files[0];
    fileInput.value = "";
    if (!f) return;
    if (f.size > 10 * 1024 * 1024) { toast("File too large (max 10 MB)."); return; }
    if (S.down || !S.started) { ensureStarted().then(function () { doUpload(f); }); return; }
    doUpload(f);
  }
  function doUpload(f) {
    var fd = new FormData(); fd.append("file", f);
    S.msgs.push({ sender: "client", body: "📎 " + f.name }); renderMsgs(); typing(true);
    api("POST", "/api/chat/" + encodeURIComponent(S.conv) + "/upload", fd, true)
      .then(function (res) { typing(false); applyThread(res); })
      .catch(function (e) { typing(false); toast(e.message || "Upload failed."); });
  }

  function renderFallback() {
    var wa = (C.whatsapp || "").replace(/\D/g, "");
    body.innerHTML =
      '<div class="chat-msg them"><div class="bubble">Hi! 👋 Our live assistant is offline right now, but you can reach ' +
      esc(C.name || "us") + ' directly:</div></div>';
    qbar.innerHTML =
      (wa ? '<a class="chat-chip" href="https://wa.me/' + wa + '" target="_blank" rel="noopener">💬 WhatsApp</a>' : "") +
      (C.email ? '<a class="chat-chip" href="mailto:' + esc(C.email) + '">✉️ Email</a>' : "") +
      '<a class="chat-chip" href="index.html#contact">📝 Custom request</a>';
  }

  function toast(m) {
    var el = ce("div", "chat-toast", esc(m)); panel.appendChild(el);
    setTimeout(function () { el.classList.add("show"); }, 10);
    setTimeout(function () { el.remove(); }, 3200);
  }

  function reset() { S.conv = null; S.secret = null; S.started = false; S.msgs = []; try { localStorage.removeItem(LS_KEY); } catch (e) {} }

  /* ---- open/close + polling ---- */
  function toggle() {
    S.open = !S.open;
    panel.hidden = !S.open;
    launcher.classList.toggle("open", S.open);
    launcher.innerHTML = S.open ? ICON_CLOSE : ICON_CHAT;
    if (S.open) {
      if (dot) dot.hidden = true;
      launcher.appendChild(dot);
      ensureStarted().then(function () { if (!S.down) applyThread({ messages: S.msgs, quick_replies: S.quick, human_takeover: S.human, needs_human: S.needsHuman }); });
      setTimeout(function () { input && input.focus(); }, 100);
    }
    restartPoll();
  }

  function restartPoll() {
    if (S.timer) clearInterval(S.timer);
    // Clear a previous instance's poll too (SPA navigation re-runs this script,
    // so without this each page swap would leave another interval running).
    if (window.__chatPoll) clearInterval(window.__chatPoll);
    if (!S.started && !S.conv) return;
    var every = S.open ? POLL_OPEN : POLL_IDLE;
    S.timer = setInterval(function () {
      if (S.sending) return;
      fetchThread();
    }, every);
    window.__chatPoll = S.timer;
  }

  /* ---- boot ---- */
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
  function boot() {
    build();
    if (S.conv) restartPoll(); // resume idle polling to surface unread replies
  }
})();
