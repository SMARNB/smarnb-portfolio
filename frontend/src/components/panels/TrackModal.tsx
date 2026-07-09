/* Track-order modal — look up an order by ID against the public API (falls back
   to a locally-saved copy), then show a progress bar, stage timeline and latest
   updates. Port of the tracking flow in app.js. */
import { useEffect, useRef, useState } from "react";
import { Icon } from "../../lib/icons";
import { money, fmtDate, whatsappLink } from "../../lib/format";
import { CONFIG } from "../../lib/config";
import { getOrders, getOrder } from "../../lib/cart";
import type { LocalOrder } from "../../lib/cart";
import type { Order } from "../../lib/types";
import { useUI } from "../../context/UIContext";

const STAGES = [
  { key: "Received", note: "Order received." },
  { key: "Confirmed", note: "Details confirmed & started." },
  { key: "In Progress", note: "Work is underway." },
  { key: "In Review", note: "Ready for your review." },
  { key: "Delivered", note: "Final files delivered." },
];

interface TrackResult {
  id: string;
  items: { service: string; tier: string; price: number; qty: number }[];
  total: number;
  status: string;
  progress?: number;
  payment_method?: string;
  invoice?: { number: string; status: string } | null;
  timeline: { status: string | null; note: string; at: string }[];
}

function normalizeServer(s: Order): TrackResult {
  return {
    id: s.public_id,
    items: (s.items || []).map((i) => ({ service: i.service, tier: i.tier, price: i.price, qty: i.qty })),
    total: s.total,
    status: s.status_label || s.status,
    progress: s.progress,
    payment_method: s.payment_method,
    invoice: s.invoice && s.invoice.status !== "void" ? { number: s.invoice.number, status: s.invoice.status } : null,
    timeline: (s.updates || []).map((u) => ({ status: u.status, note: u.message, at: u.created_at })),
  };
}
function normalizeLocal(o: LocalOrder): TrackResult {
  return {
    id: o.id,
    items: o.items.map((i) => ({ service: i.service, tier: i.tier, price: i.price, qty: i.qty })),
    total: o.total,
    status: o.status,
    payment_method: o.payment_method,
    timeline: o.timeline.map((u) => ({ status: u.status, note: u.note, at: u.at })),
  };
}

export function TrackModal() {
  const { isOpen, close, stack } = useUI();
  const open = isOpen("track");
  const panel = stack.find((p) => p.type === "track") as { type: "track"; id?: string } | undefined;
  const prefillId = panel?.id;

  const [query, setQuery] = useState("");
  const [result, setResult] = useState<TrackResult | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const lastPrefill = useRef<string | undefined>(undefined);

  const doTrack = (raw: string) => {
    const id = raw.trim().toUpperCase();
    if (!id) {
      setResult(null);
      setState("idle");
      return;
    }
    setState("loading");
    setResult(null);
    fetch((CONFIG.apiBase || "") + "/api/orders/" + encodeURIComponent(id), {
      headers: { Accept: "application/json" },
    })
      .then((r) => {
        if (!r.ok) throw new Error("nf");
        return r.json();
      })
      .then((server: Order) => {
        setResult(normalizeServer(server));
        setState("idle");
      })
      .catch(() => {
        const local = getOrder(id);
        if (local) {
          setResult(normalizeLocal(local));
          setState("idle");
        } else {
          setState("error");
        }
      });
  };

  // When opened with a prefilled id, run the lookup once.
  useEffect(() => {
    if (open && prefillId && lastPrefill.current !== prefillId) {
      lastPrefill.current = prefillId;
      setQuery(prefillId);
      doTrack(prefillId);
    }
    if (!open) lastPrefill.current = undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, prefillId]);

  const recent = getOrders().slice(0, 6);

  return (
    <div
      className={`modal${open ? " open" : ""}`}
      id="trackModal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="trackTitle"
      aria-hidden={!open}
    >
      <div className="modal-head">
        <h3 id="trackTitle">Track your order</h3>
        <button className="close-btn" aria-label="Close tracking" onClick={() => close("track")}>
          <Icon name="close" size={20} />
        </button>
      </div>
      <div className="modal-body">
        <p className="form-note" style={{ marginBottom: ".8rem" }}>
          Enter your order ID (e.g. ALR-XXXXXX) to see its status.
        </p>
        <div style={{ display: "flex", gap: ".5rem" }}>
          <input
            className="input"
            placeholder="ALR-XXXXXX"
            aria-label="Order ID"
            autoComplete="off"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                doTrack(query);
              }
            }}
          />
          <button className="btn btn-primary" onClick={() => doTrack(query)}>
            Track
          </button>
        </div>
        <div style={{ marginTop: "1.2rem" }}>
          {state === "loading" && <p className="form-note">Looking up {query.toUpperCase()}…</p>}
          {state === "error" && (
            <div className="form-status err show">
              No order found for “{query.toUpperCase()}”. Check the ID, or it may have been placed on a different device.
            </div>
          )}
          {state === "idle" && result && <ResultView order={result} />}
          {state === "idle" && !result && <RecentList recent={recent} onPick={(id) => { setQuery(id); doTrack(id); }} />}
        </div>
      </div>
    </div>
  );
}

