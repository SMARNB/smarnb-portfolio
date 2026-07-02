/* Client login / register with the anti-spam flow: registration may require an
   emailed 6-digit code before the account is usable, and login may require a 2FA
   code when the account has an authenticator enabled. */
import { useState } from "react";
import { Link } from "react-router-dom";
import { API } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import type { ApiError, User } from "../../lib/types";

type Step = "form" | "verify" | "totp";

export function ClientAuth({ onAuthed }: { onAuthed: () => void }) {
  const { login, register, setUser } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [step, setStep] = useState<Step>("form");
  const [creds, setCreds] = useState<{ email: string; password: string }>({ email: "", password: "" });
  const [status, setStatus] = useState<{ type: string; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const reg = mode === "register";

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget;
    const email = (f.elements.namedItem("email") as HTMLInputElement).value.trim();
    const password = (f.elements.namedItem("password") as HTMLInputElement).value;
    if (!email || password.length < 6) {
      setStatus({ type: "err", msg: "Enter your email and a password (6+ characters)." });
      return;
    }
    setBusy(true);
    setStatus({ type: "ok", msg: "Please wait…" });
    try {
      if (reg) {
        const res = await register({
          email,
          password,
          name: (f.elements.namedItem("name") as HTMLInputElement)?.value.trim() || "",
          whatsapp: (f.elements.namedItem("whatsapp") as HTMLInputElement)?.value.trim() || "",
        });
        if (res.verification_required) {
          setCreds({ email, password });
          setStep("verify");
          setStatus({ type: "ok", msg: "We emailed you a 6-digit code — enter it below." });
          setBusy(false);
          return;
        }
        onAuthed();
      } else {
        const res = await login({ email, password });
        if (res.totp_required) {
          setCreds({ email, password });
          setStep("totp");
          setStatus(null);
          setBusy(false);
          return;
        }
        onAuthed();
      }
    } catch (err) {
      setStatus({ type: "err", msg: (err as ApiError).message || "Something went wrong." });
      setBusy(false);
    }
  }

  async function submitCode(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const code = (e.currentTarget.elements.namedItem("code") as HTMLInputElement).value.replace(/\s/g, "");
    setBusy(true);
    setStatus({ type: "ok", msg: "Verifying…" });
    try {
      if (step === "verify") {
        const user = await API.post<User>("/api/auth/verify", { code });
        setUser(user);
        onAuthed();
      } else {
        const res = await login({ email: creds.email, password: creds.password, totp_code: code });
        if (res.access_token) onAuthed();
        else setStatus({ type: "err", msg: "That code wasn't right." });
        setBusy(false);
      }
    } catch (err) {
      setStatus({ type: "err", msg: (err as ApiError).message || "That code wasn't right." });
      setBusy(false);
    }
  }

  async function resend() {
    setStatus({ type: "ok", msg: "Sending a new code…" });
    try {
      await API.post("/api/auth/resend");
      setStatus({ type: "ok", msg: "Sent — check your inbox (and spam)." });
    } catch (err) {
      setStatus({ type: "err", msg: (err as ApiError).message || "Couldn't resend right now." });
    }
  }

  if (step !== "form") {
    const verifying = step === "verify";
    return (
      <div className="auth-wrap">
        <div className="card auth-card">
          <h1>{verifying ? "Verify your email" : "Two-factor code"}</h1>
          <p className="lead">
            {verifying
              ? `Enter the 6-digit code we sent to ${creds.email}.`
              : "Enter the 6-digit code from your authenticator app."}
          </p>
          <form className="form" onSubmit={submitCode} noValidate>
            <div className="field">
              <label htmlFor="c-code">6-digit code</label>
              <input className="input" id="c-code" name="code" inputMode="numeric" autoComplete="one-time-code"
                pattern="\d{6}" maxLength={6} placeholder="123456" required autoFocus />
            </div>
            {status && <div className={`dash-status show ${status.type}`} role="alert">{status.msg}</div>}
            <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
              {verifying ? "Verify" : "Continue"}
            </button>
          </form>
          <p className="auth-foot">
            {verifying ? (
              <a href="#" style={{ color: "var(--accent-2)", fontWeight: 600 }}
                onClick={(e) => { e.preventDefault(); resend(); }}>Resend code</a>
            ) : (
              <a href="#" style={{ color: "var(--muted)" }}
                onClick={(e) => { e.preventDefault(); setStep("form"); setStatus(null); }}>← Back</a>
            )}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <h1>{reg ? "Create your account" : "Welcome back"}</h1>
        <p className="lead">Track your projects, watch live progress, and place new orders.</p>
        <div className="seg" role="tablist">
          <button aria-selected={!reg} onClick={() => { setMode("login"); setStatus(null); }}>Log in</button>
          <button aria-selected={reg} onClick={() => { setMode("register"); setStatus(null); }}>Sign up</button>
        </div>
        <form className="form" onSubmit={onSubmit} noValidate>
          {reg && (
            <div className="field">
              <label htmlFor="f-name">Name</label>
              <input className="input" id="f-name" name="name" autoComplete="name" />
            </div>
          )}
          <div className="field">
            <label htmlFor="f-email">Email</label>
            <input className="input" id="f-email" name="email" type="email" autoComplete="email" required />
          </div>
          <div className="field">
            <label htmlFor="f-pass">Password</label>
            <input
              className="input"
              id="f-pass"
              name="password"
              type="password"
              autoComplete={reg ? "new-password" : "current-password"}
              required
              minLength={6}
            />
          </div>
          {reg && (
            <div className="field">
              <label htmlFor="f-wa">WhatsApp <span style={{ color: "var(--muted)", fontWeight: 400 }}>(optional)</span></label>
              <input className="input" id="f-wa" name="whatsapp" autoComplete="tel" />
            </div>
          )}
          {status && <div className={`dash-status show ${status.type}`} role="alert">{status.msg}</div>}
          <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
            {reg ? "Create account" : "Log in"}
          </button>
        </form>
        <p className="auth-foot">
          {reg ? "Already have an account? " : "New here? "}
          <a href="#" style={{ color: "var(--accent-2)", fontWeight: 600 }} onClick={(e) => { e.preventDefault(); setMode(reg ? "login" : "register"); setStatus(null); }}>
            {reg ? "Log in" : "Create an account"}
          </a>
        </p>
        <p className="auth-foot">
          <Link to="/" style={{ color: "var(--muted)" }}>← Back to site</Link>
        </p>
      </div>
    </div>
  );
}
