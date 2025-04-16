#!/usr/bin/env -S nix run nixpkgs#deno -- run -A
// build.ts - シンプルな開発サーバーとビルド機能に特化したスクリプト
import { createServer } from "npm:vite";
import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

// 開発サーバーの起動
async function createViteDevServer() {
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
      port: 3000,
      watch: {
        usePolling: true,
        interval: 100
      }
    }
  };

  return createServer(config);
}

// 本番用ビルド処理
async function buildForProduction() {
  console.log("Building for production...");
  
  try {
    // ビルド先ディレクトリの作成
    const distDir = path.join(Deno.cwd(), 'dist');
    try {
      Deno.mkdirSync(distDir, { recursive: true });
    } catch (e) {
      if (!(e instanceof Deno.errors.AlreadyExists)) {
        throw e;
      }
    }
    
    // DenoのAPIを使ってビルド - deno.jsonを使わないよう修正
    const command = new Deno.Command("deno", {
      args: [
        "bundle",
        "--no-config",  // 設定ファイルを使用しない
        "--no-check",   // 型チェックをスキップ
        "--jsx-import-source=https://esm.sh/react@18.2.0",  // JSXの設定を直接指定
        "--jsx=react-jsx",  // JSXの構文を直接指定
        "index.tsx",
        "dist/bundle.js"
      ],
      stdout: "piped",
      stderr: "piped",
    });
    
    const { code, stdout, stderr } = await command.output();
    if (code !== 0) {
      console.error("Build failed:", new TextDecoder().decode(stderr));
      Deno.exit(1);
    }
    
    // index.htmlをdistディレクトリにコピー
    try {
      await Deno.copyFile(
        "index.html",
        path.join(distDir, "index.html")
      );
    } catch (e) {
      console.error("Error copying index.html:", e);
      // index.htmlがない場合は新規作成
      const htmlContent = `
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Tree Layout Example</title>
    <style>
      body {
        font-family: sans-serif;
        margin: 0;
        padding: 0;
      }
      
      .tree-node {
        margin: 2px 0;
      }
      
      .tree-node-content {
        padding: 4px;
        border-radius: 4px;
      }
      
      .tree-node-content:hover {
        background-color: #f0f0f0;
      }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="./bundle.js"></script>
  </body>
</html>
`;
      await Deno.writeTextFile(path.join(distDir, "index.html"), htmlContent);
    }
    
    console.log("Build completed successfully.");
  } catch (error) {
    console.error("Error during build:", error);
    Deno.exit(1);
  }
}

// コマンドライン引数から実行する機能を決定
async function main() {
  const command = Deno.args[0] || "dev";

  switch (command) {
    case "dev":
      // 開発サーバーを起動
      console.log("Starting development server...");
      const devServer = await createViteDevServer();
      await devServer.listen();
      devServer.printUrls();
      break;
    case "build":
      // 本番用ビルド処理
      await buildForProduction();
      break;
    default:
      console.error(`Unknown command: ${command}`);
      console.log("Available commands: dev, build");
      Deno.exit(1);
  }
}

// スクリプト実行
await main();
