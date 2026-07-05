/* Admin "Clients" tab — every registered client account. Proves accounts are
   stored, shows verified/2FA status + order count, and lets the owner reset a
   password (to regain access to a forgotten test login), mark an account
   verified, or delete a throwaway account. */
import { useCallback, useEffect, useState } from "react";
import { API } from "../../../lib/api";
import type { ApiError } from "../../../lib/types";
import { fmtDay } from "../../../lib/format";
import { Icon } from "../../../lib/icons";

interface ClientUser {
  id: number;
  email: string;
  name: string;
  whatsapp: string;
  role: string;
  created_at: string;
  email_verified: boolean;
  totp_enabled: boolean;
  orders: number;
}

export function ClientsTab({ onUnauth }: { onUnauth: () => void }) {
  const [users, setUsers] = useState<ClientUser[] | null>(null);
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);

  const fail = useCallback(
    (e: unknown) => {
      const err = e as ApiError;
      if (err.status === 401) onUnauth();
      else setStatus({ type: "err", msg: err.message || "Something went wrong." });
    },
    [onUnauth],
  );

  const load = useCallback(() => {
    API.get<ClientUser[]>("/api/admin/users").then(setUsers).catch(fail);
  }, [fail]);

  useEffect(() => {
    load();
  }, [load]);

  async function resetPassword(u: ClientUser) {
    const pw = window.prompt(
      `Set a new password for ${u.email} (6+ characters).\nThey can sign in with it right away at /app.`,
    );
    if (pw === null) return;
    if (pw.length < 6) {
      setStatus({ type: "err", msg: "Password must be at least 6 characters." });
      return;
    }
    try {
      await API.post(`/api/admin/users/${u.id}/password`, { password: pw });
      setStatus({ type: "ok", msg: `Password updated for ${u.email}.` });
    } catch (e) {
      fail(e);
    }
  }

  async function markVerified(u: ClientUser) {
    try {
      await API.post(`/api/admin/users/${u.id}/verify`);
      setStatus({ type: "ok", msg: `${u.email} marked as verified.` });
      load();
    } catch (e) {
      fail(e);
    }
  }

  async function remove(u: ClientUser) {
    if (!window.confirm(`Delete ${u.email}? Their orders are kept but detached. This can't be undone.`)) return;
    try {
      await API.del(`/api/admin/users/${u.id}`);
      setStatus({ type: "ok", msg: `Deleted ${u.email}.` });
      load();
    } catch (e) {
      fail(e);
    }
  }

  return (
    <div>
      <div className="dash-head">
        <div>
          <h1>Clients</h1>
          <p>Everyone who has signed up at /app. Reset a password to regain access, or mark an account verified.</p>
        </div>
      </div>

      {status && (
        <div className={`dash-status show ${status.type}`} role="status">
          {status.msg}
        </div>
      )}

      {!users && <p className="form-note">Loading…</p>}

      {users && users.length === 0 && (
        <div className="empty-card card">
          <Icon name="user" size={26} />
          <p>No client accounts yet. When someone signs up at /app they'll appear here.</p>
        </div>
      )}

      {users && users.length > 0 && (
        <div className="svc-list">
          {users.map((u) => (
            <div className="svc-item client-row" key={u.id}>
              <div className="client-main">
                <div className="t">{u.email || "(unreadable — encryption key changed)"}</div>
                <div className="c">
                  {u.name || "—"} · joined {fmtDay(u.created_at)} · {u.orders} order{u.orders === 1 ? "" : "s"}
                </div>
                <div className="client-badges">
                  <span className={`client-badge ${u.email_verified ? "ok" : "warn"}`}>
                    {u.email_verified ? "Verified" : "Unverified"}
                  </span>
                  {u.totp_enabled && <span className="client-badge">2FA</span>}
                </div>
              </div>
              <div className="client-actions">
                <button className="btn btn-outline btn-sm" onClick={() => resetPassword(u)}>
                  Reset password
                </button>
                {!u.email_verified && (
                  <button className="btn btn-ghost btn-sm" onClick={() => markVerified(u)}>
                    Mark verified
                  </button>
                )}
                <button className="btn btn-ghost btn-sm client-del" onClick={() => remove(u)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
