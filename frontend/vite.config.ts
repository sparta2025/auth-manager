import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // In dev mode, proxy all /auth, /admin, /reports, /documents, /settings to backend
      "/auth": { target: "http://localhost:8000", changeOrigin: true },
      "/admin": { target: "http://localhost:8000", changeOrigin: true },
      "/reports": { target: "http://localhost:8000", changeOrigin: true },
      "/documents": { target: "http://localhost:8000", changeOrigin: true },
      "/settings": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
