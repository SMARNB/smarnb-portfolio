/* Manual-transfer helpers shared by the checkout modal and the client dashboard:
   - ManualPayDetails: the owner's Raast / SadaPay / JazzCash account details for
     the method the buyer selected (from CONFIG.paymentInstructions).
   - ProofUpload: the buyer attaches a payment screenshot (must show date & time)
     + an optional transaction reference; it lands on the order for the developer
     to review in /admin and mark paid. */
import { useState } from "react";
import { CONFIG } from "../../lib/config";
import { API } from "../../lib/api";
import type { ApiError, Order } from "../../lib/types";

/* Map a payment-option label (the <select> value) to the instruction entries to
   show. An unknown / card label shows nothing. */
const METHOD_MATCH: Record<string, string> = {
  raast: "Raast",
  sadapay: "SadaPay",
  jazzcash: "JazzCash",
};

export function manualMethodKey(label: string): string | null {
  const entry = CONFIG.payments.find((p) => p.label === label);
  return entry && METHOD_MATCH[entry.id] ? entry.id : null;
}

export function ManualPayDetails({ methodLabel, all = false }: { methodLabel?: string; all?: boolean }) {
  const key = methodLabel ? manualMethodKey(methodLabel) : null;
  const wanted = all ? Object.values(METHOD_MATCH) : key ? [METHOD_MATCH[key]] : [];
  const methods = CONFIG.paymentInstructions.methods.filter((m) => wanted.includes(m.label));
  if (!methods.length) return null;
  return (
    <div className="manual-pay">
      {methods.map((m) => (
        <div className={`pay-method${m.soon ? " soon" : ""}`} key={m.label}>
          <div>
            <b>{m.label}</b>
            <div className="pm-val">{m.value}</div>
            {m.sub && <small>{m.sub}</small>}
          </div>
        </div>
      ))}
      <p className="form-note">{CONFIG.paymentInstructions.note}</p>
    </div>
  );
}

export function ProofUpload({ orderId, onUploaded }: { orderId: string; onUploaded?: (o: Order) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [ref, setRef] = useState("");
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setStatus({ type: "err", msg: "Attach your payment screenshot first (it must show the date & time)." });
      return;
    }
    setBusy(true);
    setStatus({ type: "ok", msg: "Uploading…" });
    try {
      const o = await API.upload<Order>(
        "/api/orders/" + encodeURIComponent(orderId) + "/proof", file, { ref });
      setDone(true);
      setStatus({ type: "ok", msg: "Proof received ✓ — I'll verify and mark your order paid shortly." });
      onUploaded?.(o);
    } catch (err) {
      setStatus({ type: "err", msg: (err as ApiError).message || "Upload failed — please try again." });
      setBusy(false);
    }
  }

  if (done) {
    return <div className="form-status ok show">✓ Payment proof received — I'll confirm shortly.</div>;
  }
  return (
    <form className="form proof-form" onSubmit={submit} noValidate>
      <div className="field">
        <label htmlFor={"pf-file-" + orderId}>
          Payment screenshot <span className="req">*</span>{" "}
          <span style={{ color: "var(--muted)", fontWeight: 400 }}>(must show date &amp; time)</span>
        </label>
        <input
          className="input"
          id={"pf-file-" + orderId}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          onChange={(e) => setFile(e.currentTarget.files?.[0] || null)}
        />
      </div>
      <div className="field">
        <label htmlFor={"pf-ref-" + orderId}>
          Transaction ID / sent when <span style={{ color: "var(--muted)", fontWeight: 400 }}>(optional)</span>
        </label>
        <input
          className="input"
          id={"pf-ref-" + orderId}
          value={ref}
          maxLength={200}
          placeholder="e.g. TID 8839021 · sent 2 Jul, 3:40 pm"
          onChange={(e) => setRef(e.currentTarget.value)}
        />
      </div>
      {status && <div className={`form-status show ${status.type}`}>{status.msg}</div>}
      <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
        Submit payment proof
      </button>
    </form>
  );
}
