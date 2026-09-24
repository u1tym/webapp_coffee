import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  base: "/portal_coffee_ledger/",
  plugins: [vue()],
  server: {
    port: 5173,
  },
});
