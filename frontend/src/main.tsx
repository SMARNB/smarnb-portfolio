import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import "./lib/prefetch"; // fire /api/services + /api/testimonials in parallel, ASAP
// Self-hosted type system (bundled by Vite → hashed, same-origin /assets, immutable
// cache). First-party: no fonts.googleapis.com / gstatic runtime load, so the strict
// CSP (font-src 'self') is satisfied without any change. Roman-only (wght) — italics
// are not used. Subsets are unicode-range gated, so only Latin actually downloads.
import "@fontsource-variable/space-grotesk/wght.css"; // display / headings
import "@fontsource-variable/hanken-grotesk/wght.css"; // body / UI
import "@fontsource-variable/jetbrains-mono/wght.css"; // labels / prices / stats (signature)
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

// Dismiss the shell splash screen once the app has painted. Shown at least ~400ms
// (so it never flashes as a glitch on fast loads) and removed after the fade; a
// safety timeout guarantees it can never get stuck if something stalls.
(function dismissSplash() {
  const t0 = performance.now();
  const hide = () => {
    const el = document.getElementById("splash");
    if (!el) return;
    el.classList.add("splash--hide");
    const done = () => el.remove();
    el.addEventListener("transitionend", done, { once: true });
    setTimeout(done, 700); // fallback if transitionend doesn't fire
  };
  const schedule = () =>
    setTimeout(hide, Math.max(0, 400 - (performance.now() - t0)));
  // Wait for the first React paint (two frames), then respect the minimum.
  requestAnimationFrame(() => requestAnimationFrame(schedule));
  // Hard safety net: never let the splash linger past 6s regardless.
  setTimeout(hide, 6000);
})();
