/* Orders tab — stats, status filters, order list and the manage panel with the
   AUTOMATIC milestone checklist (toggle/add/delete → server recomputes status +
   progress and posts a client update), due date + payment, notes, deliverables
   and cancel/reopen. Port of the Orders tab in admin-dash.js. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "../../../lib/icons";
import { money, fmtDate } from "../../../lib/format";
import { API } from "../../../lib/api";
import type { ApiError, Order, Stats } from "../../../lib/types";

const STATUSES: [string, string][] = [
  ["received", "Received"],
  ["confirmed", "Confirmed"],
  ["in_progress", "In Progress"],
  ["in_review", "In Review"],
  ["delivered", "Delivered"],
  ["cancelled", "Cancelled"],
];

export function OrdersTab({ onUnauth, onStatsChange }: { onUnauth: () => void; onStatsChange?: () => void }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const refresh = useCallback(() => {
    return Promise.all([API.get<Stats>("/api/admin/stats"), API.get<Order[]>("/api/admin/orders")])
      .then(([s, o]) => {
        setStats(s);
        setOrders(o);
      })
      .catch((err: ApiError) => {
        if (err.status === 401 || err.status === 403) onUnauth();
      });
  }, [onUnauth]);

  useEffect(() => {
    refresh();
    pollRef.current = window.setInterval(refresh, 25000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [refresh]);

  const mergeOrder = useCallback((u: Order) => {
    setOrders((prev) => {
      const i = prev.findIndex((x) => x.public_id === u.public_id);
      if (i >= 0) {
        const next = prev.slice();
        next[i] = u;
        return next;
      }
      return [u, ...prev];
    });
  }, []);

  const refreshStats = useCallback(() => {
    API.get<Stats>("/api/admin/stats").then(setStats).then(onStatsChange).catch(() => {});
  }, [onStatsChange]);

  const selected = orders.find((o) => o.public_id === selectedId) || null;
  const list = orders.filter((o) => filter === "all" || o.status === filter);

  const statCards: [string, string | number, boolean][] = stats
    ? [
        ["Total orders", stats.total_orders, false],
        ["Active", stats.active_orders, false],
        ["Delivered", stats.delivered_orders, false],
        ["Revenue (paid)", money(stats.revenue), true],
        ["Clients", stats.clients, false],
      ]
    : [];

  const counts = (stats && stats.by_status) || {};
  const chips: [string, string][] = [["all", "All"], ...STATUSES];

  return (
    <>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "1rem" }}>
        <button className="btn btn-ghost btn-sm" onClick={refresh}>
          <Icon name="arrow" size={16} /> Refresh
        </button>
      </div>

      <div className="stat-grid" id="stats">
        {statCards.map((c) => (
          <div className="card stat-card" key={c[0]}>
            <div className={`v${c[2] ? " grad" : ""}`}>{c[1] == null ? 0 : c[1]}</div>
            <div className="k">{c[0]}</div>
          </div>
        ))}
      </div>

      <div className="filter-chips" id="filters">
        {chips.map((c) => {
          const n = c[0] === "all" ? orders.length : counts[c[0]] || 0;
          return (
            <button key={c[0]} className={filter === c[0] ? "active" : ""} onClick={() => setFilter(c[0])}>
              {c[1]} ({n})
            </button>
          );
        })}
      </div>

      <div className="admin-grid">
        <div className="order-rows" id="orderRows">
          {list.length === 0 ? (
            <p className="form-note">No orders{filter !== "all" ? " in this status" : " yet"}.</p>
          ) : (
            list.map((o) => {
              const prog = typeof o.progress === "number" ? o.progress : 0;
              return (
                <button
                  key={o.public_id}
                  className={`order-row${selectedId === o.public_id ? " active" : ""}`}
                  onClick={() => setSelectedId(o.public_id)}
                >
                  <div className="r1">
                    <span className="oid">{o.public_id}</span>
                    <span className={`status-chip st-${o.status}`}>{o.status_label || o.status}</span>
                  </div>
                  <div className="who">
                    {o.customer_name || o.customer_email} · {money(o.total)}
                    {o.payment_status === "paid" ? " · paid" : ""}
                  </div>
                  <div className="r2">
                    <div className="progress">
                      <span style={{ width: `${prog}%` }} />
                    </div>
                    <span className="pct" style={{ fontSize: ".8rem" }}>{prog}%</span>
                  </div>
                </button>
              );
            })
          )}
        </div>

        <div id="manage">
          {selected ? (
            <ManagePanel
              key={selected.public_id}
              order={selected}
              mergeOrder={mergeOrder}
              refreshStats={refreshStats}
            />
          ) : (
            <div className="card manage">
              <div className="empty">Select an order on the left to manage it.</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function ManagePanel({
  order,
  mergeOrder,
  refreshStats,
}: {
  order: Order;
  mergeOrder: (u: Order) => void;
  refreshStats: () => void;
}) {
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [newMs, setNewMs] = useState("");
  const [note, setNote] = useState("");
  const dTitle = useRef<HTMLInputElement>(null);
  const dPreview = useRef<HTMLInputElement>(null);
  const dFinal = useRef<HTMLInputElement>(null);
  const dNote = useRef<HTMLInputElement>(null);
  const dueRef = useRef<HTMLInputElement>(null);
  const payRef = useRef<HTMLSelectElement>(null);

  const mStatus = (type: string, msg: string) => setStatus({ type, msg });
  const applyOrder = (u: Order, msg?: string) => {
    mergeOrder(u);
    refreshStats();
    if (msg) mStatus("ok", msg);
  };

  const items = (order.items || [])
    .map((i) => `${i.service} (${i.tier}${i.qty > 1 ? " ×" + i.qty : ""})`)
    .join(", ");
  const updates = (order.updates || []).slice().reverse();
  const dels = order.deliverables || [];
  const prog = typeof order.progress === "number" ? order.progress : 0;
  const cancelled = order.status === "cancelled";

  function toggleMilestone(mid: number, on: boolean) {
    mStatus("ok", "Updating…");
    API.patch<Order>("/api/admin/milestones/" + mid, { done: !on })
      .then((u) => applyOrder(u, "Tracker updated."))
      .catch((err: ApiError) => mStatus("err", err.message || "Failed."));
  }
  function delMilestone(mid: number) {
    if (!window.confirm("Remove this milestone?")) return;
    API.del<Order>("/api/admin/milestones/" + mid)
      .then((u) => applyOrder(u, "Milestone removed."))
      .catch((err: ApiError) => mStatus("err", err.message || "Failed."));
  }
  function addMilestone() {
    const t = newMs.trim();
    if (!t) {
      mStatus("err", "Name the step first.");
      return;
    }
    mStatus("ok", "Adding…");
    API.post<Order>("/api/admin/orders/" + encodeURIComponent(order.public_id) + "/milestones", { title: t })
      .then((u) => {
        setNewMs("");
        applyOrder(u, "Milestone added.");
      })
      .catch((err: ApiError) => mStatus("err", err.message || "Failed."));
  }
  function setOrderStatus(s: string, msg: string) {
    API.patch<Order>("/api/admin/orders/" + encodeURIComponent(order.public_id), { status: s })
      .then((u) => applyOrder(u, msg))
      .catch((err: ApiError) => mStatus("err", err.message || "Failed."));
  }
  function saveDatePayment() {
    const payload: { payment_status: string; due_date?: string } = { payment_status: payRef.current!.value };
    const due = dueRef.current!.value;
    if (due) payload.due_date = due;
    mStatus("ok", "Saving…");
    API.patch<Order>("/api/admin/orders/" + encodeURIComponent(order.public_id), payload)
      .then((u) => applyOrder(u, "Saved."))
      .catch((err: ApiError) => mStatus("err", err.message || "Save failed."));
  }
  function postNote() {
    const msg = note.trim();
    if (!msg) {
      mStatus("err", "Write a note first.");
      return;
    }
    mStatus("ok", "Posting…");
    API.post<Order>("/api/admin/orders/" + encodeURIComponent(order.public_id) + "/updates", { message: msg })
      .then((u) => {
        setNote("");
        applyOrder(u, "Note posted.");
      })
      .catch((err: ApiError) => mStatus("err", err.message || "Failed."));
  }
  function addDeliverable() {
    const title = dTitle.current!.value.trim();
    const preview = dPreview.current!.value.trim();
    const final = dFinal.current!.value.trim();
    if (!title && !preview && !final) {
      mStatus("err", "Add a title and at least one link.");
      return;
    }
    mStatus("ok", "Adding file…");
    API.post<Order>("/api/admin/orders/" + encodeURIComponent(order.public_id) + "/deliverables", {
      title,
      preview_url: preview,
      final_url: final,
      note: dNote.current!.value.trim(),
    })
      .then((u) => {
        dTitle.current!.value = "";
        dPreview.current!.value = "";
        dFinal.current!.value = "";
        dNote.current!.value = "";
        applyOrder(u, "Deliverable added.");
      })
      .catch((err: ApiError) => mStatus("err", err.message || "Failed."));
  }
  function delDeliverable(did: number) {
    API.del("/api/admin/deliverables/" + did)
      .then(() => API.get<Order>("/api/admin/orders/" + encodeURIComponent(order.public_id)))
      .then((u) => applyOrder(u, "Removed."))
      .catch((err: ApiError) => mStatus("err", err.message || "Failed."));
  }

  let firstOpen = true;

  return (
    <div className="card manage">
      <h3>{order.public_id}</h3>
      <p className="sub">
        {order.customer_name} &lt;{order.customer_email}&gt;
        {order.customer_whatsapp ? " · " + order.customer_whatsapp : ""}
        <br />
        {items} · <b>{money(order.total)}</b>
        {order.payment_method ? " · " + order.payment_method : ""}
      </p>
      {status && <div className={`dash-status show ${status.type}`}>{status.msg}</div>}

      <div className="auto-track">
        <div className="at-head">
          <span className={`status-chip st-${order.status}`}>{order.status_label || order.status}</span>
          <span className="at-auto">auto · updates the client live</span>
        </div>
        <div className="progress-row">
          <div className="progress">
            <span style={{ width: `${prog}%` }} />
          </div>
          <span className="pct">{prog}%</span>
        </div>
      </div>

      {cancelled ? (
        <div className="form-note" style={{ margin: ".4rem 0" }}>
          This order is cancelled.{" "}
          <button className="btn btn-outline btn-sm" onClick={() => setOrderStatus("received", "Order reopened.")}>
            Reopen
          </button>
        </div>
      ) : (
        <div className="field">
          <label>
            Milestones <span style={{ color: "var(--muted)", fontWeight: 400 }}>(tick them off — status &amp; progress update automatically)</span>
          </label>
          <div className="ms-list" id="m-milestones">
            {(order.milestones || []).length === 0 ? (
              <p className="form-note">No milestones yet — add one below.</p>
            ) : (
              (order.milestones || []).map((m) => {
                const current = !m.done && firstOpen;
                if (current) firstOpen = false;
                return (
                  <div className={`ms-row${m.done ? " done" : ""}${current ? " current" : ""}`} key={m.id}>
                    <button
                      type="button"
                      className="ms-check"
                      title={m.done ? "Mark not done" : "Mark done"}
                      onClick={() => toggleMilestone(m.id, m.done)}
                    >
                      {m.done && <Icon name="check" size={13} />}
                    </button>
                    <div className="ms-main">
                      <span className="ms-title">{m.title}</span>
                      {m.done && m.done_at ? <small>{fmtDate(m.done_at)}</small> : current ? <small>in progress</small> : null}
                    </div>
                    <button type="button" className="ms-del" title="Remove milestone" onClick={() => delMilestone(m.id)}>
                      ×
                    </button>
                  </div>
                );
              })
            )}
          </div>
          <div className="ms-add">
            <input
              className="input"
              placeholder="Add a custom step…"
              maxLength={200}
              value={newMs}
              onChange={(e) => setNewMs(e.target.value)}
            />
            <button className="btn btn-outline btn-sm" onClick={addMilestone}>
              <Icon name="plus" size={16} /> Add
            </button>
          </div>
        </div>
      )}

      <div className="two">
        <div className="field">
          <label htmlFor="m-due">Due date</label>
          <input className="input" type="date" id="m-due" ref={dueRef} defaultValue={order.due_date || ""} />
        </div>
        <div className="field">
          <label htmlFor="m-pay">Payment</label>
          <select className="select" id="m-pay" ref={payRef} defaultValue={order.payment_status}>
            {["unpaid", "paid", "refunded"].map((p) => (
              <option key={p} value={p}>
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>
      <button className="btn btn-primary btn-block" onClick={saveDatePayment}>
        Save date &amp; payment
      </button>
      {!cancelled && (
        <button
          className="btn btn-ghost btn-block btn-sm"
          style={{ marginTop: ".5rem" }}
          onClick={() => {
            if (window.confirm("Cancel order " + order.public_id + "?")) setOrderStatus("cancelled", "Order cancelled.");
          }}
        >
          Cancel this order
        </button>
      )}

      <hr className="divider" style={{ margin: "1.3rem 0" }} />
      <div className="field">
        <label htmlFor="m-msg">Post a note to the client</label>
        <textarea
          className="textarea"
          id="m-msg"
          placeholder="e.g. Wireframes done, building the API now…"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
      </div>
      <button className="btn btn-ghost btn-block" onClick={postNote}>
        Post note
      </button>
      {updates.length > 0 && (
        <div className="admin-updates">
          {updates.map((u, i) => (
            <div className="u" key={i}>
              {u.message}
              <small>
                {fmtDate(u.created_at)}
                {u.status ? " · " + u.status : ""}
              </small>
            </div>
          ))}
        </div>
      )}

      <hr className="divider" style={{ margin: "1.3rem 0" }} />
      <label style={{ fontWeight: 600, fontSize: ".88rem" }}>
        Deliverables <span style={{ color: "var(--muted)", fontWeight: 400 }}>(preview always visible · final unlocks when Paid)</span>
      </label>
      {dels.length > 0 ? (
        <div className="dlv-admin-list">
          {dels.map((d) => (
            <div className="dlv-admin" key={d.id}>
              <div>
                <b>{d.title || "Deliverable"}</b>
                <small>
                  {d.preview_url ? "preview ✓ " : ""}
                  {d.final_url ? "final ✓" : "no final"}
                </small>
              </div>
              <button className="btn btn-outline btn-sm" onClick={() => delDeliverable(d.id)}>
                Remove
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="form-note">No files attached yet.</p>
      )}
      <div className="two">
        <div className="field">
          <label htmlFor="d-title">Title</label>
          <input className="input" id="d-title" ref={dTitle} placeholder="Final design files" />
        </div>
        <div className="field">
          <label htmlFor="d-preview">Preview URL</label>
          <input className="input" id="d-preview" ref={dPreview} placeholder="https://… watermarked/demo" />
        </div>
      </div>
      <div className="two">
        <div className="field">
          <label htmlFor="d-final">Final URL (gated)</label>
          <input className="input" id="d-final" ref={dFinal} placeholder="https://… real product" />
        </div>
        <div className="field">
          <label htmlFor="d-note">Note</label>
          <input className="input" id="d-note" ref={dNote} placeholder="optional" />
        </div>
      </div>
      <button className="btn btn-ghost btn-block" onClick={addDeliverable}>
        Add deliverable
      </button>
    </div>
  );
}
