/* Floating chat assistant + live chat — React port of assets/js/chat.js. The bot
   answers instantly from the catalog; the developer can take over from the Inbox.
   Accepts image/PDF uploads, persists the per-thread secret in localStorage, polls
   for replies, and degrades to WhatsApp/email when the backend is unreachable.
   A single instance lives in the layout (no double-mount, no stacked pollers). */
import { useCallback, useEffect, useRef, useState } from "react";
import { motion, useMotionValue } from "framer-motion";
import { CONFIG } from "../../lib/config";
import { API } from "../../lib/api";
import type { ApiError, ChatMessage, ChatThread } from "../../lib/types";

const LS_KEY = "alira_chat";
const POLL_OPEN = 4000;
const POLL_IDLE = 20000;
const BASE = CONFIG.apiBase || "";
const CHAT = CONFIG.chat;

const ICON_CHAT = (
  <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 8.5 8.5 0 0 1-3.8-.9L3 21l1.9-5.7A8.38 8.38 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.38 8.38 0 0 1 21 11.5z" />
  </svg>
);
const ICON_CLOSE = (
  <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);
const ICON_SEND = (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);
const ICON_CLIP = (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
  </svg>
);
const ICON_PLUS = (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);
const ICON_HISTORY = (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 3v5h5" /><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8" /><path d="M12 7v5l3 2" />
  </svg>
);
const ICON_BACK = (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
  </svg>
);

interface ClientChatSummary {
  public_id: string;
  status: string;
  last_message: string;
  last_message_at: string;
  messages: number;
}

function escapeHtml(s: string): string {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}
function md(s: string): string {
  let h = escapeHtml(s);
  h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  h = h.replace(/\n/g, "<br>");
  return h;
}
function loadSaved(): { conv: string | null; secret: string | null } | null {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) || "null");
  } catch {
    return null;
  }
}

export function ChatWidget() {
  if (CHAT.enabled === false) return null;
  return <ChatWidgetInner />;
}

