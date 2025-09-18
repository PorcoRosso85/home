import rsc from '@vitejs/plugin-rsc'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    rsc({
      // Define a static encryption key for development
      // In production, use environment variable
      defineEncryptionKey: '"development-encryption-key-12345678"',
    }),
  ],

  environments: {
    // `rsc` environment loads modules with `react-server` condition
    // responsible for RSC stream serialization and server functions
    rsc: {
      build: {
        rollupOptions: {
          input: {
            index: './src/framework/entry.rsc.tsx',
          },
        },
      },
    },

    // `ssr` environment loads modules without `react-server` condition
    // responsible for RSC stream deserialization and traditional SSR
    ssr: {
      build: {
        rollupOptions: {
          input: {
            index: './src/framework/entry.ssr.tsx',
          },
        },
      },
    },

    // `client` environment used for hydration and client-side rendering
    // responsible for RSC stream deserialization, CSR, and server functions
    client: {
      build: {
        rollupOptions: {
          input: {
            index: './src/framework/entry.browser.tsx',
          },
        },
      },
    },
  },
})