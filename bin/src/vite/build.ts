import { createServer } from "npm:vite@4.5.0";
import * as path from "https://deno.land/std@0.180.0/path/mod.ts";

// 現在の実行ディレクトリを取得（絶対パスで）
const __dirname = path.dirname(path.fromFileUrl(import.meta.url));

async function main() {
  try {
    const server = await createServer({
      // 明示的にルートディレクトリを現在のディレクトリに限定
      root: __dirname,
      
      // キャッシュを無効化
      cacheDir: false,
      
      // 他のプロジェクトを読み込まないように制限
      server: {
        fs: {
          strict: true,
          allow: [__dirname]
        },
        hmr: false,
        
        // CORS設定を追加 - ブラウザのメッセージポート問題を緩和
        cors: {
          origin: "*",
          methods: "GET,HEAD,PUT,PATCH,POST,DELETE",
          preflightContinue: false,
          optionsSuccessStatus: 204
        },
        
        // より明示的なヘッダー設定
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET,HEAD,PUT,PATCH,POST,DELETE",
          "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"
        }
      },
      
      // 依存関係の最適化を無効化
      optimizeDeps: {
        disabled: true
      },
      
      // サードパーティのコードの変換も無効化
      ssr: {
        external: []
      },
      
      // ビルドキャッシュも無効化
      build: {
        write: true,
        emptyOutDir: true
      },
      
      // これ以上のスキャンを防ぐために明示的にエントリーポイントを指定
      resolve: {
        conditions: [],
        mainFields: []
      }
    });
    
    await server.listen();
    console.log("サーバー起動完了 - 現在のディレクトリに制限:", __dirname);
    server.printUrls();
  } catch (error) {
    console.error("エラー:", error);
  }
}

if (import.meta.main) {
  await main();
}
