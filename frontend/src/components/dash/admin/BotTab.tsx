/* Bot training tab — review unanswered questions and teach answers into the
   knowledge base (CRUD + enable/disable). Port of the Bot training tab in
   admin-dash.js. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "../../../lib/icons";
import { fmtDate } from "../../../lib/format";
import { API } from "../../../lib/api";
import type { ApiError, BotKnowledge, BotUnanswered } from "../../../lib/types";

export function BotTab({ onUnauth, onChanged }: { onUnauth: () => void; onChanged: () => void }) {
  const [unans, setUnans] = useState<BotUnanswered[] | null>(null);
  const [knowledge, setKnowledge] = useState<BotKnowledge[] | null>(null);
  const [q, setQ] = useState("");
  const [a, setA] = useState("");
  const [k, setK] = useState("");
  const [teachId, setTeachId] = useState<number | null>(null);
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const answerRef = useRef<HTMLTextAreaElement>(null);

  const loadUnans = useCallback(() => {
    API.get<BotUnanswered[]>("/api/admin/chat/unanswered")
      .then(setUnans)
      .catch((err: ApiError) => {
        if (err.status === 401 || err.status === 403) onUnauth();
      });
  }, [onUnauth]);
  const loadKnowledge = useCallback(() => {
    API.get<BotKnowledge[]>("/api/admin/chat/knowledge").then(setKnowledge).catch(() => {});
  }, []);

  useEffect(() => {
    loadUnans();
    loadKnowledge();
  }, [loadUnans, loadKnowledge]);

  function teach(u: BotUnanswered) {
    setQ(u.question);
    setTeachId(u.id);
    setTimeout(() => {
      answerRef.current?.focus();
      answerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 0);
  }

  function dismiss(id: number) {
    API.post("/api/admin/chat/unanswered/" + id + "/resolve")
      .then(() => {
        loadUnans();
        onChanged();
      })
      .catch((err: ApiError) => window.alert(err.message || "Failed."));
  }

  async function addKnowledge(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const question = q.trim();
    const answer = a.trim();
    if (!question || !answer) {
      setStatus({ type: "err", msg: "Both a question and an answer are required." });
      return;
    }
    try {
      await API.post("/api/admin/chat/knowledge", { question, answer, keywords: k.trim(), enabled: true });
      setQ("");
      setA("");
      setK("");
      setStatus({ type: "ok", msg: "Added! The bot now knows this. ✅" });
      if (teachId != null) {
        await API.post("/api/admin/chat/unanswered/" + teachId + "/resolve").catch(() => {});
        setTeachId(null);
      }
      loadKnowledge();
      loadUnans();
      onChanged();
    } catch (err) {
      setStatus({ type: "err", msg: (err as Error).message || "Failed." });
    }
  }

  function delKnowledge(id: number) {
    if (!window.confirm("Delete this answer?")) return;
    API.del("/api/admin/chat/knowledge/" + id).then(loadKnowledge).catch((err: ApiError) => window.alert(err.message || "Failed."));
  }
  function toggleKnowledge(row: BotKnowledge) {
    API.patch("/api/admin/chat/knowledge/" + row.id, {
      question: row.question,
      answer: row.answer,
      keywords: row.keywords || "",
      enabled: !row.enabled,
    })
      .then(loadKnowledge)
      .catch((err: ApiError) => window.alert(err.message || "Failed."));
  }

  return (
    <>
      <p className="form-note" style={{ marginBottom: "1rem" }}>
        Teach your assistant. It answers from your services automatically; add custom Q&amp;A here, and review questions
        it couldn't answer so you can teach it a reply. No third-party AI — everything stays first-party.
      </p>

      <div className="card" style={{ marginBottom: "1.2rem" }}>
        <h3 style={{ marginBottom: ".6rem" }}>Unanswered questions</h3>
        <p className="form-note" style={{ marginTop: 0 }}>
          Visitors asked these and the bot wasn't sure. Teach it an answer (adds it to the knowledge base) or dismiss.
        </p>
        <div id="unansList">
          {unans === null ? (
            <p className="form-note">Loading…</p>
          ) : unans.length === 0 ? (
            <p className="form-note">Nothing pending — the bot is handling everything. 🎉</p>
          ) : (
            unans.map((u) => (
              <div className="rev-item card" style={{ padding: ".9rem 1rem" }} key={u.id}>
                <div className="rev-top">
                  <div>
                    <b>{u.question}</b>
                    {u.count > 1 && <span className="status-chip st-received"> asked {u.count}×</span>}
                    <div style={{ color: "var(--muted)", fontSize: ".8rem" }}>last seen {fmtDate(u.last_seen)}</div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap", marginTop: ".5rem" }}>
                  <button className="btn btn-primary btn-sm" onClick={() => teach(u)}>Teach an answer</button>
                  <button className="btn btn-outline btn-sm" onClick={() => dismiss(u.id)}>Dismiss</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: ".6rem" }}>Knowledge base</h3>
        <form className="form" onSubmit={addKnowledge} noValidate style={{ marginBottom: "1rem" }}>
          <div className="field">
            <label htmlFor="kn-q">Question / trigger phrase</label>
            <input className="input" id="kn-q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. Do you offer hosting?" />
          </div>
          <div className="field">
            <label htmlFor="kn-a">Answer</label>
            <textarea className="textarea" id="kn-a" ref={answerRef} value={a} onChange={(e) => setA(e.target.value)} placeholder="What the bot should reply. **Bold** works." />
          </div>
          <div className="field">
            <label htmlFor="kn-k">Extra keywords <span style={{ color: "var(--muted)", fontWeight: 400 }}>(optional, comma-separated)</span></label>
            <input className="input" id="kn-k" value={k} onChange={(e) => setK(e.target.value)} placeholder="hosting, deploy, server, maintenance" />
          </div>
          {status && <div className={`dash-status show ${status.type}`}>{status.msg}</div>}
          <button className="btn btn-primary btn-sm" type="submit">
            <Icon name="plus" size={16} /> Add to knowledge base
          </button>
        </form>

        <div id="knList">
          {knowledge === null ? (
            <p className="form-note">Loading…</p>
          ) : knowledge.length === 0 ? (
            <p className="form-note">No custom answers yet. The bot still answers from your services, pricing and built-in common questions.</p>
          ) : (
            knowledge.map((row) => (
              <div className="rev-item card" style={{ padding: ".9rem 1rem" }} key={row.id}>
                <div className="rev-top">
                  <div>
                    <b>{row.question}</b>
                    {row.hits ? <span className="status-chip st-delivered"> {row.hits} hit{row.hits === 1 ? "" : "s"}</span> : null}
                    {!row.enabled && <span className="status-chip st-cancelled"> off</span>}
                  </div>
                </div>
                <p style={{ margin: ".4rem 0", color: "var(--muted)", whiteSpace: "pre-wrap" }}>{row.answer}</p>
                {row.keywords && <div style={{ color: "var(--muted)", fontSize: ".8rem" }}>keywords: {row.keywords}</div>}
                <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap", marginTop: ".5rem" }}>
                  <button className="btn btn-outline btn-sm" onClick={() => toggleKnowledge(row)}>{row.enabled ? "Disable" : "Enable"}</button>
                  <button className="btn btn-outline btn-sm" onClick={() => delKnowledge(row.id)}>Delete</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}
