#!/usr/bin/env -S nix run nixpkgs#deno -- run -A
// build.ts - Kuzu-Wasm用の最小構成Vite開発サーバー
import { createServer } from "npm:vite";
import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

// 開発サーバーの起動
async function createViteDevServer() {
  // Vite設定
  const config = {
    configFile: false,
    root: ".",
    plugins: [],
    define: {
      'process.env.NODE_ENV': '\"development\"',
      'import.meta.env.DEV': 'true',
    },
    resolve: {
      dedupe: ['react', 'react-dom'],
      alias: [
        { find: 'react', replacement: 'https://esm.sh/react@18.2.0' },
        { find: 'react-dom', replacement: 'https://esm.sh/react-dom@18.2.0' },
        { find: 'react-dom/client', replacement: 'https://esm.sh/react-dom@18.2.0/client' }
      ]
    },
    optimizeDeps: {
      force: true
    },
    esbuild: {
      jsx: "automatic",
      jsxImportSource: "https://esm.sh/react@18.2.0"
    },
    server: {
      port: 8000,
      watch: {
        usePolling: true,
        interval: 100
      }
    }
  };

  return createServer(config);
}

// メイン関数
async function main() {
  console.log("Kuzu-Wasm Deno Demo - Viteでの開発サーバー起動");
  
  // 開発サーバーを起動
  const devServer = await createViteDevServer();
  await devServer.listen();
  console.log("サーバー起動完了");
  devServer.printUrls();
}

// スクリプト実行
await main();