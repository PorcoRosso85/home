import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    headers: {
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin'
    }
  },
  optimizeDeps: {
    exclude: ['@kuzu/kuzu-wasm', 'kuzu-wasm']
  },
  // .cypherファイルを文字列として読み込み可能にする
  assetsInclude: ['**/*.cypher'],
  resolve: {
    alias: {
      '@': '/src',
      '@/types': '/types'
    }
  }
})