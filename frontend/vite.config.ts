import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Single-origin app: in dev we proxy /api to the FastAPI backend on :8101; in
// production FastAPI serves the built files in frontend/dist and handles /api.
// (3D-redesign copy: ports 8101/5181 so it can run beside the original 8100/5180.)
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5181,
    proxy: {
      "/api": {
        target: "http://localhost:8101",
        changeOrigin: true,
      },
    },
  },
});