function ChatWidgetInner() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<ChatMessage[]>([]);
  const [quick, setQuick] = useState<string[]>([]);
  const [human, setHuman] = useState(false);
  const [down, setDown] = useState(false);
  const [unread, setUnread] = useState(0);
  const [typing, setTyping] = useState(false);
  const [text, setText] = useState("");
  const [view, setView] = useState<"chat" | "list">("chat");
  const [history, setHistory] = useState<ClientChatSummary[] | null>(null);
  const loggedIn = !!API.getUser();

  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== "undefined" && window.innerWidth <= 480
  );

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 480);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Mutable refs (don't trigger re-render; mirror the vanilla `S` object).
  const conv = useRef<string | null>(null);
  const secret = useRef<string | null>(null);
  const started = useRef(false);
  const starting = useRef(false);
  const sending = useRef(false);
  const lastSeen = useRef(0);
  const openRef = useRef(false);
  const timer = useRef<number | null>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const save = () => {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify({ conv: conv.current, secret: secret.current }));
    } catch {
      /* ignore */
    }
  };
  const reset = () => {
    conv.current = null;
    secret.current = null;
    started.current = false;
    setMsgs([]);
    try {
      localStorage.removeItem(LS_KEY);
    } catch {
      /* ignore */
    }
  };

  const api = useCallback(
    async <T,>(method: string, path: string, body?: unknown, isForm = false): Promise<T> => {
      const headers: Record<string, string> = { Accept: "application/json" };
      if (secret.current) headers["X-Chat-Secret"] = secret.current;
      const t = API.getToken();
      if (t) headers["Authorization"] = "Bearer " + t;
      const opt: RequestInit = { method, headers };
      if (body !== undefined) {
        if (isForm) opt.body = body as FormData;
        else {
          headers["Content-Type"] = "application/json";
          opt.body = JSON.stringify(body);
        }
      }
      const r = await fetch(BASE + path, opt);
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
        const e = new Error(typeof d === "string" ? d : "Request failed") as ApiError;
        e.status = r.status;
        throw e;
      }
      return data as T;
    },
    [],
  );

  const applyThread = useCallback((res: ChatThread | { messages: ChatMessage[]; quick_replies: string[]; human_takeover: boolean; needs_human: boolean }) => {
    if (!res) return;
    setMsgs(res.messages || []);
    setQuick(res.quick_replies || []);
    setHuman(!!res.human_takeover);
    lastSeen.current = (res.messages || []).length;
    setUnread(0);
  }, []);

  const flagUnread = useCallback((res: ChatThread) => {
    const m = res.messages || [];
    const incoming = m.filter((x) => x.sender !== "client").length;
    if (m.length > lastSeen.current && incoming) {
      setUnread(m.length - lastSeen.current);
    }
    setMsgs(m);
  }, []);

  const fetchThread = useCallback(async () => {
    if (!conv.current) return;
    try {
      const res = await api<ChatThread>("GET", "/api/chat/" + encodeURIComponent(conv.current));
      setDown(false);
      if (!openRef.current) flagUnread(res);
      else applyThread(res);
    } catch (e) {
      const err = e as ApiError;
      if (err.status === 403 || err.status === 404) reset();
      else setDown(true);
    }
  }, [api, applyThread, flagUnread]);

  const restartPoll = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    if (!started.current && !conv.current) return;
    const every = openRef.current ? POLL_OPEN : POLL_IDLE;
    timer.current = window.setInterval(() => {
      if (sending.current) return;
      fetchThread();
    }, every);
  }, [fetchThread]);

  const ensureStarted = useCallback(async () => {
    if (started.current && conv.current) return fetchThread();
    if (starting.current) return;
    starting.current = true;
    const u = API.getUser();
    try {
      const res = await api<ChatThread>("POST", "/api/chat/start", {
        name: u?.name || "",
        email: u?.email || "",
      });
      conv.current = res.public_id;
      secret.current = res.secret || null;
      started.current = true;
      setDown(false);
      save();
      applyThread(res);
    } catch {
      setDown(true);
    } finally {
      starting.current = false;
    }
  }, [api, applyThread, fetchThread]);

  // Archive the current thread (kept server-side) and start a fresh one.
  const newConversation = useCallback(async () => {
    if (conv.current) {
      try {
        await api("POST", "/api/chat/" + encodeURIComponent(conv.current) + "/end");
      } catch {
        /* best effort */
      }
    }
    reset();
    setView("chat");
    await ensureStarted();
    restartPoll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, ensureStarted, restartPoll]);

  // Signed-in clients only: list their past threads to resume one.
  const openHistory = useCallback(async () => {
    setHistory(null);
    setView("list");
    try {
      setHistory(await api<ClientChatSummary[]>("GET", "/api/chat/mine"));
    } catch {
      setHistory([]);
    }
  }, [api]);

  const resumeConv = useCallback(
    async (pid: string) => {
      conv.current = pid;
      secret.current = null;
      started.current = true;
      setView("chat");
      try {
        const res = await api<ChatThread>("GET", "/api/chat/" + encodeURIComponent(pid));
        if (res.secret) secret.current = res.secret;
        setDown(false);
        applyThread(res);
        save();
      } catch {
        setDown(true);
      }
      restartPoll();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    },
    [api, applyThread, restartPoll],
  );

  const sendText = useCallback(
    async (override?: string) => {
      const msg = (override != null ? override : text).trim();
      if (!msg || sending.current) return;
      if (down || !started.current) {
        ensureStarted();
        return;
      }
      sending.current = true;
      setText("");
      setMsgs((m) => [...m, { sender: "client", body: msg }]);
      setQuick([]);
      setTyping(true);
      try {
        const res = await api<ChatThread>("POST", "/api/chat/" + encodeURIComponent(conv.current!) + "/messages", { body: msg });
        applyThread(res);
      } catch (e) {
        const err = e as ApiError;
        if (err.status === 403 || err.status === 404) reset();
      } finally {
        setTyping(false);
        sending.current = false;
      }
    },
    [text, down, ensureStarted, api, applyThread],
  );

  const onFile = useCallback(
    async (f: File | undefined) => {
      if (!f) return;
      if (f.size > 10 * 1024 * 1024) return;
      const doUpload = async () => {
        const fd = new FormData();
        fd.append("file", f);
        setMsgs((m) => [...m, { sender: "client", body: "📎 " + f.name }]);
        setTyping(true);
        try {
          const res = await api<ChatThread>("POST", "/api/chat/" + encodeURIComponent(conv.current!) + "/upload", fd, true);
          applyThread(res);
        } catch {
          /* ignore */
        } finally {
          setTyping(false);
        }
      };
      if (down || !started.current) {
        await ensureStarted();
      }
      if (conv.current) doUpload();
    },
    [api, applyThread, down, ensureStarted],
  );

  // Resume idle polling on mount if a saved thread exists.
  useEffect(() => {
    const saved = loadSaved();
    if (saved && saved.conv && (saved.secret || API.getToken())) {
      conv.current = saved.conv;
      secret.current = saved.secret;
      started.current = true;
      restartPoll();
    }
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll the body as messages arrive.
  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [msgs, typing]);

  const toggle = () => {
    const next = !open;
    setOpen(next);
    openRef.current = next;
    if (next) {
      setUnread(0);
      ensureStarted();
    }
    restartPoll();
  };

  const attUrl = (a: NonNullable<ChatMessage["attachment"]>) =>
    BASE + "/api/chat/" + encodeURIComponent(conv.current || "") + "/attachments/" + a.id + "?s=" + encodeURIComponent(secret.current || "");

  const wa = (CONFIG.whatsapp || "").replace(/\D/g, "");

  return (
    <>
      <motion.button 
        className={`chat-launcher${open ? " open" : ""}`} 
        aria-label="Open chat" 
        onClick={toggle}
        drag
        dragMomentum={false}
        style={{ x, y }}
      >
        {open ? ICON_CLOSE : ICON_CHAT}
        {!open && unread > 0 && <span className="chat-dot">{unread > 9 ? "9+" : unread}</span>}
      </motion.button>

      <motion.div 
        className="chat-panel" 
        role="dialog" 
        aria-label="Chat" 
        hidden={!open}
        style={isMobile ? undefined : { x, y }}
      >
        <div className="chat-head">
          <div className="chat-head-main">
            <span className="chat-avatar">{CONFIG.initials || "AI"}</span>
            <div>
              <b>{CHAT.title || "Chat with us"}</b>
              <small>{human ? `${CONFIG.name || "Developer"} is in the chat` : CHAT.subtitle || "We usually reply fast"}</small>
            </div>
          </div>
          <div className="chat-head-actions">
            {view === "list" ? (
              <button className="chat-x" aria-label="Back to chat" title="Back" onClick={() => setView("chat")}>
                {ICON_BACK}
              </button>
            ) : (
              <>
                <button className="chat-x" aria-label="Start a new conversation" title="New conversation" onClick={newConversation}>
                  {ICON_PLUS}
                </button>
                {loggedIn && (
                  <button className="chat-x" aria-label="Past conversations" title="Past conversations" onClick={openHistory}>
                    {ICON_HISTORY}
                  </button>
                )}
              </>
            )}
            <button className="chat-x" aria-label="Close chat" onClick={toggle}>
              {ICON_CLOSE}
            </button>
          </div>
        </div>

        <div className="chat-body" id="chat-body" ref={bodyRef}>
          {view === "list" ? (
            <div className="chat-history">
              {history === null && <p className="chat-hist-empty">Loading…</p>}
              {history && history.length === 0 && (
                <p className="chat-hist-empty">No past conversations yet — start chatting and they'll show up here.</p>
              )}
              {history &&
                history.map((h) => (
                  <button className="chat-hist-item" key={h.public_id} onClick={() => resumeConv(h.public_id)}>
                    <span className="chat-hist-msg">{h.last_message || "New conversation"}</span>
                    <span className="chat-hist-meta">
                      {h.status === "closed" ? "Ended" : "Active"} · {new Date(h.last_message_at).toLocaleDateString()}
                    </span>
                  </button>
                ))}
            </div>
          ) : (
          <>
          {down ? (
            <div className="chat-msg them">
              <div className="bubble">
                Hi! 👋 Our live assistant is offline right now, but you can reach {CONFIG.name || "us"} directly:
              </div>
            </div>
          ) : (
            msgs.map((m, i) => {
              const side = m.sender === "client" ? "me" : "them";
              return (
                <div className={`chat-msg ${side}${m.sender === "bot" ? " bot" : ""}`} key={m.id ?? `o${i}`}>
                  {m.sender === "dev" && <span className="chat-by">{CONFIG.name || "Developer"}</span>}
                  {m.attachment ? (
                    (m.attachment.content_type || "").indexOf("image/") === 0 ? (
                      <a href={attUrl(m.attachment)} target="_blank" rel="noopener">
                        <img className="chat-img" src={attUrl(m.attachment)} alt={m.attachment.filename} />
                      </a>
                    ) : (
                      <a className="chat-file" href={attUrl(m.attachment)} target="_blank" rel="noopener">
                        📄 {m.attachment.filename}
                      </a>
                    )
                  ) : (
                    <div className="bubble" dangerouslySetInnerHTML={{ __html: md(m.body) }} />
                  )}
                </div>
              );
            })
          )}
          {typing && (
            <div className="chat-msg them">
              <div className="bubble chat-typing">
                <span /><span /><span />
              </div>
            </div>
          )}
          </>
          )}
        </div>

        {view === "chat" && (
          <>
        <div className="chat-quick" id="chat-quick">
          {down ? (
            <>
              {wa && (
                <a className="chat-chip" href={`https://wa.me/${wa}`} target="_blank" rel="noopener">
                  💬 WhatsApp
                </a>
              )}
              {CONFIG.email && (
                <a className="chat-chip" href={`mailto:${CONFIG.email}`}>
                  ✉️ Email
                </a>
              )}
              <a className="chat-chip" href="/contact">
                📝 Custom request
              </a>
            </>
          ) : (
            quick.map((q, i) => (
              <button type="button" className="chat-chip" key={i} onClick={() => sendText(q)}>
                {q}
              </button>
            ))
          )}
        </div>

        <form
          className="chat-input"
          onSubmit={(e) => {
            e.preventDefault();
            sendText();
          }}
        >
          <button type="button" className="chat-clip" aria-label="Attach a file (image or PDF)" onClick={() => fileRef.current?.click()}>
            {ICON_CLIP}
          </button>
          <input
            type="file"
            ref={fileRef}
            accept="image/png,image/jpeg,image/gif,image/webp,application/pdf"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              e.target.value = "";
              onFile(f);
            }}
          />
          <textarea
            rows={1}
            placeholder="Type a message…"
            aria-label="Message"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendText();
              }
            }}
          />
          <button type="submit" className="chat-send" aria-label="Send">
            {ICON_SEND}
          </button>
        </form>
        <div className="chat-foot">Files: images &amp; PDF only · powered by {CONFIG.brand || "us"}</div>
          </>
        )}
      </motion.div>
    </>
  );
}
