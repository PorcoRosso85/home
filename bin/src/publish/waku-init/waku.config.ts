import { defineConfig } from 'waku/config';

export default defineConfig({
  unstable_honoEnhancer: './waku.hono-enhancer',
  middleware: [
    'waku/middleware/context',
    'waku/middleware/dev-server',
    './waku.cloudflare-middleware',
    'waku/middleware/handler',
  ],
  vite: {
    optimizeDeps: {
      exclude: ['sqlite'],
    },
    server: {
      host: '127.0.0.1', // IPv4で明示的にリッスン
      port: 3000,
    },
  },
});
