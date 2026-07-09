import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// PORT lets a second session run its own dev server when 5180 is taken. Typed via
// globalThis so we don't need @types/node just for this one read.
const devPort =
  Number((globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env?.PORT) || 5180;

// Single-origin app: in dev we proxy /api to the FastAPI backend on :8100; in
// production FastAPI serves the built files in frontend/dist and handles /api.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: devPort,
    proxy: {
      "/api": {
        target: "http://localhost:8100",
        changeOrigin: true,
      },
    },
  },
});
