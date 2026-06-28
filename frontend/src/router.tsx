import { createBrowserRouter } from "react-router-dom";
import { PublicLayout } from "./components/layout/PublicLayout";
import { Home } from "./pages/Home";
import { Store } from "./pages/Store";
import { ClientDashboard } from "./pages/ClientDashboard";
import { AdminDashboard } from "./pages/AdminDashboard";
import { NotFound } from "./pages/NotFound";

export const router = createBrowserRouter(
  [
    {
      element: <PublicLayout />,
      children: [
        { path: "/", element: <Home /> },
        { path: "/store", element: <Store /> },
      ],
    },
    { path: "/app", element: <ClientDashboard /> },
    { path: "/admin", element: <AdminDashboard /> },
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
