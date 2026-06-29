import { lazy, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";
import { PublicLayout } from "./components/layout/PublicLayout";
import { Home } from "./pages/Home";
import { Store } from "./pages/Store";
import { NotFound } from "./pages/NotFound";

// Dashboards are code-split so the public marketing pages don't ship their code.
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
