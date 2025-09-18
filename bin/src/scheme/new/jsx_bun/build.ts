#!/usr/bin/env -S nix run nixpkgs#bun -- run
// build.ts - シンプルな開発サーバーとビルド機能に特化したスクリプト
import fs from 'fs';
import path from 'path';
import { createServer } from 'vite'; // Bunのグローバルキャッシュから読み込む
import { fileURLToPath } from 'url';
import type { InlineConfig, ViteDevServer } from 'vite'; // 型定義

// 依存関係の明示的な指定（--no-installと組み合わせて使用）
process.env.BUN_RUNTIME_DEPS = 'react@19.1.0,react-dom@19.1.0,vite@6.2.6';

// ディレクトリの取得
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = __dirname;

// 開発サーバーの起動 - デフォルトでシンプルな設定
async function createViteDevServer(): Promise<ViteDevServer> {
  const config: InlineConfig = {
    root,
    logLevel: 'info',
    server: {
      watch: {
        usePolling: true,
        interval: 100
      }
    },
    resolve: {
      dedupe: ['react', 'react-dom'],
    },
    esbuild: {
      jsx: "automatic",
      jsxImportSource: "react",
    }
  };

  return createServer(config);
}

// 本番用ビルド処理 - シンプルなBunビルド
async function buildForProduction() {
  console.log("Building for production...");
  
  try {
    // ビルド先ディレクトリの作成
    const distDir = path.join(root, 'dist');
    if (!fs.existsSync(distDir)) {
      fs.mkdirSync(distDir, { recursive: true });
    }
    
    // Bunのビルトイン機能を使用してビルド
    console.log("Building with Bun...");
    
    const result = await Bun.build({
      entrypoints: [path.join(root, 'index.tsx')],
      outdir: distDir,
      target: 'browser',
      minify: true,
    });
    
    if (!result.success) {
      console.error("Build failed:", result.logs);
      process.exit(1);
    }
    
    // index.htmlをdistディレクトリにコピー
    fs.copyFileSync(
      path.join(root, 'index.html'),
      path.join(distDir, 'index.html')
    );
    
    console.log("Build completed successfully.");
  } catch (error) {
    console.error("Error during build:", error);
    process.exit(1);
  }
}

// コマンドライン引数から実行する機能を決定
async function main(): Promise<void> {
  const command = process.argv[2] || "dev";

  switch (command) {
    case "dev":
      // 開発サーバーを起動
      console.log("Starting development server...");
      const devServer = await createViteDevServer();
      const server = await devServer.listen();
      
      // ポート番号を明示的に表示
      const actualPort = server.config.server.port;
      console.log(`\nDevelopment server is running at:`);
      console.log(`  > Local: http://localhost:${actualPort}/`);
      
      // 標準のURL表示も実行
      devServer.printUrls();
      break;
    case "build":
      // 本番用ビルド処理
      await buildForProduction();
      break;
    default:
      console.error(`Unknown command: ${command}`);
      console.log("Available commands: dev, build");
      process.exit(1);
  }
}

// スクリプト実行
main().catch(error => {
  console.error("Error:", error);
  process.exit(1);
});