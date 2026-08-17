import tailwindcss from "@tailwindcss/vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  // Built straight into the directory FastAPI serves, so there is one process
  // to run in production rather than two.
  build: { outDir: "../platform/static", emptyOutDir: true },
  server: {
    proxy: { "/results": "http://127.0.0.1:8000" },
  },
});
