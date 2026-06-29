import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Tauri 期望 fixed port + 不向远端发请求
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: "127.0.0.1",
  },
});
