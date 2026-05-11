import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/events": "http://localhost:8000",
      "/stats": "http://localhost:8000",
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
});
