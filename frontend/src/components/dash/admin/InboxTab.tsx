/* Inbox tab — live chat. Conversation list with unread/needs-you badges, the
   thread (bot/client/dev bubbles), reply with optional "let the bot resume", a
   bot pause toggle and attachment rendering. Port of the Inbox tab in
   admin-dash.js. Polls the open thread every 5s.

   Admin attachment blobs are fetched (with the admin bearer token) from
   /api/admin/chat/attachments/{id}, which serves the bytes to the developer for
   any conversation — this is what renders the image/PDF previews below. */
import { useCallback, useEffect, useRef, useState } from "react";
import { CONFIG } from "../../../lib/config";
import { fmtDate } from "../../../lib/format";
import { API } from "../../../lib/api";
import type { ApiError, ChatMessage, ConversationSummary } from "../../../lib/types";

interface AdminThread {
  public_id: string;
  customer_name: string;
  customer_email: string;
  status: string;
  human_takeover: boolean;
  needs_human: boolean;
  messages: ChatMessage[];
}

function mdLite(s: string): string {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  let h = d.innerHTML;
  h = h.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  return h.replace(/\n/g, "<br>");
}

function authedBlob(path: string): Promise<Blob> {
  return fetch((CONFIG.apiBase || "") + path, {
    headers: { Authorization: "Bearer " + API.getToken() },
  }).then((r) => {
    if (!r.ok) throw new Error("load failed");
    return r.blob();
  });
}

export function InboxTab({
  onUnauth,
  list,
  reloadList,
  onActivity,
}: {
  onUnauth: () => void;
  list: ConversationSummary[] | null;
  reloadList: () => void;
  onActivity: () => void;
}) {
  const [selectedCid, setSelectedCid] = useState<string | null>(null);
  const [thread, setThread] = useState<AdminThread | null>(null);
  const convTimer = useRef<number | null>(null);

  const loadThread = useCallback(
    (cid: string) => {
      API.get<AdminThread>("/api/admin/chat/conversations/" + encodeURIComponent(cid))
        .then(setThread)
        .catch(() => {});
    },
    [],
  );

  const openConv = useCallback(
    (cid: string) => {
      setSelectedCid(cid);
      if (convTimer.current) clearInterval(convTimer.current);
      loadThread(cid);
      convTimer.current = window.setInterval(() => loadThread(cid), 5000);
    },
    [loadThread],
  );

  useEffect(() => {
    return () => {
      if (convTimer.current) clearInterval(convTimer.current);
    };
  }, []);

  // Surface a load error / auth expiry from the list fetch.
  useEffect(() => {
    if (list === null) {
      API.get("/api/admin/chat/conversations").catch((err: ApiError) => {
        if (err.status === 401 || err.status === 403) onUnauth();
      });
    }
  }, [list, onUnauth]);

  return (
    <div className="admin-grid">
      <div className="order-rows" id="convRows">
        {list === null ? (
          <p className="form-note">Loading…</p>
        ) : list.length === 0 ? (
          <p className="form-note">No conversations yet.</p>
        ) : (
          list.map((c) => (
            <button
              key={c.public_id}
              className={`order-row${selectedCid === c.public_id ? " active" : ""}`}
              onClick={() => openConv(c.public_id)}
            >
              <div className="r1">
                <span className="oid">{c.customer_name || c.customer_email || "Visitor"}</span>
                {c.unread ? (
                  <span className="status-chip" style={{ background: "var(--accent-3)", color: "#fff" }}>
                    {c.unread} new
                  </span>
                ) : c.needs_human ? (
                  <span className="status-chip st-received">needs you</span>
                ) : null}
              </div>
              <div className="who">{c.last_message || "…"}</div>
              <div className="r2" style={{ justifyContent: "space-between" }}>
                <small style={{ color: "var(--muted)" }}>{fmtDate(c.last_message_at)}</small>
                {c.human_takeover ? (
                  <small style={{ color: "var(--accent-2)" }}>live</small>
                ) : (
                  <small style={{ color: "var(--muted-2)" }}>bot</small>
                )}
              </div>
            </button>
          ))
        )}
      </div>

      <div id="convThread">
        {thread ? (
          <ConvThread
            thread={thread}
            onSent={() => {
              loadThread(thread.public_id);
              reloadList();
              onActivity();
            }}
            onToggleBot={() => loadThread(thread.public_id)}
          />
        ) : (
          <div className="card manage">
            <div className="empty">Select a conversation to read &amp; reply. The bot handles chats until you jump in.</div>
          </div>
        )}
      </div>
    </div>
  );
}

