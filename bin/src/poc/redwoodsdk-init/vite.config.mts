import { defineConfig } from "vite";
import { redwood } from "rwsdk/vite";
import { cloudflare } from "@cloudflare/vite-plugin";

export default defineConfig({
  plugins: [
    cloudflare({
      viteEnvironment: { name: "worker" },
      // Try to use external wrangler binary on NixOS
      miniflare: {
        binPath: process.env.WRANGLER_BINARY,
      }
    }),
    redwood(),
  ],
});
