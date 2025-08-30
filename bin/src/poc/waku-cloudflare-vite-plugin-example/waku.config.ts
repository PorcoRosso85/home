import { defineConfig } from "waku/config";
import { cloudflare } from "@cloudflare/vite-plugin";

export default defineConfig({
  // unstable_honoEnhancer: "./waku.hono-enhancer",
  // middleware: [
  //   "waku/middleware/context",
  //   "waku/middleware/dev-server",
  //   "./waku.cloudflare-middleware",
  //   "waku/middleware/handler",
  // ],
  vite: {
    environments: {
      rsc: {
        build: {
          rollupOptions: {
            input: {
              index: "./src/server.ts",
            },
          },
        },
      },
    },
    plugins: [
      cloudflare({
        viteEnvironment: { name: "rsc" }
      }),
    ],
  },
});
