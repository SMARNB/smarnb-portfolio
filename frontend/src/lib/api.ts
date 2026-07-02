/* =============================================================================
   Typed API client — port of assets/js/api.js. Bearer JWT in localStorage
   (keys alira_token / alira_user), same-origin (apiBase ""), error shape with
   .status. The single source of truth for talking to the FastAPI backend.
   ========================================================================== */
import { CONFIG } from "./config";
import type { ApiError, Token, User } from "./types";

const BASE = CONFIG.apiBase || "";
const TOKEN_KEY = "alira_token";
const USER_KEY = "alira_user";

function ls(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function getToken(): string {
  const s = ls();
  return s ? s.getItem(TOKEN_KEY) || "" : "";
}
export function setToken(t: string): void {
  const s = ls();
  if (!s) return;
  if (t) s.setItem(TOKEN_KEY, t);
  else s.removeItem(TOKEN_KEY);
}
export function getUser(): User | null {
  try {
    return JSON.parse(ls()!.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}
export function setUser(u: User | null): void {
  const s = ls();
  if (!s) return;
  if (u) s.setItem(USER_KEY, JSON.stringify(u));
  else s.removeItem(USER_KEY);
}

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

async function req<T = unknown>(method: Method, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const t = getToken();
  if (t) headers["Authorization"] = "Bearer " + t;

  const r = await fetch(BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const txt = await r.text();
  let data: unknown = null;
  if (txt) {
    try {
      data = JSON.parse(txt);
    } catch {
      data = txt;
    }
  }
  if (!r.ok) {
    const d = (data as { detail?: unknown })?.detail;
    const msg =
      typeof d === "string"
        ? d
        : Array.isArray(d) && (d[0] as { msg?: string })?.msg
          ? (d[0] as { msg: string }).msg
          : "Request failed (" + r.status + ")";
    const err = new Error(msg) as ApiError;
    err.status = r.status;
    throw err;
  }
  return data as T;
}

/** Multipart upload (a File under the "file" field). Mirrors req()'s error shape;
    the browser sets the multipart Content-Type/boundary, so we don't. */
async function uploadReq<T = unknown>(path: string, file: File): Promise<T> {
  const fd = new FormData();
  fd.append("file", file);
  const headers: Record<string, string> = {};
  const t = getToken();
  if (t) headers["Authorization"] = "Bearer " + t;
  const r = await fetch(BASE + path, { method: "POST", headers, body: fd });
  const txt = await r.text();
  let data: unknown = null;
  if (txt) {
    try {
      data = JSON.parse(txt);
    } catch {
      data = txt;
    }
  }
  if (!r.ok) {
    const d = (data as { detail?: unknown })?.detail;
    const msg = typeof d === "string" ? d : "Upload failed (" + r.status + ")";
    const err = new Error(msg) as ApiError;
    err.status = r.status;
    throw err;
  }
  return data as T;
}

function saveAuth(res: Token): Token {
  if (res && res.access_token) {
    setToken(res.access_token);
    setUser(res.user);
  }
  return res;
}

export const API = {
  base: BASE,
  getToken,
  setToken,
  getUser,
  setUser,
  isAuthed: () => !!getToken(),
  logout: () => {
    setToken("");
    setUser(null);
  },
  get: <T = unknown>(p: string) => req<T>("GET", p),
  post: <T = unknown>(p: string, b?: unknown) => req<T>("POST", p, b === undefined ? {} : b),
  put: <T = unknown>(p: string, b?: unknown) => req<T>("PUT", p, b === undefined ? {} : b),
  patch: <T = unknown>(p: string, b?: unknown) => req<T>("PATCH", p, b === undefined ? {} : b),
  del: <T = unknown>(p: string) => req<T>("DELETE", p),
  upload: <T = unknown>(p: string, file: File) => uploadReq<T>(p, file),
  register: (d: { email: string; password: string; name?: string; whatsapp?: string }) =>
    req<Token>("POST", "/api/auth/register", d).then(saveAuth),
  login: (d: { email: string; password: string; totp_code?: string }) =>
    req<Token>("POST", "/api/auth/login", d).then(saveAuth),
  me: () => req<User>("GET", "/api/auth/me"),
};
