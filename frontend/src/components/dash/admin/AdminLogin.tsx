/* Developer (admin) login. Only an admin-role account may sign in. 2FA is required
   for the admin: after the password it asks for the authenticator code, and on the
   first login it forces 2FA setup. */
import { useState } from "react";
import { Link } from "react-router-dom";
import { API } from "../../../lib/api";
import { useAuth } from "../../../context/AuthContext";
import { TwoFactorSetup } from "../TwoFactorSetup";
import type { ApiError } from "../../../lib/types";

export function AdminLogin({ onAuthed, initialError }: { onAuthed: () => void; initialError?: string }) {
  const { login, logout } = useAuth();
  const [err, setErr] = useState(initialError || "");
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState<"form" | "totp" | "setup">("form");
  const [creds, setCreds] = useState<{ email: string; password: string }>({ email: "", password: "" });

  async function attempt(email: string, password: string, totp_code?: string) {
    setBusy(true);
    setErr("");
    try {
      const res = await login({ email, password, totp_code });
      if (res.totp_required) {
        setCreds({ email, password });
        setStep("totp");
        setBusy(false);
        return;
      }
      if (!res.user || res.user.role !== "admin") {
        logout();
        setErr("That account isn't an admin.");
        setBusy(false);
        return;
      }
      if (res.must_setup_2fa) {
        setStep("setup");
        setBusy(false);
        return;
      }
      onAuthed();
    } catch (e2) {
      API.logout();
      setErr((e2 as ApiError).message || "Login failed.");
      setBusy(false);
    }
  }

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget;
    const email = (f.elements.namedItem("email") as HTMLInputElement).value.trim();
    const password = (f.elements.namedItem("password") as HTMLInputElement).value;
    attempt(email, password);
  }

  function onTotp(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const code = (e.currentTarget.elements.namedItem("code") as HTMLInputElement).value.replace(/\s/g, "");
    attempt(creds.email, creds.password, code);
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        {step === "setup" ? (
          <TwoFactorSetup forced heading="Secure your admin account" onEnabled={() => onAuthed()} />
        ) : step === "totp" ? (
          <>
            <h1>Two-factor code</h1>
            <p className="lead">Enter the 6-digit code from your authenticator app.</p>
            <form className="form" onSubmit={onTotp} noValidate>
              <div className="field">
                <label htmlFor="a-code">6-digit code</label>
                <input className="input" id="a-code" name="code" inputMode="numeric" autoComplete="one-time-code"
                  pattern="\d{6}" maxLength={6} placeholder="123456" required autoFocus />
              </div>
              <div className={`dash-status ${err ? "show err" : ""}`}>{err}</div>
              <button className="btn btn-primary btn-block" type="submit" disabled={busy}>Verify</button>
            </form>
          </>
        ) : (
          <>
            <h1>Developer login</h1>
            <p className="lead">Private area — only the developer account can sign in.</p>
            <form className="form" onSubmit={onSubmit} noValidate>
              <div className="field">
                <label htmlFor="l-email">Email</label>
                <input className="input" id="l-email" name="email" type="email" required autoComplete="email" />
              </div>
              <div className="field">
                <label htmlFor="l-pass">Password</label>
                <input className="input" id="l-pass" name="password" type="password" required autoComplete="current-password" />
              </div>
              <div className={`dash-status ${err ? "show err" : ""}`}>{err}</div>
              <button className="btn btn-primary btn-block" type="submit" disabled={busy}>Log in</button>
            </form>
          </>
        )}
        <p className="auth-foot">
          <Link to="/" style={{ color: "var(--muted)" }}>← Back to site</Link>
        </p>
      </div>
    </div>
  );
}