function RecentList({ recent, onPick }: { recent: LocalOrder[]; onPick: (id: string) => void }) {
  if (!recent.length)
    return <p className="form-note">No orders found in this browser yet. Place an order and it'll appear here.</p>;
  return (
    <>
      <h4 style={{ marginBottom: ".6rem" }}>Your recent orders</h4>
      <div className="recent-orders">
        {recent.map((o) => (
          <div
            className="recent-order"
            key={o.id}
            tabIndex={0}
            role="button"
            onClick={() => onPick(o.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onPick(o.id);
              }
            }}
          >
            <span className="oid">{o.id}</span>
            <span className="status-chip">{o.status}</span>
          </div>
        ))}
      </div>
    </>
  );
}

function ResultView({ order }: { order: TrackResult }) {
  const statusStr = String(order.status || "Received");
  const cancelled = statusStr.toLowerCase() === "cancelled";
  let currentIdx = STAGES.findIndex((s) => s.key.toLowerCase() === statusStr.toLowerCase());
  if (currentIdx < 0) currentIdx = 0;
  const prog =
    typeof order.progress === "number" ? order.progress : Math.round((currentIdx / (STAGES.length - 1)) * 100);
  const items = order.items.map((i) => `${i.service} (${i.tier})`).join(", ");
  const updates = order.timeline.slice().reverse().slice(0, 6);

  return (
    <>
      <div className="order-id-box" style={{ textAlign: "left" }}>
        <small>Order</small>
        <div className="id" style={{ fontSize: "1.2rem" }}>{order.id}</div>
        <p className="form-note" style={{ marginTop: ".3rem" }}>{items} · {money(order.total)}</p>
        {order.invoice && (
          <a
            className="btn btn-outline btn-sm"
            style={{ marginTop: ".55rem" }}
            href={`/api/orders/${encodeURIComponent(order.id)}/invoice.pdf`}
            target="_blank"
            rel="noopener"
          >
            <Icon name="download" size={15} /> Invoice {order.invoice.number} (PDF)
          </a>
        )}
      </div>

      {cancelled ? (
        <div className="form-status err show">This order was cancelled.</div>
      ) : (
        <>
          <div style={{ margin: "1rem 0 1.2rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: ".82rem", color: "var(--muted)", marginBottom: ".4rem" }}>
              <span>Progress</span>
              <span style={{ color: "var(--text)", fontWeight: 800 }}>{prog}%</span>
            </div>
            <div style={{ height: "10px", borderRadius: "999px", background: "var(--surface-2)", overflow: "hidden", border: "1px solid var(--border)" }}>
              <span style={{ display: "block", height: "100%", width: `${prog}%`, background: "var(--grad)", borderRadius: "999px" }} />
            </div>
          </div>
          <div className="timeline">
            {STAGES.map((s, i) => {
              const cls = i < currentIdx ? "done" : i === currentIdx ? "current done" : "";
              return (
                <div className={`tl-step ${cls}`} key={s.key}>
                  <span className="tl-dot">{i <= currentIdx ? <Icon name="check" size={14} /> : null}</span>
                  <div className="tl-body">
                    <b>{s.key}</b>
                    <small>{s.note}</small>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {updates.length > 0 && (
        <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--border)" }}>
          <b style={{ fontSize: ".9rem" }}>Latest updates</b>
          {updates.map((u, idx) => (
            <div style={{ marginTop: ".6rem", fontSize: ".88rem" }} key={idx}>
              <span>{u.note}</span>
              <small style={{ display: "block", color: "var(--muted-2)", fontSize: ".74rem", marginTop: ".1rem" }}>
                {fmtDate(u.at)}
              </small>
            </div>
          ))}
        </div>
      )}

      <p className="form-note" style={{ marginTop: "1rem" }}>
        Questions about this order?{" "}
        <a href={whatsappLink("Hi! About my order " + order.id + "…")} target="_blank" rel="noopener" style={{ color: "var(--accent-2)", fontWeight: 600 }}>
          Message me
        </a>
        .
      </p>
    </>
  );
}
