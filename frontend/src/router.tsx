import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";
import { PublicLayout } from "./components/layout/PublicLayout";
import { Home } from "./pages/Home";
import { Store } from "./pages/Store";
import { ServicesPage } from "./pages/ServicesPage";
import { WorkPage } from "./pages/WorkPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { AboutPage } from "./pages/AboutPage";
import { ContactPage } from "./pages/ContactPage";
import { NotFound } from "./pages/NotFound";

// Public pages are imported eagerly: they live inside the animated <AnimatePresence
// mode="wait"> shell, and a lazy/Suspense child there deadlocks the enter/exit
// transition (the entering page suspends and the old page never unmounts). The
// dashboards are separate top-level routes (outside the shell), so they stay split.
const ClientDashboard = lazy(() =>
  import("./pages/ClientDashboard").then((m) => ({ default: m.ClientDashboard })),
);
const AdminDashboard = lazy(() =>
  import("./pages/AdminDashboard").then((m) => ({ default: m.AdminDashboard })),
);

function DashFallback() {
  return (
    <div className="container" style={{ minHeight: "60vh", display: "grid", placeItems: "center" }}>
      <p className="form-note">Loading…</p>
    </div>
  );
}

export const router = createBrowserRouter(
  [
    {
      element: <PublicLayout />,
      children: [
        { path: "/", element: <Home /> },
        { path: "/store", element: <Store /> },
        { path: "/services", element: <ServicesPage /> },
        { path: "/work", element: <WorkPage /> },
        { path: "/projects", element: <ProjectsPage /> },
        { path: "/about", element: <AboutPage /> },
        { path: "/contact", element: <ContactPage /> },
      ],
    },
    {
      path: "/app",
      element: (
        <Suspense fallback={<DashFallback />}>
          <ClientDashboard />
        </Suspense>
      ),
    },
    {
      path: "/admin",
      element: (
        <Suspense fallback={<DashFallback />}>
          <AdminDashboard />
        </Suspense>
      ),
    },
    { path: "*", element: <NotFound /> },
  ],
  {
    future: {
      v7_relativeSplatPath: true,
      v7_fetcherPersist: true,
      v7_normalizeFormMethod: true,
      v7_partialHydration: true,
      v7_skipActionErrorRevalidation: true,
    },
  },
);
