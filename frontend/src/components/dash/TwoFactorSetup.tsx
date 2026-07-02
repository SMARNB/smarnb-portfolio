/* Reusable authenticator-app (TOTP) setup: fetches a secret + QR from the server,
   the user scans it in Google/Microsoft Authenticator (etc.), then confirms a code
   to turn 2FA on. Used by the admin forced-setup screen and the client Security card. */
import { useEffect, useState } from "react";
import { API } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import type { ApiError, TotpSetup, User } from "../../lib/types";

export function TwoFactorSetup({
  heading = "Set up two-factor authentication",
  forced = false,
  onEnabled,
  onCancel,
}: {
  heading?: string;
  forced?: boolean;
  onEnabled: (user: User) => void;
  onCancel?: () => void;
}) {
  const { setUser } = useAuth();
  const [setup, setSetup] = useState<TotpSetup | null>(null);
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let live = true;
    API.post<TotpSetup>("/api/auth/2fa/setup")
      .then((s) => live && setSetup(s))
      .catch((e: ApiError) => live && setStatus({ type: "err", msg: e.message || "Couldn't start 2FA setup." }));
    return () => { live = false; };
  }, []);

  async function confirm(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const code = (e.currentTarget.elements.namedItem("code") as HTMLInputElement).value.replace(/\s/g, "");
    if (!/^\d{6}$/.test(code)) {
      setStatus({ type: "err", msg: "Enter the 6-digit code from your authenticator app." });
      return;
    }
    setBusy(true);
    setStatus({ type: "ok", msg: "Verifying…" });
    try {
      const user = await API.post<User>("/api/auth/2fa/enable", { code });
      setUser(user);
      onEnabled(user);
    } catch (err) {
      setStatus({ type: "err", msg: (err as ApiError).message || "That code wasn't right." });
      setBusy(false);
    }
  }

  return (
    <div className="tfa-setup">
      <h2>{heading}</h2>
      <p className="lead">
        {forced
          ? "Your admin account requires 2FA. Scan this with an authenticator app to continue."
          : "Scan this QR code with Google Authenticator, Microsoft Authenticator, Authy, or any TOTP app."}
      </p>
      {setup ? (
        <>
          <div className="tfa-qr" aria-label="2FA QR code" dangerouslySetInnerHTML={{ __html: setup.qr_svg }} />
          <p className="tfa-secret">
            Can't scan? Enter this key manually:<br />
            <code>{setup.secret}</code>
          </p>
          <form className="form" onSubmit={confirm} noValidate>
            <div className="field">
              <label htmlFor="tfa-code">6-digit code from the app</label>
              <input className="input" id="tfa-code" name="code" inputMode="numeric" autoComplete="one-time-code"
                pattern="\d{6}" maxLength={6} placeholder="123456" required />
            </div>
            {status && <div className={`dash-status show ${status.type}`} role="alert">{status.msg}</div>}
            <button className="btn btn-primary btn-block" type="submit" disabled={busy}>Turn on 2FA</button>
            {!forced && onCancel && (
              <button type="button" className="btn btn-ghost btn-block mt-2" onClick={onCancel}>Cancel</button>
            )}
          </form>
        </>
      ) : (
        <div className={`dash-status ${status ? "show " + status.type : ""}`}>{status?.msg || "Loading…"}</div>
      )}
    </div>
  );
}
