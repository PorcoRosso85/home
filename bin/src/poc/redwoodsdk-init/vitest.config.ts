import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'miniflare',
    environmentOptions: {
      // Miniflare options for Cloudflare Workers environment
      modules: true,
      scriptPath: './src/worker.tsx',
      durableObjects: {
        SESSION_DURABLE_OBJECT: 'SessionDurableObject'
      },
      d1Databases: ['DB'],
      kvNamespaces: ['KV'],
      r2Buckets: ['BUCKET'],
      bindings: {
        ENVIRONMENT: 'test',
        WEBAUTHN_RP_ID: 'localhost',
        WEBAUTHN_APP_NAME: 'Test App'
      }
    },
    setupFiles: ['./tests/setup/test-setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '*.config.ts',
        'generated/',
        'dist/'
      ],
      thresholds: {
        // Set initial thresholds - teams should increase these over time
        statements: 60,
        branches: 50,
        functions: 60,
        lines: 60
      }
    },
    testTimeout: 10000,
    hookTimeout: 10000,
    isolate: true,
    threads: false, // Required for Miniflare
    pool: 'forks', // Better compatibility with Workers environment
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@generated': path.resolve(__dirname, './generated'),
      'cloudflare:workers': path.resolve(__dirname, './tests/setup/mock-cloudflare.ts'),
      'rwsdk/worker': path.resolve(__dirname, './tests/setup/mock-rwsdk.ts'),
      'rwsdk/router': path.resolve(__dirname, './tests/setup/mock-rwsdk.ts'),
      'rwsdk/auth': path.resolve(__dirname, './tests/setup/mock-rwsdk.ts')
    }
  },
  define: {
    'import.meta.env.VITE_IS_DEV_SERVER': JSON.stringify('true')
  }
});