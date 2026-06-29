/* Developer (admin) login. Only an admin-role account may sign in. Port of
   renderLogin() in admin-dash.js. */
import { useState } from "react";
import { Link } from "react-router-dom";
import { API } from "../../../lib/api";
import { useAuth } from "../../../context/AuthContext";

export function AdminLogin({ onAuthed, initialError }: { onAuthed: () => void; initialError?: string }) {
  const { login, logout } = useAuth();
  const [err, setErr] = useState(initialError || "");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget;
    const email = (f.elements.namedItem("email") as HTMLInputElement).value.trim();
    const password = (f.elements.namedItem("password") as HTMLInputElement).value;
    setBusy(true);
    setErr("");
    try {
      const res = await login({ email, password });
      if (res.user.role !== "admin") {
        logout();
        setErr("That account isn't an admin.");
        setBusy(false);
        return;
      }
      onAuthed();
    } catch (e2) {
      API.logout();
      setErr((e2 as Error).message || "Login failed.");
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
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
          <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
            Log in
          </button>
        </form>
        <p className="auth-foot">
          <Link to="/" style={{ color: "var(--muted)" }}>← Back to site</Link>
        </p>
      </div>
    </div>
  );
}
