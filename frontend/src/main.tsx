import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import "./styles/global.css";
import "./styles/dashboard.css";
import "./styles/chat.css";

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
