/* Client login / register card. Port of renderAuth() in client-dash.js. */
import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export function ClientAuth({ onAuthed }: { onAuthed: () => void }) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
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
        await register({
          email,
          password,
          name: (f.elements.namedItem("name") as HTMLInputElement)?.value.trim() || "",
          whatsapp: (f.elements.namedItem("whatsapp") as HTMLInputElement)?.value.trim() || "",
        });
      } else {
        await login({ email, password });
      }
      onAuthed();
    } catch (err) {
      setStatus({ type: "err", msg: (err as Error).message || "Something went wrong." });
      setBusy(false);
    }
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
