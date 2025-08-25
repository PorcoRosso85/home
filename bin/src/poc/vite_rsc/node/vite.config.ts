import rsc from '@vitejs/plugin-rsc'
import { cloudflare } from '@cloudflare/vite-plugin'
import { defineConfig } from 'vite'

export default defineConfig({
  clearScreen: false,
  build: {
    minify: false,
  },
  plugins: [
    rsc({
      entries: {
        client: './src/framework/entry.browser.tsx',
        ssr: './src/framework/entry.ssr.tsx',
      },
      // Define a static encryption key for development
      defineEncryptionKey: '"development-encryption-key-12345678"',
      serverHandler: false,
      // Enable loadModule proxy for Cloudflare Workers development
      loadModuleDevProxy: true,
      useBuildAppHook: true,
    }),
    cloudflare({
      configPath: './wrangler.toml',
      viteEnvironment: {
        name: 'rsc',
      },
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
          // ensure `default` export only in cloudflare entry output
          preserveEntrySignatures: 'exports-only',
        },
      },
      optimizeDeps: {
        include: ['turbo-stream'],
      },
    },

    // `ssr` environment loads modules without `react-server` condition
    // responsible for RSC stream deserialization and traditional SSR
    ssr: {
      keepProcessEnv: false,
      build: {
        // build `ssr` inside `rsc` directory so that
        // wrangler can deploy self-contained `dist/rsc`
        outDir: './dist/rsc/ssr',
        rollupOptions: {
          input: {
            index: './src/framework/entry.ssr.tsx',
          },
        },
      },
      resolve: {
        noExternal: true,
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
  
  builder: {
    // empty buildApp to disable cloudflare's buildApp
    buildApp: async () => {},
  },
})