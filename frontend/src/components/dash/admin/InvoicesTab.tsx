/* Admin "Invoices" tab — the sales ledger. Every order's invoice (draft → sent →
   paid, or void) with search, PDF download, send/resend (payment request when
   unpaid, receipt when paid) and void control. */
import { useCallback, useEffect, useState } from "react";
import { API, getToken } from "../../../lib/api";
import type { ApiError } from "../../../lib/types";
import { fmtDay } from "../../../lib/format";
import { Icon } from "../../../lib/icons";

interface InvoiceRow {
  number: string;
  status: string;
  currency: string;
  total: number;
  lines: { title: string; qty: number; unit: number; amount: number }[];
  created_at: string;
  sent_at: string | null;
  paid_at: string | null;
  order_public_id: string;
  customer_name: string;
  customer_email: string;
  payment_status: string;
}

async function downloadPdf(number: string, setErr: (m: string) => void) {
  try {
    const r = await fetch(`/api/admin/invoices/${encodeURIComponent(number)}.pdf`, {
      headers: { Authorization: "Bearer " + getToken() },
    });
    if (!r.ok) throw new Error("Download failed (" + r.status + ")");
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = number + ".pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  } catch (e) {
    setErr((e as Error).message || "Download failed.");
  }
}

export function InvoicesTab({ onUnauth }: { onUnauth: () => void }) {
  const [rows, setRows] = useState<InvoiceRow[] | null>(null);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState("");

  const fail = useCallback(
    (e: unknown) => {
      const err = e as ApiError;
      if (err.status === 401) onUnauth();
      else setStatus({ type: "err", msg: err.message || "Something went wrong." });
    },
    [onUnauth],
  );

  const load = useCallback(() => {
    API.get<{ invoices: InvoiceRow[] }>("/api/admin/invoices")
      .then((r) => setRows(r.invoices))
      .catch(fail);
  }, [fail]);

  useEffect(() => {
    load();
  }, [load]);

  async function send(inv: InvoiceRow) {
    const receipt = inv.payment_status === "paid";
    if (!window.confirm(
      receipt
        ? `Email the receipt for ${inv.number} to ${inv.customer_email}?`
        : `Email invoice ${inv.number} (payment request) to ${inv.customer_email}?`,
    )) return;
    setBusy(inv.number);
    try {
      await API.post(`/api/admin/orders/${inv.order_public_id}/invoice/send`);
      setStatus({ type: "ok", msg: `${inv.number} emailed to ${inv.customer_email} (copy to you).` });
      load();
    } catch (e) {
      fail(e);
    } finally {
      setBusy("");
    }
  }

  async function toggleVoid(inv: InvoiceRow) {
    const next = inv.status === "void" ? "draft" : "void";
    if (next === "void" && !window.confirm(`Void ${inv.number}? Its public PDF link stops working.`)) return;
    try {
      await API.patch(`/api/admin/invoices/${inv.number}`, { status: next });
      setStatus({ type: "ok", msg: `${inv.number} ${next === "void" ? "voided" : "restored"}.` });
      load();
    } catch (e) {
      fail(e);
    }
  }

  const needle = q.trim().toLowerCase();
  const list = (rows || []).filter(
    (r) =>
      !needle ||
      (r.number + " " + r.order_public_id + " " + r.customer_name + " " + r.customer_email)
        .toLowerCase()
        .includes(needle),
  );
  const chip = (s: string) =>
    s === "paid" ? "ok" : s === "void" ? "warn" : s === "sent" ? "" : "";

  return (
    <div>
      <div className="dash-head">
        <div>
          <h1>Invoices</h1>
          <p>
            Every order gets an invoice automatically — emailed with a branded PDF when payment
            lands (you get a copy). Configure the sender under the Email tab.
          </p>
        </div>
      </div>

      {status && (
        <div className={`dash-status show ${status.type}`} role="status">
          {status.msg}
        </div>
      )}

      <div className="field" style={{ maxWidth: 340, marginBottom: "1rem" }}>
        <input
          className="input"
          placeholder="Search number, order id, customer…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {!rows && <p className="form-note">Loading…</p>}
      {rows && list.length === 0 && (
        <div className="empty-card card">
          <Icon name="doc" size={26} />
          <p>No invoices yet — one is created automatically with each new order.</p>
        </div>
      )}

      {list.length > 0 && (
        <div className="svc-list">
          {list.map((inv) => (
            <div className="svc-item client-row" key={inv.number}>
              <div className="client-main">
                <div className="t">
                  {inv.number} · {inv.currency}
                  {inv.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className="c">
                  {inv.customer_name || "—"} · {inv.customer_email || "no email"} · order{" "}
                  {inv.order_public_id} · issued {fmtDay(inv.created_at)}
                  {inv.sent_at ? ` · sent ${fmtDay(inv.sent_at)}` : ""}
                </div>
                <div className="client-badges">
                  <span className={`client-badge ${chip(inv.status)}`}>{inv.status.toUpperCase()}</span>
                  {inv.payment_status === "paid" && inv.status !== "paid" && (
                    <span className="client-badge ok">ORDER PAID</span>
                  )}
                </div>
              </div>
              <div className="client-actions">
                <button className="btn btn-outline btn-sm" onClick={() => downloadPdf(inv.number, (m) => setStatus({ type: "err", msg: m }))}>
                  <Icon name="download" size={15} /> PDF
                </button>
                {inv.status !== "void" && (
                  <button
                    className="btn btn-ghost btn-sm"
                    disabled={busy === inv.number || !inv.customer_email}
                    onClick={() => send(inv)}
                  >
                    {inv.payment_status === "paid"
                      ? inv.sent_at ? "Resend receipt" : "Send receipt"
                      : inv.sent_at ? "Resend invoice" : "Send invoice"}
                  </button>
                )}
                <button className="btn btn-ghost btn-sm client-del" onClick={() => toggleVoid(inv)}>
                  {inv.status === "void" ? "Restore" : "Void"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
