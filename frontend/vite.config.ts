import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Single-origin app: in dev we proxy /api to the FastAPI backend on :8100; in
// production FastAPI serves the built files in frontend/dist and handles /api.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5180,
    proxy: {
      "/api": {
        target: "http://localhost:8100",
        changeOrigin: true,
      },
    },
  },
});
