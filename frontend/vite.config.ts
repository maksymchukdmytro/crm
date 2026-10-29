import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Збірка з відносними шляхами: сервер додає <base href="/crm/"> (або "/"), тож одна збірка
// працює за будь-яким префіксом. У режимі розробки запити /api проксуються на бекенд.
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: { outDir: "dist", sourcemap: false, chunkSizeWarningLimit: 900 },
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8077" },
  },
});
