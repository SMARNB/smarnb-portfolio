/* Admin "Email" tab — outbound email control room. Shows transport status
   (SendGrid on Render / SMTP elsewhere; secrets stay in env), lets the owner
   edit the customer-visible sender (name / from / reply-to — update here when
   the custom domain arrives, no redeploy), send a test, compose promotional
   campaigns (markdown), and audit the recent send log. */
import { useCallback, useEffect, useState } from "react";
import { API } from "../../../lib/api";
import type { ApiError } from "../../../lib/types";
import { fmtDay } from "../../../lib/format";

interface EmailStatus {
  enabled: boolean;
  transport: string;
  sendgrid_configured: boolean;
  smtp_configured: boolean;
  env_from: string;
  note: string;
  settings: {
    from_name: string;
    from_email: string;
    reply_to: string;
    bcc_owner: boolean;
    invoice_footer: string;
    promo_footer: string;
  };
}
interface LogRow {
  id: number;
  kind: string;
  to: string;
  subject: string;
  ok: boolean;
  error: string;
  created_at: string;
}

export function EmailTab({ onUnauth }: { onUnauth: () => void }) {
  const [st, setSt] = useState<EmailStatus | null>(null);
  const [log, setLog] = useState<LogRow[]>([]);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [camp, setCamp] = useState({ subject: "", body_md: "" });
  const [sending, setSending] = useState(false);

  const fail = useCallback(
    (e: unknown) => {
      const err = e as ApiError;
      if (err.status === 401) onUnauth();
      else setStatus({ type: "err", msg: err.message || "Something went wrong." });
    },
    [onUnauth],
  );

  const load = useCallback(() => {
    API.get<EmailStatus>("/api/admin/email/settings").then(setSt).catch(fail);
    API.get<{ log: LogRow[] }>("/api/admin/email/log").then((r) => setLog(r.log)).catch(() => {});
  }, [fail]);

  useEffect(() => {
    load();
  }, [load]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!st) return;
    setSaving(true);
    try {
      const r = await API.put<EmailStatus>("/api/admin/email/settings", st.settings);
      setSt(r);
      setStatus({ type: "ok", msg: "Sender settings saved." });
    } catch (err) {
      fail(err);
    } finally {
      setSaving(false);
    }
  }

  async function testSend() {
    try {
      const r = await API.post<{ to: string }>("/api/admin/email/test");
      setStatus({ type: "ok", msg: `Test email sent to ${r.to} — check the inbox.` });
      load();
    } catch (e) {
      fail(e);
    }
  }

  async function campaign(testOnly: boolean) {
    if (!camp.subject.trim() || !camp.body_md.trim()) {
      setStatus({ type: "err", msg: "Give the campaign a subject and a body." });
      return;
    }
    if (!testOnly && !window.confirm("Send this campaign to ALL subscribed clients?")) return;
    setSending(true);
    try {
      const r = await API.post<{ sent: number; skipped: number }>("/api/admin/email/campaign", {
        ...camp,
        test_only: testOnly,
      });
      setStatus({
        type: "ok",
        msg: testOnly
          ? "Preview sent to your own inbox."
          : `Campaign sent to ${r.sent} client${r.sent === 1 ? "" : "s"} (${r.skipped} unsubscribed/skipped).`,
      });
      if (!testOnly) setCamp({ subject: "", body_md: "" });
      load();
    } catch (e) {
      fail(e);
    } finally {
      setSending(false);
    }
  }

  const set = (k: keyof EmailStatus["settings"], v: string | boolean) =>
    st && setSt({ ...st, settings: { ...st.settings, [k]: v } });

  return (
    <div>
      <div className="dash-head">
        <div>
          <h1>Email</h1>
          <p>Invoices, receipts and promotional campaigns — sent from your own address.</p>
        </div>
      </div>

      {status && (
        <div className={`dash-status show ${status.type}`} role="status">
          {status.msg}
        </div>
      )}

      {!st && <p className="form-note">Loading…</p>}

      {st && (
        <>
          <div className={`dash-status show ${st.enabled ? "ok" : "err"}`} style={{ marginBottom: "1rem" }}>
            {st.enabled
              ? `Email is ON via ${st.transport === "sendgrid" ? "SendGrid" : "SMTP"} — invoices send automatically when orders are paid.`
              : "Email is OFF. Add SENDGRID_API_KEY + EMAIL_FROM in Render → Environment to turn it on (free tier ≈100/day). " + st.note}
          </div>

          <form className="form card" onSubmit={save} style={{ padding: "1.2rem", marginBottom: "1.4rem" }}>
            <h3 style={{ fontSize: "1.05rem" }}>Sender (what customers see)</h3>
            <p className="form-note" style={{ marginTop: "-.4rem" }}>
              Bought your domain? Update the address here — no redeploy needed. (With SendGrid,
              also verify the new sender/domain in the SendGrid dashboard.)
            </p>
            <div className="two">
              <div className="field">
                <label>From name</label>
                <input className="input" value={st.settings.from_name}
                       onChange={(e) => set("from_name", e.target.value)} />
              </div>
              <div className="field">
                <label>From email {st.env_from ? `(env default: ${st.env_from})` : ""}</label>
                <input className="input" value={st.settings.from_email}
                       onChange={(e) => set("from_email", e.target.value)}
                       placeholder="you@yourdomain.com" />
              </div>
            </div>
            <div className="two">
              <div className="field">
                <label>Reply-to (optional)</label>
                <input className="input" value={st.settings.reply_to}
                       onChange={(e) => set("reply_to", e.target.value)} />
              </div>
              <div className="field">
                <label style={{ display: "flex", gap: ".5rem", alignItems: "center", marginTop: "1.7rem" }}>
                  <input type="checkbox" checked={st.settings.bcc_owner}
                         onChange={(e) => set("bcc_owner", e.target.checked)} />
                  Send me a copy of every invoice
                </label>
              </div>
            </div>
            <div className="field">
              <label>Invoice footer (payment instructions on unpaid invoices)</label>
              <textarea className="textarea" style={{ minHeight: 70 }} value={st.settings.invoice_footer}
                        onChange={(e) => set("invoice_footer", e.target.value)} />
            </div>
            <div className="field">
              <label>Promo footer (shown above the unsubscribe link)</label>
              <textarea className="textarea" style={{ minHeight: 56 }} value={st.settings.promo_footer}
                        onChange={(e) => set("promo_footer", e.target.value)} />
            </div>
            <div style={{ display: "flex", gap: ".6rem" }}>
              <button className="btn btn-primary btn-sm" disabled={saving}>
                {saving ? "Saving…" : "Save sender settings"}
              </button>
              <button type="button" className="btn btn-ghost btn-sm" disabled={!st.enabled} onClick={testSend}>
                Send a test to me
              </button>
            </div>
          </form>

          <div className="form card" style={{ padding: "1.2rem", marginBottom: "1.4rem", display: "grid", gap: "1rem" }}>
            <h3 style={{ fontSize: "1.05rem" }}>Promotional campaign</h3>
            <p className="form-note" style={{ marginTop: "-.6rem" }}>
              Announce new services or offers to every signed-up client (unsubscribers are skipped
              automatically; invoices are never affected). Markdown supported.
            </p>
            <div className="field">
              <label>Subject</label>
              <input className="input" value={camp.subject}
                     onChange={(e) => setCamp({ ...camp, subject: e.target.value })}
                     placeholder="New: AI chatbot integration for your store" />
            </div>
            <div className="field">
              <label>Body (markdown)</label>
              <textarea className="textarea" style={{ minHeight: 140 }} value={camp.body_md}
                        onChange={(e) => setCamp({ ...camp, body_md: e.target.value })}
                        placeholder={"# Big news\nI now offer …"} />
            </div>
            <div style={{ display: "flex", gap: ".6rem" }}>
              <button type="button" className="btn btn-ghost btn-sm" disabled={!st.enabled || sending}
                      onClick={() => campaign(true)}>
                Preview to me
              </button>
              <button type="button" className="btn btn-primary btn-sm" disabled={!st.enabled || sending}
                      onClick={() => campaign(false)}>
                {sending ? "Sending…" : "Send to all clients"}
              </button>
            </div>
          </div>

          <div className="card" style={{ padding: "1.2rem" }}>
            <h3 style={{ fontSize: "1.05rem", marginBottom: ".6rem" }}>Recent sends</h3>
            {log.length === 0 && <p className="form-note">Nothing sent yet.</p>}
            {log.map((r) => (
              <div key={r.id} className="c" style={{ padding: ".25rem 0", fontSize: ".88rem" }}>
                <b style={{ color: r.ok ? "var(--ok)" : "var(--danger)" }}>{r.ok ? "✓" : "✗"}</b>{" "}
                {r.kind} · {r.to} · {r.subject}
                {r.error ? ` — ${r.error}` : ""} · {fmtDay(r.created_at)}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
