/* =============================================================================
   STORE  —  cart, orders & tracking (client-side, localStorage)
   -----------------------------------------------------------------------------
   No backend required. Orders are saved in the visitor's browser so they can
   track them, and a copy is sent to you by email (Formspree) + WhatsApp.
   ========================================================================== */

(function () {
  "use strict";

  var CART_KEY = "alira_cart_v1";
  var ORDERS_KEY = "alira_orders_v1";
  var listeners = [];

  /* ---- safe localStorage (some browsers block it in private mode) -------- */
  function read(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) { return fallback; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
  }

  function emit() { listeners.forEach(function (fn) { try { fn(); } catch (e) {} }); }

  /* ---- cart --------------------------------------------------------------- */
  function getCart() { return read(CART_KEY, []); }

  function addItem(item) {
    var cart = getCart();
    // a line item is unique by service + tier
    var key = item.serviceId + "::" + item.tier;
    var existing = cart.find(function (i) { return i.key === key; });
    if (existing) {
      existing.qty += 1;
    } else {
      cart.push({
        key: key,
        serviceId: item.serviceId,
        service: item.service,
        tier: item.tier,
        price: item.price,
        delivery: item.delivery,
        qty: 1,
      });
    }
    write(CART_KEY, cart);
    emit();
  }

  function removeItem(key) {
    write(CART_KEY, getCart().filter(function (i) { return i.key !== key; }));
    emit();
  }

  function setQty(key, qty) {
    var cart = getCart();
    var item = cart.find(function (i) { return i.key === key; });
    if (!item) return;
    item.qty = Math.max(1, Math.min(99, qty | 0));
    write(CART_KEY, cart);
    emit();
  }

  function clearCart() { write(CART_KEY, []); emit(); }

  function cartCount() {
    return getCart().reduce(function (n, i) { return n + i.qty; }, 0);
  }
  function cartTotal() {
    return getCart().reduce(function (n, i) { return n + i.price * i.qty; }, 0);
  }

  /* ---- orders ------------------------------------------------------------- */
  function getOrders() { return read(ORDERS_KEY, []); }
  function getOrder(id) {
    return getOrders().find(function (o) {
      return o.id.toUpperCase() === String(id).trim().toUpperCase();
    });
  }

  function makeId() {
    var s = "";
    var chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"; // no ambiguous chars
    for (var i = 0; i < 6; i++) s += chars[(Math.random() * chars.length) | 0];
    return "ALR-" + s;
  }

  function placeOrder(customer) {
    var items = getCart();
    var order = {
      id: makeId(),
      items: items,
      total: cartTotal(),
      customer: {
        name: String(customer.name || "").slice(0, 120),
        email: String(customer.email || "").slice(0, 160),
        whatsapp: String(customer.whatsapp || "").slice(0, 40),
        notes: String(customer.notes || "").slice(0, 2000),
      },
      status: "Received",
      createdAt: new Date().toISOString(),
      timeline: [
        { status: "Received", at: new Date().toISOString(),
          note: "Order received. I'll confirm details with you shortly." },
      ],
    };
    var orders = getOrders();
    orders.unshift(order);
    write(ORDERS_KEY, orders.slice(0, 50)); // keep last 50
    clearCart();
    notify(order);
    return order;
  }

  /* ---- notify the freelancer (email via Formspree + WhatsApp link) -------- */
  function orderSummaryText(order) {
    var c = window.SITE_CONFIG;
    var lines = ["New order " + order.id, ""];
    order.items.forEach(function (i) {
      lines.push("• " + i.service + " — " + i.tier + " x" + i.qty +
        " (" + c.currency + (i.price * i.qty) + ")");
    });
    lines.push("", "Total: " + c.currency + order.total);
    lines.push("From: " + order.customer.name + " <" + order.customer.email + ">");
    if (order.customer.whatsapp) lines.push("WhatsApp: " + order.customer.whatsapp);
    if (order.customer.notes) lines.push("Notes: " + order.customer.notes);
    return lines.join("\n");
  }

  function whatsappLink(text) {
    var num = (window.SITE_CONFIG.whatsapp || "").replace(/\D/g, "");
    return "https://wa.me/" + num + "?text=" + encodeURIComponent(text);
  }

  function notify(order) {
    var id = window.SITE_CONFIG.formspreeId;
    if (!id) return; // not configured — orders still save + WhatsApp still works
    try {
      fetch("https://formspree.io/f/" + id, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          _subject: "New order " + order.id + " — " + window.SITE_CONFIG.brand,
          order_id: order.id,
          name: order.customer.name,
          email: order.customer.email,
          whatsapp: order.customer.whatsapp,
          notes: order.customer.notes,
          summary: orderSummaryText(order),
          total: window.SITE_CONFIG.currency + order.total,
        }),
      }).catch(function () {}); // fire-and-forget; WhatsApp is the reliable fallback
    } catch (e) {}
  }

  /* ---- generic message sender (custom request / contact form) ------------- */
  function sendMessage(payload) {
    var id = window.SITE_CONFIG.formspreeId;
    if (!id) return Promise.reject(new Error("no-endpoint"));
    return fetch("https://formspree.io/f/" + id, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    }).then(function (r) {
      if (!r.ok) throw new Error("bad-status");
      return r;
    });
  }

  function onChange(fn) { listeners.push(fn); }

  window.Store = {
    getCart: getCart, addItem: addItem, removeItem: removeItem, setQty: setQty,
    clearCart: clearCart, cartCount: cartCount, cartTotal: cartTotal,
    getOrders: getOrders, getOrder: getOrder, placeOrder: placeOrder,
    sendMessage: sendMessage, whatsappLink: whatsappLink,
    orderSummaryText: orderSummaryText, onChange: onChange,
  };
})();
