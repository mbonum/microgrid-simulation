import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// API target is configurable so the Vite dev server can reach the backend
// from inside a container (see docker-compose.yml: VITE_API_TARGET=http://api:8000).
const apiTarget = process.env.VITE_API_TARGET ?? "http://localhost:8000";
const wsTarget = apiTarget.replace(/^http/, "ws");

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/simulation": apiTarget,
      "/ws": { target: wsTarget, ws: true },
    },
  },
});
