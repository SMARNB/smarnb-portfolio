/* Client project card — live milestone tracker, progress, updates, deliverables
   (payment-gated) and the pay flow (Stripe when enabled + manual instructions).
   Port of projectCard/milestonesHtml/deliverablesHtml/payPanelHtml in
   client-dash.js. */
import { useState } from "react";
import { CONFIG } from "../../lib/config";
import { Icon } from "../../lib/icons";
import { money, fmtDate } from "../../lib/format";
import { API } from "../../lib/api";
import { ProofUpload } from "../panels/ManualPayment";
import type { ApiError, Order, PaymentConfig } from "../../lib/types";

const STAGES = ["received", "confirmed", "in_progress", "in_review", "delivered"];
const stageIndex = (st: string) => Math.max(0, STAGES.indexOf(st));

export function ProjectCard({
  o,
  payCfg,
  onChanged,
}: {
  o: Order;
  payCfg: PaymentConfig;
  onChanged: () => void;
}) {
  const [showTimeline, setShowTimeline] = useState(false);
  const [showPay, setShowPay] = useState(false);
  const [payStatus, setPayStatus] = useState<{ type: string; msg: string } | null>(null);

  const idx = stageIndex(o.status);
  const prog = typeof o.progress === "number" ? o.progress : Math.round((idx / (STAGES.length - 1)) * 100);
  const items = (o.items || [])
    .map((i) => `${i.service} (${i.tier}${i.qty > 1 ? " ×" + i.qty : ""})`)
    .join(", ");
  const cancellable = o.status === "received" || o.status === "confirmed";
  const unpaid = o.payment_status !== "paid" && o.status !== "cancelled";
  const updates = (o.updates || []).slice().reverse();

  function cancelOrder() {
    if (!window.confirm(`Cancel order ${o.public_id}? This can't be undone.`)) return;
    API.post("/api/orders/" + encodeURIComponent(o.public_id) + "/cancel")
      .then(onChanged)
      .catch((err: ApiError) => window.alert(err.message || "Could not cancel."));
  }

  function startStripe() {
    setPayStatus({ type: "ok", msg: "Opening secure checkout…" });
    API.post<{ url?: string }>("/api/payments/stripe/checkout/" + encodeURIComponent(o.public_id))
      .then((r) => {
        if (r && r.url) window.location.href = r.url;
        else setPayStatus({ type: "err", msg: "Could not start checkout." });
      })
      .catch((err: ApiError) => setPayStatus({ type: "err", msg: err.message || "Card payments aren't enabled yet." }));
  }

  function startSafepay() {
    setPayStatus({ type: "ok", msg: "Opening secure Safepay checkout…" });
    API.post<{ url?: string }>("/api/payments/safepay/checkout/" + encodeURIComponent(o.public_id))
      .then((r) => {
        if (r && r.url) window.location.href = r.url;
        else setPayStatus({ type: "err", msg: "Could not start Safepay checkout." });
      })
      .catch((err: ApiError) => setPayStatus({ type: "err", msg: err.message || "Safepay isn't enabled yet." }));
  }

  return (
    <article className="card proj-card">
      <div className="proj-top">
        <span className="oid">{o.public_id}</span>
        <span className={`status-chip st-${o.status}`}>{o.status_label || o.status}</span>
      </div>
      <div className="items">{items} · <b>{money(o.total)}</b></div>
      <div className="progress-row">
        <div className="progress">
          <span style={{ width: `${prog}%` }} />
        </div>
        <span className="pct">{prog}%</span>
      </div>

      <Tracker o={o} />

      <div className="meta-row">
        {o.due_date && <span>Due: <b>{o.due_date}</b></span>}
        {o.payment_method && <span>Payment: <b>{o.payment_method}</b> ({o.payment_status || "unpaid"})</span>}
        <span>Ordered: <b>{fmtDate(o.created_at)}</b></span>
      </div>

      {updates.length > 0 && (
        <>
          <button className="timeline-toggle" onClick={() => setShowTimeline((v) => !v)}>
            <Icon name="check" size={16} /> View updates ({updates.length})
          </button>
          {showTimeline && (
            <div className="mini-timeline">
              {updates.map((u, i) => (
                <div className="mt-item" key={i}>
                  <span className="mt-dot" />
                  <div>
                    <p>{u.message}</p>
                    <small>{fmtDate(u.created_at)}</small>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      <Deliverables o={o} />

      {unpaid ? (
        <>
          <div className="pay-row">
            <button className="btn btn-primary btn-sm" onClick={() => setShowPay((v) => !v)}>
              Pay now · {money(o.total)}
            </button>
            {cancellable && (
              <button className="btn btn-outline btn-sm" onClick={cancelOrder}>
                Cancel order
              </button>
            )}
          </div>
          {showPay && <PayPanel o={o} payCfg={payCfg} onStripe={startStripe} onSafepay={startSafepay} status={payStatus} />}
        </>
      ) : (
        cancellable && (
          <div style={{ marginTop: "1rem" }}>
            <button className="btn btn-outline btn-sm" onClick={cancelOrder}>Cancel order</button>
          </div>
        )
      )}

      {o.payment_status === "paid" && <div className="paid-badge">✓ Paid — thank you!</div>}
    </article>
  );
}

function Tracker({ o }: { o: Order }) {
  const ms = o.milestones || [];
  if (!ms.length || o.status === "cancelled") return null;
  let firstOpen = true;
  return (
    <div className="tracker">
      {ms.map((m) => {
        const current = !m.done && firstOpen;
        if (current) firstOpen = false;
        return (
          <div className={`tk-step${m.done ? " done" : ""}${current ? " current" : ""}`} key={m.id}>
            {m.done ? (
              <span className="tk-dot done"><Icon name="check" size={11} /></span>
            ) : current ? (
              <span className="tk-dot current" />
            ) : (
              <span className="tk-dot" />
            )}
            <span className="tk-label">
              {m.title}
              {current && <small> · in progress</small>}
            </span>
          </div>
        );
      })}
      {o.next_step ? (
        <div className="tk-next">Next up: <b>{o.next_step}</b></div>
      ) : (
        <div className="tk-next done">✓ All steps complete</div>
      )}
    </div>
  );
}

function Deliverables({ o }: { o: Order }) {
  const dels = o.deliverables || [];
  if (!dels.length) return null;
  return (
    <div className="deliverables">
      <h4 className="dlv-h">Your files</h4>
      {dels.map((d) => (
        <div className="dlv" key={d.id}>
          <div className="dlv-main">
            <b>{d.title || "Deliverable"}</b>
            {d.note && <small>{d.note}</small>}
          </div>
          <div className="dlv-actions">
            {d.preview_url && (
              <a className="btn btn-outline btn-sm" href={d.preview_url} target="_blank" rel="noopener">
                Preview
              </a>
            )}
            {d.locked ? (
              <span className="dlv-lock">🔒 Unlocks after payment</span>
            ) : (
              d.final_url && (
                <a className="btn btn-primary btn-sm" href={d.final_url} target="_blank" rel="noopener">
                  Download
                </a>
              )
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function PayPanel({
  o,
  payCfg,
  onStripe,
  onSafepay,
  status,
}: {
  o: Order;
  payCfg: PaymentConfig;
  onStripe: () => void;
  onSafepay: () => void;
  status: { type: string; msg: string } | null;
}) {
  const pi = CONFIG.paymentInstructions;
  const online = payCfg.stripe_enabled || payCfg.safepay_enabled;
  return (
    <div className="pay-panel">
      {payCfg.safepay_enabled && (
        <button className="btn btn-primary btn-block" onClick={onSafepay}>
          💳 Pay {money(o.total)} with card / wallet
        </button>
      )}
      {payCfg.stripe_enabled && (
        <button className="btn btn-primary btn-block" onClick={onStripe}>
          💳 Pay {money(o.total)} with card
        </button>
      )}
      {online && <div className="pay-or">or pay manually</div>}
      <div className="pay-methods">
        {pi.methods.map((m, i) => (
          <div className={`pay-method${m.soon ? " soon" : ""}`} key={i}>
            <div>
              <b>{m.label}</b>
              <div className="pm-val">{m.value}</div>
              {m.sub && <small>{m.sub}</small>}
            </div>
          </div>
        ))}
      </div>
      {pi.note && <p className="form-note" style={{ marginTop: ".6rem" }}>{pi.note}</p>}
      {(o.proofs || []).length > 0 ? (
        <div className="form-status ok show" style={{ marginTop: ".6rem" }}>
          ✓ Payment proof uploaded — awaiting confirmation.
        </div>
      ) : (
        <div style={{ marginTop: ".8rem" }}>
          <b style={{ fontSize: ".92rem" }}>Paid by bank / wallet transfer?</b>
          <ProofUpload orderId={o.public_id} />
        </div>
      )}
      {status && <div className={`dash-status show ${status.type}`}>{status.msg}</div>}
    </div>
  );
}
