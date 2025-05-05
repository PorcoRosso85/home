import { createServer } from "npm:vite";
import * as path from "https://deno.land/std@0.177.0/path/mod.ts";
import Terminal from "npm:vite-plugin-terminal";
import wasmPlugin from "npm:vite-plugin-wasm";
import topLevelAwait from "npm:vite-plugin-top-level-await";

// 開発サーバーの起動
async function createViteDevServer() {
  // NOTE: WebAssembly ESM統合プラグイン - WASMモジュールをブラウザで直接使えるようにするため
  // NOTE: トップレベルawaitサポートプラグイン - WASMモジュールの非同期初期化に必要
  
  // Vite設定
  const config = {
    configFile: false,
    root: ".",
    plugins: [
      Terminal({ 
        console: 'terminal',  // ブラウザのconsole.logをターミナルにリダイレクト
        output: ['terminal', 'console'] // 両方に出力
      }),
      // NOTE: プラグインの順番が重要 - wasmプラグインを先に適用し、次にtopLevelAwaitプラグインを適用
      wasmPlugin(),  // WASMモジュールをESM形式で使用可能にする
      topLevelAwait() // トップレベルでのawait使用を可能にする
    ],
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
      force: true,
      // NOTE: kuzu-wasmを除外リストに追加 - これにより、モジュールがViteの依存関係事前バンドルプロセスから除外され、
      // 外部化されずにブラウザで直接使用できるようになる
      exclude: ['kuzu-wasm'],
      esbuildOptions: {
        supported: {
          // NOTE: top-level-awaitサポートを明示的に有効化 - ESBuildレベルでも非同期モジュール初期化をサポートするため
          'top-level-await': true
        }
      }
    },
    build: {
      rollupOptions: {
        external: [], // 外部化するモジュールを指定しない（空リスト）
      },
      // NOTE: ターゲットをESNextに設定 - モダンなJavaScript機能（top-level-await含む）をサポートするため
      // 古いブラウザ向けにトランスパイルせず、最新のES機能を使用することでWASMとの互換性を向上
      target: 'esnext',
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
      },
      fs: {
        // Viteのファイルシステムアクセスを設定
        strict: false,
        allow: ['..', '.', '/'],
      },
      headers: {
        // クロスオリジン分離の設定（SharedArrayBuffer対応に必須）
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin'
      }
    }
  };

  return createServer(config);
}

// メイン関数
async function main() {
  console.log("Kuzu-Browse Deno Demo - Viteでの開発サーバー起動");
  
  try {
    // 開発サーバーを起動
    const devServer = await createViteDevServer();
    await devServer.listen();
    console.log("サーバー起動完了");
    devServer.printUrls();
  } catch (error) {
    console.error("サーバー起動中にエラーが発生しました:", error.message);
    console.error("スタックトレース:", error.stack);
    Deno.exit(1);  // エラーコードと共に終了
  }
}

// スクリプトが直接実行された場合のみメイン関数を実行
if (import.meta.main) {
  await main();
}

// 関数をエクスポート
export { createViteDevServer, main };
