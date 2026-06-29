/* Services tab — list, add/edit (3 package tiers), delete, and a one-time import
   of the built-in catalog into the DB. Port of the Services tab in admin-dash.js. */
import { useCallback, useEffect, useState } from "react";
import { Icon } from "../../../lib/icons";
import { CONFIG } from "../../../lib/config";
import { csv } from "../../../lib/format";
import { API } from "../../../lib/api";
import { services as builtinServices } from "../../../lib/data";
import type { ApiError, ServiceIn, ServiceOut, ServicePackage } from "../../../lib/types";

const ICON_CHOICES = ["spark", "code", "server", "layout", "bot", "eye", "pen", "box", "rocket", "chat", "doc", "shield", "clock", "card"];
const TIERS = ["Basic", "Standard", "Premium"];

function builtinToService(b: (typeof builtinServices)[number]): ServiceIn {
  return {
    title: b.title,
    category: b.category || "Development",
    icon: b.icon || "spark",
    short: b.short || "",
    tags: b.tags || [],
    packages: b.packages || [],
    deliverables: b.deliverables || [],
    active: true,
    sort_order: 0,
    slug: b.id,
  };
}

export function ServicesTab({ onUnauth }: { onUnauth: () => void }) {
  const [list, setList] = useState<ServiceOut[] | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<ServiceOut | null | "new" | undefined>(undefined);
  const [importing, setImporting] = useState(false);

  const load = useCallback(() => {
    API.get<ServiceOut[]>("/api/admin/services")
      .then(setList)
      .catch((err: ApiError) => {
        if (err.status === 401 || err.status === 403) onUnauth();
        else setError(err.message || "Failed to load.");
      });
  }, [onUnauth]);

  useEffect(() => {
    load();
  }, [load]);

  const have = new Set((list || []).map((s) => s.slug));
  const missing = builtinServices.filter((b) => !have.has(b.id));

  function doImport() {
    setImporting(true);
    API.post("/api/admin/services/import", { services: missing.map(builtinToService) })
      .then(() => {
        setImporting(false);
        load();
      })
      .catch((err: ApiError) => {
        setImporting(false);
        window.alert(err.message || "Import failed.");
      });
  }
  function del(id: number) {
    if (!window.confirm("Delete this service?")) return;
    API.del("/api/admin/services/" + id).then(load).catch((err: ApiError) => window.alert(err.message || "Failed."));
  }

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
        <p className="form-note" style={{ maxWidth: "44rem", margin: 0 }}>
          These are the services shown on your site. Add, edit, hide or delete any of them here — changes appear on the
          next site load.
        </p>
        <button className="btn btn-primary btn-sm" onClick={() => setEditing("new")}>
          <Icon name="plus" size={16} /> Add service
        </button>
      </div>

      {list && missing.length > 0 && (
        <div className="card" style={{ border: "1px solid var(--accent)", background: "var(--grad-soft)", marginBottom: "1.2rem" }}>
          <b>Bring your built-in services into the dashboard</b>
          <p style={{ color: "var(--muted)", fontSize: ".92rem", margin: ".4rem 0 .9rem" }}>
            Your site has <b>{missing.length}</b> built-in service(s) that aren't managed here yet. Import them once to
            edit, hide, reorder or delete them like any other.
          </p>
          <button className="btn btn-primary btn-sm" disabled={importing} onClick={doImport}>
            <Icon name="plus" size={16} /> {importing ? "Importing…" : `Import ${missing.length} built-in service(s)`}
          </button>
        </div>
      )}

      {editing !== undefined && (
        <ServiceForm
          svc={editing === "new" ? null : editing}
          onClose={() => setEditing(undefined)}
          onSaved={() => {
            setEditing(undefined);
            load();
          }}
        />
      )}

      <div className="svc-list" id="svcList">
        {error ? (
          <div className="form-status err show">{error}</div>
        ) : list === null ? (
          <p className="form-note">Loading…</p>
        ) : list.length === 0 ? (
          <p className="form-note">No services yet — click “Add service”, or import your built-ins above.</p>
        ) : (
          list.map((s) => (
            <div className={`svc-item${s.active ? "" : " off"}`} key={s.id}>
              <div>
                <div className="t">{s.title}</div>
                <div className="c">
                  {s.category} · {s.packages ? s.packages.length : 0} package(s){s.active ? "" : " · hidden"}
                </div>
              </div>
              <div style={{ display: "flex", gap: ".5rem" }}>
                <button className="btn btn-outline btn-sm" onClick={() => setEditing(s)}>Edit</button>
                <button className="btn btn-outline btn-sm" onClick={() => del(s.id)}>Delete</button>
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );
}

function ServiceForm({ svc, onClose, onSaved }: { svc: ServiceOut | null; onClose: () => void; onSaved: () => void }) {
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const pk = (svc && svc.packages) || [];

  function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget;
    const get = (n: string) => (f.elements.namedItem(n) as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement)?.value ?? "";
    const title = get("title").trim();
    if (!title) {
      setStatus({ type: "err", msg: "Title is required." });
      return;
    }
    const packages: ServicePackage[] = [];
    TIERS.forEach((tier, i) => {
      const priceRaw = (f.elements.namedItem(`price-${i}`) as HTMLInputElement).value;
      const price = parseFloat(priceRaw);
      if (priceRaw === "" || isNaN(price)) return;
      packages.push({
        tier,
        price,
        delivery: get(`del-${i}`).trim(),
        revisions: 2,
        summary: get(`sum-${i}`).trim(),
        features: csv(get(`feat-${i}`)),
        popular: i === 1,
      });
    });
    const payload: ServiceIn = {
      title,
      category: get("category").trim() || "Development",
      icon: get("icon"),
      short: get("short").trim(),
      tags: csv(get("tags")),
      packages,
      deliverables: [],
      active: (f.elements.namedItem("active") as HTMLInputElement).checked,
      sort_order: 0,
    };
    setStatus({ type: "ok", msg: "Saving…" });
    const p = svc ? API.patch("/api/admin/services/" + svc.id, payload) : API.post("/api/admin/services", payload);
    p.then(onSaved).catch((err: ApiError) => setStatus({ type: "err", msg: err.message || "Failed." }));
  }

  return (
    <div className="card" style={{ marginBottom: "1.2rem" }}>
      <h3 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>{svc ? "Edit service" : "Add a service"}</h3>
      {status && <div className={`dash-status show ${status.type}`}>{status.msg}</div>}
      <form onSubmit={save}>
        <div className="two">
          <div className="field">
            <label>Title</label>
            <input className="input" name="title" defaultValue={svc ? svc.title : ""} placeholder="e.g. Discord Bot Development" />
          </div>
          <div className="field">
            <label>Category</label>
            <input className="input" name="category" defaultValue={svc ? svc.category : "Development"} placeholder="Development / Design / Automation…" />
          </div>
        </div>
        <div className="two">
          <div className="field">
            <label>Icon</label>
            <select className="select" name="icon" defaultValue={svc ? svc.icon : "spark"}>
              {ICON_CHOICES.map((ic) => (
                <option key={ic}>{ic}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Tags (comma-separated)</label>
            <input className="input" name="tags" defaultValue={svc ? (svc.tags || []).join(", ") : ""} />
          </div>
        </div>
        <div className="field">
          <label>Short description</label>
          <textarea className="textarea" name="short" style={{ minHeight: 70 }} defaultValue={svc ? svc.short : ""} />
        </div>
        <label style={{ fontWeight: 600, fontSize: ".88rem" }}>
          Packages <span style={{ color: "var(--muted)", fontWeight: 400 }}>(fill the tiers you offer; blank price = skipped)</span>
        </label>
        <div style={{ marginTop: ".5rem" }}>
          {TIERS.map((tier, i) => {
            const p = pk[i] || ({} as ServicePackage);
            const label = i === 1 ? "Standard (popular)" : tier;
            return (
              <div className="card" style={{ padding: "1rem", marginBottom: ".6rem" }} key={tier}>
                <b style={{ fontSize: ".85rem" }}>{label}</b>
                <div className="two" style={{ marginTop: ".5rem" }}>
                  <div className="field">
                    <label>Price ({CONFIG.currency})</label>
                    <input className="input" name={`price-${i}`} type="number" min="0" defaultValue={p.price ?? ""} />
                  </div>
                  <div className="field">
                    <label>Delivery</label>
                    <input className="input" name={`del-${i}`} defaultValue={p.delivery || ""} placeholder="e.g. 5 days" />
                  </div>
                </div>
                <div className="field">
                  <label>Summary</label>
                  <input className="input" name={`sum-${i}`} defaultValue={p.summary || ""} />
                </div>
                <div className="field">
                  <label>Features (comma-separated)</label>
                  <input className="input" name={`feat-${i}`} defaultValue={(p.features || []).join(", ")} />
                </div>
              </div>
            );
          })}
        </div>
        <label className="field" style={{ flexDirection: "row", alignItems: "center", gap: ".5rem", margin: ".4rem 0 1rem" }}>
          <input type="checkbox" name="active" defaultChecked={!svc || svc.active} /> Active (visible on site)
        </label>
        <div style={{ display: "flex", gap: ".6rem" }}>
          <button className="btn btn-primary" type="submit">{svc ? "Save changes" : "Create service"}</button>
          <button className="btn btn-ghost" type="button" onClick={onClose}>Cancel</button>
        </div>
      </form>
    </div>
  );
}
