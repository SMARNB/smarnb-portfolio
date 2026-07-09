/* Admin "Inventory" tab — sellable items with optional stock tracking. A tracked
   item's stock decrements automatically when a PAID order line's title matches
   the item's name; every change lands in an auditable moves ledger, and low
   stock alerts the owner (WhatsApp + email). Untracked items (stock —) are just
   catalogued. */
import { useCallback, useEffect, useState } from "react";
import { API } from "../../../lib/api";
import type { ApiError } from "../../../lib/types";
import { fmtDay } from "../../../lib/format";
import { Icon } from "../../../lib/icons";

interface InvItem {
  id: number;
  sku: string;
  name: string;
  kind: string;
  stock: number | null;
  low_stock_threshold: number;
  tracked: boolean;
  low: boolean;
  active: boolean;
  notes: string;
  created_at: string;
}
interface Move {
  id: number;
  delta: number;
  reason: string;
  ref: string;
  note: string;
  created_at: string;
}

const EMPTY = { sku: "", name: "", kind: "product", stock: "", low_stock_threshold: "1" };

export function InventoryTab({ onUnauth }: { onUnauth: () => void }) {
  const [items, setItems] = useState<InvItem[] | null>(null);
  const [form, setForm] = useState({ ...EMPTY });
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [openMoves, setOpenMoves] = useState<number | null>(null);
  const [moves, setMoves] = useState<Move[]>([]);

  const fail = useCallback(
    (e: unknown) => {
      const err = e as ApiError;
      if (err.status === 401) onUnauth();
      else setStatus({ type: "err", msg: err.message || "Something went wrong." });
    },
    [onUnauth],
  );

  const load = useCallback(() => {
    API.get<{ items: InvItem[] }>("/api/admin/inventory")
      .then((r) => setItems(r.items))
      .catch(fail);
  }, [fail]);

  useEffect(() => {
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    try {
      await API.post("/api/admin/inventory", {
        sku: form.sku.trim(),
        name: form.name.trim(),
        kind: form.kind,
        stock: form.stock.trim() === "" ? null : Math.max(0, parseInt(form.stock, 10) || 0),
        low_stock_threshold: Math.max(0, parseInt(form.low_stock_threshold, 10) || 0),
      });
      setForm({ ...EMPTY });
      setStatus({ type: "ok", msg: "Item added." });
      load();
    } catch (err) {
      fail(err);
    }
  }

  async function adjust(item: InvItem, sign: 1 | -1) {
    const raw = window.prompt(
      `${sign > 0 ? "Add to" : "Remove from"} "${item.name}" stock (currently ${item.stock}):`,
      "1",
    );
    if (raw === null) return;
    const n = Math.abs(parseInt(raw, 10) || 0);
    if (!n) return;
    try {
      await API.post(`/api/admin/inventory/${item.id}/adjust`, {
        delta: sign * n,
        reason: sign > 0 ? "restock" : "correction",
      });
      load();
      if (openMoves === item.id) showMoves(item, true);
    } catch (e) {
      fail(e);
    }
  }

  async function setTracking(item: InvItem) {
    if (item.tracked) {
      if (!window.confirm(`Stop tracking stock for "${item.name}"? The count is cleared.`)) return;
      try {
        await API.patch(`/api/admin/inventory/${item.id}`, { untrack: true });
        load();
      } catch (e) {
        fail(e);
      }
      return;
    }
    const raw = window.prompt(`Set the current stock count for "${item.name}":`, "10");
    if (raw === null) return;
    try {
      await API.patch(`/api/admin/inventory/${item.id}`, {
        stock: Math.max(0, parseInt(raw, 10) || 0),
      });
      load();
    } catch (e) {
      fail(e);
    }
  }

  async function toggleActive(item: InvItem) {
    try {
      await API.patch(`/api/admin/inventory/${item.id}`, { active: !item.active });
      load();
    } catch (e) {
      fail(e);
    }
  }

  async function showMoves(item: InvItem, keepOpen = false) {
    if (openMoves === item.id && !keepOpen) {
      setOpenMoves(null);
      return;
    }
    try {
      const r = await API.get<{ moves: Move[] }>(`/api/admin/inventory/${item.id}/moves`);
      setMoves(r.moves);
      setOpenMoves(item.id);
    } catch (e) {
      fail(e);
    }
  }

  return (
    <div>
      <div className="dash-head">
        <div>
          <h1>Inventory</h1>
          <p>
            Track stock for limited items (licenses, packaged goods). Name an item exactly like
            the service/product title on orders and each paid order lowers its stock — you'll be
            alerted at the threshold. Leave stock empty for untracked items.
          </p>
        </div>
      </div>

      {status && (
        <div className={`dash-status show ${status.type}`} role="status">
          {status.msg}
        </div>
      )}

      <form className="form" onSubmit={add} style={{ marginBottom: "1.4rem" }}>
        <div className="two">
          <div className="field">
            <label>SKU</label>
            <input className="input" required value={form.sku}
                   onChange={(e) => setForm({ ...form, sku: e.target.value })}
                   placeholder="CW-SINGLE" />
          </div>
          <div className="field">
            <label>Name (must match the order line title)</label>
            <input className="input" required value={form.name}
                   onChange={(e) => setForm({ ...form, name: e.target.value })}
                   placeholder="CodeWatch — Single-Deployment" />
          </div>
        </div>
        <div className="two">
          <div className="field">
            <label>Kind</label>
            <select className="select" value={form.kind}
                    onChange={(e) => setForm({ ...form, kind: e.target.value })}>
              <option value="product">Product</option>
              <option value="license">License</option>
              <option value="service">Service</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="field">
            <label>Stock (empty = untracked) · alert at</label>
            <div style={{ display: "flex", gap: ".5rem" }}>
              <input className="input" inputMode="numeric" value={form.stock}
                     onChange={(e) => setForm({ ...form, stock: e.target.value })}
                     placeholder="—" />
              <input className="input" inputMode="numeric" value={form.low_stock_threshold}
                     onChange={(e) => setForm({ ...form, low_stock_threshold: e.target.value })}
                     style={{ maxWidth: 90 }} />
            </div>
          </div>
        </div>
        <button className="btn btn-primary btn-sm" style={{ justifySelf: "start" }}>
          Add item
        </button>
      </form>

      {!items && <p className="form-note">Loading…</p>}
      {items && items.length === 0 && (
        <div className="empty-card card">
          <Icon name="box" size={26} />
          <p>No inventory items yet. Add the products/licenses whose availability you want tracked.</p>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="svc-list">
          {items.map((it) => (
            <div key={it.id}>
              <div className={`svc-item client-row${it.active ? "" : " inactive"}`}>
                <div className="client-main">
                  <div className="t">
                    {it.name} <span style={{ color: "var(--muted-2)", fontWeight: 500 }}>· {it.sku}</span>
                  </div>
                  <div className="c">
                    {it.kind} · added {fmtDay(it.created_at)}
                    {it.tracked ? ` · alert at ${it.low_stock_threshold}` : ""}
                  </div>
                  <div className="client-badges">
                    <span className={`client-badge ${it.low ? "warn" : it.tracked ? "ok" : ""}`}>
                      {it.tracked ? `Stock: ${it.stock}${it.low ? " — LOW" : ""}` : "Untracked"}
                    </span>
                    {!it.active && <span className="client-badge warn">Inactive</span>}
                  </div>
                </div>
                <div className="client-actions">
                  {it.tracked && (
                    <>
                      <button className="btn btn-outline btn-sm" onClick={() => adjust(it, 1)}>
                        + Stock
                      </button>
                      <button className="btn btn-ghost btn-sm" onClick={() => adjust(it, -1)}>
                        − Stock
                      </button>
                    </>
                  )}
                  <button className="btn btn-ghost btn-sm" onClick={() => setTracking(it)}>
                    {it.tracked ? "Untrack" : "Track stock"}
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => showMoves(it)}>
                    {openMoves === it.id ? "Hide log" : "Log"}
                  </button>
                  <button className="btn btn-ghost btn-sm client-del" onClick={() => toggleActive(it)}>
                    {it.active ? "Deactivate" : "Activate"}
                  </button>
                </div>
              </div>
              {openMoves === it.id && (
                <div className="card" style={{ margin: ".4rem 0 .8rem", padding: ".9rem 1.1rem" }}>
                  {moves.length === 0 && <p className="form-note">No stock movements yet.</p>}
                  {moves.map((m) => (
                    <div key={m.id} className="c" style={{ padding: ".2rem 0", fontSize: ".88rem" }}>
                      <b style={{ color: m.delta < 0 ? "var(--danger)" : "var(--ok)" }}>
                        {m.delta > 0 ? "+" : ""}
                        {m.delta}
                      </b>{" "}
                      · {m.reason}
                      {m.ref ? ` · ${m.ref}` : ""}
                      {m.note ? ` · ${m.note}` : ""} · {fmtDay(m.created_at)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
