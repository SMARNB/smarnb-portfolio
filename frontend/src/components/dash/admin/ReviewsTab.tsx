/* Reviews tab — moderate client testimonials (approve / reject / delete). Port of
   the Reviews tab in admin-dash.js. */
import { useCallback, useEffect, useState } from "react";
import { API } from "../../../lib/api";
import type { ApiError, TestimonialAdmin } from "../../../lib/types";

const RANK: Record<string, number> = { pending: 0, approved: 1, rejected: 2 };

export function ReviewsTab({ onUnauth, onChanged }: { onUnauth: () => void; onChanged: () => void }) {
  const [list, setList] = useState<TestimonialAdmin[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    API.get<TestimonialAdmin[]>("/api/admin/testimonials")
      .then(setList)
      .catch((err: ApiError) => {
        if (err.status === 401 || err.status === 403) onUnauth();
        else setError(err.message || "Failed.");
      });
  }, [onUnauth]);

  useEffect(() => {
    load();
  }, [load]);

  function setStatus(id: number, status: string) {
    API.patch("/api/admin/testimonials/" + id, { status })
      .then(() => {
        load();
        onChanged();
      })
      .catch((err: ApiError) => window.alert(err.message || "Failed."));
  }
  function del(id: number) {
    if (!window.confirm("Delete this review permanently?")) return;
    API.del("/api/admin/testimonials/" + id)
      .then(() => {
        load();
        onChanged();
      })
      .catch((err: ApiError) => window.alert(err.message || "Failed."));
  }

  const sorted = list ? list.slice().sort((a, b) => (RANK[a.status] || 0) - (RANK[b.status] || 0)) : [];

  return (
    <>
      <p className="form-note" style={{ marginBottom: "1rem" }}>
        Reviews submitted from your site. Approve to publish them; reject or delete spam.
      </p>
      <div id="revList">
        {error ? (
          <div className="form-status err show">{error}</div>
        ) : list === null ? (
          <p className="form-note">Loading…</p>
        ) : sorted.length === 0 ? (
          <p className="form-note">No reviews submitted yet.</p>
        ) : (
          sorted.map((t) => {
            const chipClass = t.status === "approved" ? "st-delivered" : t.status === "rejected" ? "st-cancelled" : "st-received";
            return (
              <div className="rev-item card" key={t.id}>
                <div className="rev-top">
                  <div>
                    <b>{t.name}</b> <span style={{ color: "var(--muted)" }}>{t.role || ""}{t.location ? ` · ${t.location}` : ""}</span>
                    <div style={{ color: "var(--warn)", letterSpacing: "2px" }}>{"★".repeat(t.rating || 0)}</div>
                  </div>
                  <span className={`status-chip ${chipClass}`}>{t.status}</span>
                </div>
                <p style={{ margin: ".5rem 0" }}>“{t.text}”</p>
                <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
                  {t.status !== "approved" && (
                    <button className="btn btn-primary btn-sm" onClick={() => setStatus(t.id, "approved")}>Approve</button>
                  )}
                  {t.status !== "rejected" && (
                    <button className="btn btn-outline btn-sm" onClick={() => setStatus(t.id, "rejected")}>Reject</button>
                  )}
                  <button className="btn btn-outline btn-sm" onClick={() => del(t.id)}>Delete</button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </>
  );
}
