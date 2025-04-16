#!/usr/bin/env -S nix run nixpkgs#deno -- run -A
// build.ts - 開発サーバー設定、SSG事前ビルド、バンドルをカバーする統合ビルドツール
import { createServer } from "npm:vite";
import React from "https://esm.sh/react@18.2.0";
import ReactDOMServer from "https://esm.sh/react-dom@18.2.0/server";
import { App } from "./index.tsx";

// HTMLテンプレートからSSRコンテンツとスタイルを読み込む
async function readHTMLTemplate() {
  try {
    return await Deno.readTextFile("./index.html");
  } catch (e) {
    console.error("Template file not found, using default template");
    // 基本的なHTMLテンプレート
    return `
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Deno + Vite + React</title>
  </head>
  <body>
    <div id="root"><!--ssr-outlet--></div>
    <script type="module" src="./index.tsx"></script>
  </body>
</html>
`;
  }
}

// SSRでレンダリングしたHTMLを生成・保存
async function generateSSR() {
  console.log("Generating SSR content...");
  
  // テンプレートの読み込み
  const template = await readHTMLTemplate();
  
  // Appコンポーネントをサーバーでレンダリング
  const appHTML = ReactDOMServer.renderToString(React.createElement(App));
  
  // SSRコンテンツをテンプレートに挿入
  const html = template.replace('<!--ssr-outlet-->', appHTML);
  
  // 生成したHTMLを保存
  await Deno.writeTextFile("index.html", html);
  console.log("SSR HTML generated successfully");
  
  return html;
}

// 開発・ビルド環境設定を統合管理
async function main() {
  const command = Deno.args[0] || "dev";

  switch (command) {
    case "dev":
      await runDevServer();
      break;
    case "build":
      await buildForProduction();
      break;
    case "preview":
      await previewBuild();
      break;
    default:
      console.error(`Unknown command: ${command}`);
      console.log("Available commands: dev, build, preview");
      Deno.exit(1);
  }
}

// 開発サーバー起動
async function runDevServer() {
  // SSRコンテンツ生成
  await generateSSR();

  // Vite設定
  const config = {
    configFile: false,
    root: ".",
    define: {
      'process.env.NODE_ENV': '"development"',
      'import.meta.env.DEV': 'true',
    },
    resolve: {
      dedupe: ['react', 'react-dom'],
      alias: [
        { find: 'react', replacement: 'https://esm.sh/react@18.2.0' },
        { find: 'react-dom', replacement: 'https://esm.sh/react-dom@18.2.0' },
        { find: 'react-dom/client', replacement: 'https://esm.sh/react-dom@18.2.0/client' },
        { find: 'react-dom/server', replacement: 'https://esm.sh/react-dom@18.2.0/server' }
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
      port: 3000
    }
  };

  console.log("Starting Vite development server...");
  const server = await createServer(config);
  await server.listen();
  server.printUrls();
}

// 本番用ビルド処理
async function buildForProduction() {
  console.log("Building for production...");
  
  try {
    // SSGビルドスクリプトの呼び出し
    const { build } = await import("./src/build.tsx");
    await build();
    
    console.log("Production build completed successfully.");
  } catch (error) {
    console.error("Error during build:", error);
    Deno.exit(1);
  }
}

// ビルド結果のプレビュー
async function previewBuild() {
  console.log("Previewing production build...");
  
  try {
    // 簡易HTTPサーバーの起動
    const { serve } = await import("https://deno.land/std/http/server.ts");
    const { serveDir } = await import("https://deno.land/std/http/file_server.ts");
    
    serve((req) => {
      return serveDir(req, {
        fsRoot: "dist",
      });
    }, { port: 8000 });
    
    console.log("Preview server running at http://localhost:8000");
  } catch (error) {
    console.error("Error starting preview server:", error);
    Deno.exit(1);
  }
}

// スクリプト実行
await main();
