/* =============================================================================
   API client for the dashboards (client + admin). Talks to the FastAPI backend.
   ========================================================================== */
window.API = (function () {
  "use strict";
  var BASE = (window.SITE_CONFIG && window.SITE_CONFIG.apiBase) || "";
  var TOKEN_KEY = "alira_token", USER_KEY = "alira_user";

  function ls() { try { return window.localStorage; } catch (e) { return null; } }
  function getToken() { var s = ls(); return s ? (s.getItem(TOKEN_KEY) || "") : ""; }
  function setToken(t) { var s = ls(); if (!s) return; t ? s.setItem(TOKEN_KEY, t) : s.removeItem(TOKEN_KEY); }
  function getUser() { try { return JSON.parse(ls().getItem(USER_KEY) || "null"); } catch (e) { return null; } }
  function setUser(u) { var s = ls(); if (!s) return; u ? s.setItem(USER_KEY, JSON.stringify(u)) : s.removeItem(USER_KEY); }

  function req(method, path, body) {
    var headers = { "Accept": "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    var t = getToken();
    if (t) headers["Authorization"] = "Bearer " + t;
    return fetch(BASE + path, {
      method: method, headers: headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }).then(function (r) {
      return r.text().then(function (txt) {
        var data = null;
        if (txt) { try { data = JSON.parse(txt); } catch (e) { data = txt; } }
        if (!r.ok) {
          var d = data && data.detail;
          var msg = typeof d === "string" ? d
            : (Array.isArray(d) && d[0] && d[0].msg ? d[0].msg : "Request failed (" + r.status + ")");
          var err = new Error(msg); err.status = r.status; throw err;
        }
        return data;
      });
    });
  }

  function saveAuth(res) { if (res && res.access_token) { setToken(res.access_token); setUser(res.user); } return res; }

  return {
    base: BASE,
    getToken: getToken, setToken: setToken, getUser: getUser, setUser: setUser,
    isAuthed: function () { return !!getToken(); },
    logout: function () { setToken(""); setUser(null); },
    get: function (p) { return req("GET", p); },
    post: function (p, b) { return req("POST", p, b === undefined ? {} : b); },
    patch: function (p, b) { return req("PATCH", p, b === undefined ? {} : b); },
    del: function (p) { return req("DELETE", p); },
    register: function (d) { return req("POST", "/api/auth/register", d).then(saveAuth); },
    login: function (d) { return req("POST", "/api/auth/login", d).then(saveAuth); },
    me: function () { return req("GET", "/api/auth/me"); },
  };
})();
