import { lazy, Suspense } from "react";
import type { ReactNode } from "react";
import { createBrowserRouter } from "react-router-dom";
import { PublicLayout } from "./components/layout/PublicLayout";
import { Home } from "./pages/Home";
import { NotFound } from "./pages/NotFound";

// Public sub-pages are code-split — the landing (/) stays lean and each route
// loads its own chunk on navigation. Dashboards are split for the same reason.
const Store = lazy(() => import("./pages/Store").then((m) => ({ default: m.Store })));
const ServicesPage = lazy(() => import("./pages/ServicesPage").then((m) => ({ default: m.ServicesPage })));
const WorkPage = lazy(() => import("./pages/WorkPage").then((m) => ({ default: m.WorkPage })));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage").then((m) => ({ default: m.ProjectsPage })));
const AboutPage = lazy(() => import("./pages/AboutPage").then((m) => ({ default: m.AboutPage })));
const ContactPage = lazy(() => import("./pages/ContactPage").then((m) => ({ default: m.ContactPage })));
const ClientDashboard = lazy(() =>
  import("./pages/ClientDashboard").then((m) => ({ default: m.ClientDashboard })),
);
const AdminDashboard = lazy(() =>
  import("./pages/AdminDashboard").then((m) => ({ default: m.AdminDashboard })),
);

// Reserves vertical space while a page chunk loads, so navigation doesn't jump.
function PageFallback() {
  return <div className="container" style={{ minHeight: "70vh" }} aria-hidden="true" />;
}
function P({ children }: { children: ReactNode }) {
  return <Suspense fallback={<PageFallback />}>{children}</Suspense>;
}

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
        { path: "/store", element: <P><Store /></P> },
        { path: "/services", element: <P><ServicesPage /></P> },
        { path: "/work", element: <P><WorkPage /></P> },
        { path: "/projects", element: <P><ProjectsPage /></P> },
        { path: "/about", element: <P><AboutPage /></P> },
        { path: "/contact", element: <P><ContactPage /></P> },
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
