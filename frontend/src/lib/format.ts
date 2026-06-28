/* Small formatting / helper utilities shared across the app. */
import { CONFIG } from "./config";

export function money(n: number | string): string {
  return CONFIG.currency + Number(n || 0).toLocaleString();
}

export function fmtDate(iso?: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function validEmail(v: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

/** Trim long service titles for tabs / footers (port of shortTitle in app.js). */
export function shortTitle(t: string): string {
  return t
    .replace(/ in Python$/, "")
    .replace(/^Full-Stack /, "")
    .replace(/ for SaaS & Admin Dashboards/, "")
    .replace(/ for OCR & Data Scraping/, "")
    .replace(/^Premium Commercial /, "");
}

export function whatsappLink(text: string): string {
  const num = (CONFIG.whatsapp || "").replace(/\D/g, "");
  return "https://wa.me/" + num + "?text=" + encodeURIComponent(text);
}

export const csv = (s: string): string[] =>
  String(s || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
