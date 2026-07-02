/* Account security for the client area: an "unverified email" prompt (when the
   account still needs to confirm its code) and an authenticator-app (2FA) card. */
import { useState } from "react";
import { API } from "../../lib/api";
import { Icon } from "../../lib/icons";
import { useAuth } from "../../context/AuthContext";
import { TwoFactorSetup } from "./TwoFactorSetup";
import type { ApiError, User } from "../../lib/types";

export function AccountSecurity() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div className="sec-cards">
      {user.email_verified === false && <VerifyEmailCard />}
      <TwoFactorCard />
    </div>
  );
}

function VerifyEmailCard() {
  const { user, setUser } = useAuth();
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function verify(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const code = (e.currentTarget.elements.namedItem("code") as HTMLInputElement).value.replace(/\s/g, "");
    setBusy(true);
    setStatus({ type: "ok", msg: "Verifying…" });
    try {
      const u = await API.post<User>("/api/auth/verify", { code });
      setUser(u);
    } catch (err) {
      setStatus({ type: "err", msg: (err as ApiError).message || "That code wasn't right." });
      setBusy(false);
    }
  }

  async function resend() {
    setStatus({ type: "ok", msg: "Sending…" });
    try {
      await API.post("/api/auth/resend");
      setStatus({ type: "ok", msg: "Sent — check your inbox and spam." });
    } catch (err) {
      setStatus({ type: "err", msg: (err as ApiError).message || "Couldn't resend right now." });
    }
  }

  return (
    <div className="card sec-card warn">
      <h3><Icon name="check" size={18} /> Verify your email</h3>
      <p className="form-note">
        We sent a 6-digit code to <b>{user?.email}</b>. Confirm it to place orders.
      </p>
      <form className="form" onSubmit={verify} noValidate>
        <div className="field">
          <input className="input" name="code" inputMode="numeric" autoComplete="one-time-code"
            pattern="\d{6}" maxLength={6} placeholder="123456" required />
        </div>
        {status && <div className={`dash-status show ${status.type}`}>{status.msg}</div>}
        <div className="pay-row">
          <button className="btn btn-primary btn-sm" type="submit" disabled={busy}>Verify</button>
          <button type="button" className="btn btn-outline btn-sm" onClick={resend}>Resend code</button>
        </div>
      </form>
    </div>
  );
}

function TwoFactorCard() {
  const { user, setUser } = useAuth();
  const [mode, setMode] = useState<"idle" | "setup" | "disable">("idle");
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const on = !!user?.totp_enabled;

  async function disable(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const password = (e.currentTarget.elements.namedItem("password") as HTMLInputElement).value;
    setBusy(true);
    setStatus({ type: "ok", msg: "Turning off…" });
    try {
      const u = await API.post<User>("/api/auth/2fa/disable", { password });
      setUser(u);
      setMode("idle");
      setStatus(null);
    } catch (err) {
      setStatus({ type: "err", msg: (err as ApiError).message || "Couldn't turn off 2FA." });
      setBusy(false);
    }
  }

  if (mode === "setup") {
    return (
      <div className="card sec-card">
        <TwoFactorSetup
          heading="Add an authenticator"
          onEnabled={() => { setMode("idle"); setStatus({ type: "ok", msg: "Two-factor is on." }); }}
          onCancel={() => setMode("idle")}
        />
      </div>
    );
  }

  return (
    <div className="card sec-card">
      <h3><Icon name="check" size={18} /> Two-factor authentication</h3>
      <p className="form-note">
        {on
          ? "Your account is protected with an authenticator app."
          : "Add Google/Microsoft Authenticator (or any TOTP app) for an extra layer of security."}
      </p>
      {mode === "disable" ? (
        <form className="form" onSubmit={disable} noValidate>
          <div className="field">
            <label>Confirm your password to turn off 2FA</label>
            <input className="input" name="password" type="password" autoComplete="current-password" required />
          </div>
          {status && <div className={`dash-status show ${status.type}`}>{status.msg}</div>}
          <div className="pay-row">
            <button className="btn btn-primary btn-sm" type="submit" disabled={busy}>Turn off 2FA</button>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => setMode("idle")}>Cancel</button>
          </div>
        </form>
      ) : (
        <>
          {status && <div className={`dash-status show ${status.type}`}>{status.msg}</div>}
          {on ? (
            <button className="btn btn-outline btn-sm" onClick={() => setMode("disable")}>Turn off</button>
          ) : (
            <button className="btn btn-primary btn-sm" onClick={() => setMode("setup")}>Enable 2FA</button>
          )}
        </>
      )}
    </div>
  );
}
