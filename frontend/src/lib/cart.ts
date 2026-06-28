/* =============================================================================
   Cart + local orders + Formspree notify — port of assets/js/store.js. Cart and
   a copy of placed orders live in localStorage so visitors can track them even
   without an account; orders also go to the backend API + Formspree email.
   ========================================================================== */
import { CONFIG } from "./config";
import type { Order } from "./types";

const CART_KEY = "alira_cart_v1";
const ORDERS_KEY = "alira_orders_v1";

export interface CartItem {
  key: string;
  serviceId: string;
  service: string;
  tier: string;
  price: number;
  delivery: string;
  qty: number;
}

export interface LocalOrder {
  id: string;
  items: CartItem[];
  total: number;
  customer: { name: string; email: string; whatsapp: string; notes: string };
  payment_method: string;
  status: string;
  createdAt: string;
  timeline: { status: string; at: string; note: string }[];
}

export interface Customer {
  name: string;
  email: string;
  whatsapp?: string;
  notes?: string;
  payment_method?: string;
}

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}
function write(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore (private mode) */
  }
}

export const getCart = (): CartItem[] => read<CartItem[]>(CART_KEY, []);

export function writeCart(cart: CartItem[]): void {
  write(CART_KEY, cart);
}

export function addItem(item: Omit<CartItem, "key" | "qty">): CartItem[] {
  const cart = getCart();
  const key = item.serviceId + "::" + item.tier;
  const existing = cart.find((i) => i.key === key);
  if (existing) existing.qty += 1;
  else cart.push({ key, ...item, qty: 1 });
  writeCart(cart);
  return cart;
}

export function removeItem(key: string): CartItem[] {
  const cart = getCart().filter((i) => i.key !== key);
  writeCart(cart);
  return cart;
}

export function setQty(key: string, qty: number): CartItem[] {
  const cart = getCart();
  const item = cart.find((i) => i.key === key);
  if (item) item.qty = Math.max(1, Math.min(99, qty | 0));
  writeCart(cart);
  return cart;
}

export function clearCart(): CartItem[] {
  writeCart([]);
  return [];
}

export const cartCount = (cart: CartItem[]): number => cart.reduce((n, i) => n + i.qty, 0);
export const cartTotal = (cart: CartItem[]): number => cart.reduce((n, i) => n + i.price * i.qty, 0);

/* ---- local orders ---- */
export const getOrders = (): LocalOrder[] => read<LocalOrder[]>(ORDERS_KEY, []);
export const getOrder = (id: string): LocalOrder | undefined =>
  getOrders().find((o) => o.id.toUpperCase() === String(id).trim().toUpperCase());

function makeId(): string {
  const chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
  let s = "";
  for (let i = 0; i < 6; i++) s += chars[(Math.random() * chars.length) | 0];
  return "ALR-" + s;
}

export function orderSummaryText(order: LocalOrder): string {
  const c = CONFIG;
  const lines = ["New order " + order.id, ""];
  order.items.forEach((i) => {
    lines.push("• " + i.service + " — " + i.tier + " x" + i.qty + " (" + c.currency + i.price * i.qty + ")");
  });
  lines.push("", "Total: " + c.currency + order.total);
  if (order.payment_method) lines.push("Payment: " + order.payment_method);
  lines.push("From: " + order.customer.name + " <" + order.customer.email + ">");
  if (order.customer.whatsapp) lines.push("WhatsApp: " + order.customer.whatsapp);
  if (order.customer.notes) lines.push("Notes: " + order.customer.notes);
  return lines.join("\n");
}

function notify(order: LocalOrder): void {
  const id = CONFIG.formspreeId;
  if (!id) return;
  try {
    fetch("https://formspree.io/f/" + id, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        _subject: "New order " + order.id + " — " + CONFIG.brand,
        order_id: order.id,
        name: order.customer.name,
        email: order.customer.email,
        whatsapp: order.customer.whatsapp,
        notes: order.customer.notes,
        payment: order.payment_method || "",
        summary: orderSummaryText(order),
        total: CONFIG.currency + order.total,
        _gotcha: "",
      }),
    }).catch(() => {});
  } catch {
    /* ignore */
  }
}

/** Save an order locally (offline / API-down fallback). */
export function placeOrder(customer: Customer): LocalOrder {
  const items = getCart();
  const order: LocalOrder = {
    id: makeId(),
    items,
    total: cartTotal(items),
    customer: {
      name: String(customer.name || "").slice(0, 120),
      email: String(customer.email || "").slice(0, 160),
      whatsapp: String(customer.whatsapp || "").slice(0, 40),
      notes: String(customer.notes || "").slice(0, 2000),
    },
    payment_method: String(customer.payment_method || "").slice(0, 60),
    status: "Received",
    createdAt: new Date().toISOString(),
    timeline: [
      { status: "Received", at: new Date().toISOString(), note: "Order received. I'll confirm details with you shortly." },
    ],
  };
  const orders = getOrders();
  orders.unshift(order);
  write(ORDERS_KEY, orders.slice(0, 50));
  clearCart();
  notify(order);
  return order;
}

/** Place an order via the backend API (so it lands in the dashboard). Saves a
   local copy + emails via Formspree as a backup. Throws on network/API failure. */
export async function placeOrderViaApi(customer: Customer): Promise<LocalOrder> {
  const base = CONFIG.apiBase || "";
  const snapshot = getCart();
  const items = snapshot.map((i) => ({ service: i.service, tier: i.tier, price: i.price, qty: i.qty }));
  const r = await fetch(base + "/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      customer_name: customer.name,
      customer_email: customer.email,
      customer_whatsapp: customer.whatsapp || "",
      notes: customer.notes || "",
      payment_method: customer.payment_method || "",
      items,
    }),
  });
  if (!r.ok) throw new Error("api " + r.status);
  const server = (await r.json()) as Order;
  const order: LocalOrder = {
    id: server.public_id,
    items: snapshot,
    total: server.total,
    customer: {
      name: customer.name,
      email: customer.email,
      whatsapp: customer.whatsapp || "",
      notes: customer.notes || "",
    },
    payment_method: customer.payment_method || "",
    status: server.status,
    createdAt: server.created_at,
    timeline: (server.updates || []).map((u) => ({
      status: u.status || server.status,
      at: u.created_at,
      note: u.message,
    })),
  };
  const orders = getOrders();
  orders.unshift(order);
  write(ORDERS_KEY, orders.slice(0, 50));
  clearCart();
  notify(order);
  return order;
}

/** Send a generic message (custom request / contact form) via Formspree. */
export function sendMessage(payload: Record<string, unknown>): Promise<Response> {
  const id = CONFIG.formspreeId;
  if (!id) return Promise.reject(new Error("no-endpoint"));
  return fetch("https://formspree.io/f/" + id, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  }).then((r) => {
    if (!r.ok) throw new Error("bad-status");
    return r;
  });
}
