/* Developer dashboard (/admin) — admin-only login, then tabbed control room:
   Orders, Inbox (live chat), Reviews, Services, Bot training. Cross-tab badge
   polling (unread chats, pending reviews, unanswered questions). Port of
   admin-dash.js. */
import { useCallback, useEffect, useRef, useState } from "react";
import "../styles/dashboard.css"; // dashboard-only styles, loaded with this lazy chunk
import { API } from "../lib/api";
import type { ConversationSummary, TestimonialAdmin, BotUnanswered } from "../lib/types";
import { useAuth } from "../context/AuthContext";
import { useDashBody } from "../lib/useDashBody";
import { DashTopbar } from "../components/dash/DashTopbar";
import { AdminLogin } from "../components/dash/admin/AdminLogin";
import { OrdersTab } from "../components/dash/admin/OrdersTab";
import { InboxTab } from "../components/dash/admin/InboxTab";
import { ReviewsTab } from "../components/dash/admin/ReviewsTab";
import { ServicesTab } from "../components/dash/admin/ServicesTab";
import { BotTab } from "../components/dash/admin/BotTab";
import { SeoTab } from "../components/dash/admin/SeoTab";
import { BlogTab } from "../components/dash/admin/BlogTab";

type Tab = "orders" | "inbox" | "reviews" | "services" | "blog" | "bot" | "seo";
const HASH_TAB: Record<string, Tab> = { "#services": "services", "#blog": "blog", "#inbox": "inbox", "#reviews": "reviews", "#bot": "bot", "#seo": "seo" };

export function AdminDashboard() {
  useDashBody();
  const { user, ready, logout } = useAuth();
  const [signedIn, setSignedIn] = useState(false);

  const isAdmin = signedIn || (!!user && user.role === "admin");

  if (!ready) {
    return (
      <>
        <DashTopbar brandText="Developer" pill="Admin" user={null} onLogout={logout} />
        <main className="dash-main"><div className="container"><p className="form-note">Loading…</p></div></main>
      </>
    );
  }

  if (!isAdmin) {
    return (
      <>
        <DashTopbar brandText="Developer" pill="Admin" user={null} onLogout={logout} />
        <main className="dash-main">
          <div className="container">
            <AdminLogin
              onAuthed={() => setSignedIn(true)}
              initialError={user && user.role !== "admin" ? "That account isn't an admin." : undefined}
            />
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <DashTopbar brandText="Developer" pill="Admin" user={user} onLogout={() => { logout(); setSignedIn(false); }} />
      <main className="dash-main">
        <div className="container">
          <AdminShell onUnauth={() => { logout(); setSignedIn(false); }} />
        </div>
      </main>
    </>
  );
}

function AdminShell({ onUnauth }: { onUnauth: () => void }) {
  const [tab, setTab] = useState<Tab>(() => HASH_TAB[location.hash] || "orders");
  const [convs, setConvs] = useState<ConversationSummary[] | null>(null);
  const [inboxBadge, setInboxBadge] = useState(0);
  const [reviewsBadge, setReviewsBadge] = useState(0);
  const [botBadge, setBotBadge] = useState(0);
  const badgeTimer = useRef<number | null>(null);

  const pollBadges = useCallback(() => {
    API.get<ConversationSummary[]>("/api/admin/chat/conversations")
      .then((list) => {
        setConvs(list);
        setInboxBadge(list.reduce((n, c) => n + (c.unread || 0), 0));
      })
      .catch(() => {});
    API.get<TestimonialAdmin[]>("/api/admin/testimonials")
      .then((list) => setReviewsBadge(list.filter((t) => t.status === "pending").length))
      .catch(() => {});
    API.get<BotUnanswered[]>("/api/admin/chat/unanswered")
      .then((list) => setBotBadge(list.length))
      .catch(() => {});
  }, []);

  useEffect(() => {
    pollBadges();
    badgeTimer.current = window.setInterval(pollBadges, 30000);
    return () => {
      if (badgeTimer.current) clearInterval(badgeTimer.current);
    };
  }, [pollBadges]);

  const TABS: { id: Tab; label: string; badge?: number }[] = [
    { id: "orders", label: "Orders" },
    { id: "inbox", label: "Inbox", badge: inboxBadge },
    { id: "reviews", label: "Reviews", badge: reviewsBadge },
    { id: "services", label: "Services" },
    { id: "blog", label: "Blog" },
    { id: "bot", label: "Bot training", badge: botBadge },
    { id: "seo", label: "SEO" },
  ];

  return (
    <>
      <div className="dash-head">
        <div>
          <h1>Developer Dashboard</h1>
          <p>Orders, chat, reviews &amp; services — your private control room.</p>
        </div>
      </div>

      <div className="admin-tabs">
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
            {t.label}
            {t.badge ? <span className="tab-badge">{t.badge > 99 ? "99+" : t.badge}</span> : null}
          </button>
        ))}
      </div>

      <div id="tabBody">
        {tab === "orders" && <OrdersTab onUnauth={onUnauth} onStatsChange={pollBadges} />}
        {tab === "inbox" && (
          <InboxTab onUnauth={onUnauth} list={convs} reloadList={pollBadges} onActivity={pollBadges} />
        )}
        {tab === "reviews" && <ReviewsTab onUnauth={onUnauth} onChanged={pollBadges} />}
        {tab === "services" && <ServicesTab onUnauth={onUnauth} />}
        {tab === "blog" && <BlogTab onUnauth={onUnauth} />}
        {tab === "bot" && <BotTab onUnauth={onUnauth} onChanged={pollBadges} />}
        {tab === "seo" && <SeoTab onUnauth={onUnauth} />}
      </div>
    </>
  );
}
