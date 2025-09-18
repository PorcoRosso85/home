import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    setupFiles: ['./test/setup.ts'],
  },
  resolve: {
    alias: {
      'virtual:vite-rsc/server-references': './test/mocks/server-references.ts',
      '@vitejs/plugin-rsc/rsc': './test/mocks/plugin-rsc.ts',
      '@vitejs/plugin-rsc/ssr': './test/mocks/plugin-rsc.ts',
      '@vitejs/plugin-rsc/browser': './test/mocks/plugin-rsc.ts',
    },
  },
});