function ConvThread({
  thread,
  onSent,
  onToggleBot,
}: {
  thread: AdminThread;
  onSent: () => void;
  onToggleBot: () => void;
}) {
  const [reply, setReply] = useState("");
  const [resume, setResume] = useState(false);
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [thread.messages]);

  function send() {
    const msg = reply.trim();
    if (!msg) {
      setStatus({ type: "err", msg: "Write a reply first." });
      return;
    }
    setStatus({ type: "ok", msg: "Sending…" });
    API.post("/api/admin/chat/conversations/" + encodeURIComponent(thread.public_id) + "/messages", {
      body: msg,
      let_bot_resume: resume,
    })
      .then(() => {
        setReply("");
        setStatus({ type: "ok", msg: "Sent." });
        onSent();
      })
      .catch((err: ApiError) => setStatus({ type: "err", msg: err.message || "Failed." }));
  }

  function toggleBot() {
    API.post("/api/admin/chat/conversations/" + encodeURIComponent(thread.public_id) + "/bot", {})
      .then(onToggleBot)
      .catch(() => {});
  }

  return (
    <div className="card manage">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: ".5rem", flexWrap: "wrap" }}>
        <h3 style={{ margin: 0 }}>{thread.customer_name || "Visitor"}</h3>
        <button className="btn btn-outline btn-sm" onClick={toggleBot}>
          Bot: {thread.human_takeover ? "paused" : "active"}
        </button>
      </div>
      <p className="sub">
        {thread.customer_email || "no email on file"}
        {thread.needs_human && (
          <>
            {" "}· <b style={{ color: "var(--accent-3)" }}>asked for a human</b>
          </>
        )}
      </p>
      <div className="adm-chat" id="admChat" ref={chatRef}>
        {thread.messages.map((m, i) => (
          <AdmMessage key={m.id ?? i} m={m} />
        ))}
      </div>
      {status && <div className={`dash-status show ${status.type}`}>{status.msg}</div>}
      <div className="field">
        <textarea className="textarea" placeholder="Reply to the client…" value={reply} onChange={(e) => setReply(e.target.value)} />
      </div>
      <label style={{ display: "flex", alignItems: "center", gap: ".5rem", fontSize: ".84rem", color: "var(--muted)", marginBottom: ".6rem" }}>
        <input type="checkbox" checked={resume} onChange={(e) => setResume(e.target.checked)} /> Let the bot keep
        auto-answering after my reply
      </label>
      <button className="btn btn-primary btn-block" onClick={send}>
        Send reply
      </button>
    </div>
  );
}

function AdmMessage({ m }: { m: ChatMessage }) {
  const who = m.sender === "dev" ? "me" : "them";
  const label = m.sender === "bot" ? "Bot" : m.sender === "client" ? "Client" : "";
  return (
    <div className={`adm-msg ${who}${m.sender === "bot" ? " bot" : ""}`}>
      {label && <span className="adm-who">{label}</span>}
      <div className="adm-bubble">
        {m.attachment ? (
          (m.attachment.content_type || "").indexOf("image/") === 0 ? (
            <AdmImage attId={m.attachment.id} filename={m.attachment.filename} />
          ) : (
            <AdmFileButton attId={m.attachment.id} filename={m.attachment.filename} />
          )
        ) : (
          <span dangerouslySetInnerHTML={{ __html: mdLite(m.body) }} />
        )}
      </div>
    </div>
  );
}

function AdmImage({ attId, filename }: { attId: number; filename: string }) {
  const [url, setUrl] = useState<string>("");
  useEffect(() => {
    let obj = "";
    authedBlob("/api/admin/chat/attachments/" + attId)
      .then((b) => {
        obj = URL.createObjectURL(b);
        setUrl(obj);
      })
      .catch(() => {});
    return () => {
      if (obj) URL.revokeObjectURL(obj);
    };
  }, [attId]);
  return (
    <img
      className="adm-att"
      src={url || undefined}
      alt={filename}
      style={{ cursor: url ? "pointer" : "default" }}
      onClick={() => url && window.open(url, "_blank")}
    />
  );
}

function AdmFileButton({ attId, filename }: { attId: number; filename: string }) {
  return (
    <button
      className="btn btn-outline btn-sm"
      onClick={() => {
        authedBlob("/api/admin/chat/attachments/" + attId)
          .then((b) => window.open(URL.createObjectURL(b), "_blank"))
          .catch(() => window.alert("Could not load file."));
      }}
    >
      📄 {filename}
    </button>
  );
}
