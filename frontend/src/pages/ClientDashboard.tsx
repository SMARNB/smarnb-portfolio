/* Client dashboard (/app) — register/login, then "My Projects" with the live
   milestone tracker, pay flow, cancel and 25s polling. Port of client-dash.js.
   The floating chat widget is available here too (as on the old app.html). */
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "../styles/dashboard.css"; // dashboard-only styles, loaded with this lazy chunk
import { Icon } from "../lib/icons";
import { API } from "../lib/api";
import type { ApiError, Order, PaymentConfig } from "../lib/types";
import { useAuth } from "../context/AuthContext";
import { useDashBody } from "../lib/useDashBody";
import { DashTopbar } from "../components/dash/DashTopbar";
import { ClientAuth } from "../components/dash/ClientAuth";
import { ProjectCard } from "../components/dash/ProjectCard";
import { ChatWidget } from "../components/chat/ChatWidget";

export function ClientDashboard() {
  useDashBody();
  const { user, ready, logout } = useAuth();
  const [payCfg, setPayCfg] = useState<PaymentConfig>({ stripe_enabled: false });
  const [authed, setAuthed] = useState(API.isAuthed());

  // Load the payments config once (decides whether the card button shows).
  useEffect(() => {
    API.get<PaymentConfig>("/api/payments/config")
      .then((c) => c && setPayCfg(c))
      .catch(() => {});
  }, []);

  // Keep local auth flag in sync with the context user.
  useEffect(() => {
    if (user) setAuthed(true);
  }, [user]);

  const onLogout = () => {
    logout();
    setAuthed(false);
  };

  if (!ready) {
    return (
      <>
        <DashTopbar brandText="Client area" pill="Projects" user={null} onLogout={onLogout} />
        <main className="dash-main">
          <div className="container">
            <p className="form-note">Loading…</p>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <DashTopbar brandText="Client area" pill="Projects" user={user} onLogout={onLogout} />
      <main className="dash-main">
        <div className="container">
          {authed && user ? (
            <Projects payCfg={payCfg} onUnauth={onLogout} />
          ) : (
            <ClientAuth onAuthed={() => setAuthed(true)} />
          )}
        </div>
      </main>
      <ChatWidget />
    </>
  );
}

function Projects({ payCfg, onUnauth }: { payCfg: PaymentConfig; onUnauth: () => void }) {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState("");
  const [thanks, setThanks] = useState(false);
  const pollRef = useRef<number | null>(null);

  const load = useCallback(() => {
    API.get<Order[]>("/api/orders/mine")
      .then((list) => {
        setOrders(list);
        setError("");
      })
      .catch((err: ApiError) => {
        if (err.status === 401) {
          onUnauth();
          return;
        }
        setError(err.message || "Couldn't load your projects.");
      });
  }, [onUnauth]);

  // Thank-you banner after a Stripe redirect (?paid=ORDER).
  useEffect(() => {
    const m = /[?&]paid=([^&]+)/.exec(location.search || "");
    if (m) {
      try {
        window.history.replaceState({}, "", location.pathname);
      } catch {
        /* ignore */
      }
      setThanks(true);
    }
  }, []);

  // Initial load + 25s polling for live updates.
  useEffect(() => {
    load();
    pollRef.current = window.setInterval(load, 25000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [load]);

  return (
    <>
      <div className="dash-head">
        <div>
          <h1>My Projects</h1>
          <p>Live status &amp; progress on everything you've ordered.</p>
        </div>
        <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
          <button className="btn btn-ghost btn-sm" onClick={load}>
            <Icon name="arrow" size={16} /> Refresh
          </button>
          <Link className="btn btn-primary btn-sm" to="/store">
            <Icon name="plus" size={16} /> New order
          </Link>
        </div>
      </div>

      {thanks && (
        <div className="form-status ok show" style={{ marginBottom: "1rem" }}>
          Payment received — thank you! Your order will update to Paid shortly.
        </div>
      )}

      <div className="projects">
        {error ? (
          <div className="form-status err show">Couldn't load your projects. {error}</div>
        ) : orders === null ? (
          <p className="form-note">Loading…</p>
        ) : orders.length === 0 ? (
          <div className="card empty-card">
            <div style={{ width: 54, height: 54, margin: "0 auto 1rem" }}>
              <Icon name="box" size={54} />
            </div>
            <h3>No projects yet</h3>
            <p>Once you place an order it'll appear here with live progress.</p>
            <Link className="btn btn-primary mt-4" to="/store">
              Browse services
            </Link>
          </div>
        ) : (
          orders.map((o) => <ProjectCard key={o.public_id} o={o} payCfg={payCfg} onChanged={load} />)
        )}
      </div>
    </>
  );
}
