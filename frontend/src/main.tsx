import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import "./lib/prefetch"; // fire /api/services + /api/testimonials in parallel, ASAP
import "./styles/global.css";
import "./styles/chat.css";
// dashboard.css is imported by the lazy /app + /admin chunks (not on the landing
// pages), so it no longer adds render-blocking CSS to the marketing pages.

// Apply the saved theme before first render to minimise a flash of the wrong
// theme. Runs here (an external module) so it satisfies the strict CSP
// script-src 'self' — an inline <script> in index.html would be blocked.
(function applyInitialTheme() {
  try {
    const t =
      localStorage.getItem("alira_theme") ||
      (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    document.documentElement.setAttribute("data-theme", t);
  } catch {
    /* ignore */
  }
})();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
);
