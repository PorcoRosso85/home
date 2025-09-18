import { createServer } from "vite";
import wasmPlugin from "vite-plugin-wasm";
import topLevelAwait from "vite-plugin-top-level-await";

// 型定義
type Result<T> = { data: T } | { error: string };

/**
 * 最小構成のVite開発サーバー
 */
async function startDevServer(): Promise<Result<void>> {
  try {
    const server = await createServer({
      configFile: false,
      root: ".",
      plugins: [
        wasmPlugin(),
        topLevelAwait(),
      ],
      server: {
        port: 5173,
        headers: {
          // kuzu-wasmに必要なSharedArrayBuffer対応
          'Cross-Origin-Embedder-Policy': 'require-corp',
          'Cross-Origin-Opener-Policy': 'same-origin'
        }
      },
      optimizeDeps: {
        force: true,
        exclude: ['kuzu-wasm']
      },
      esbuild: {
        supported: {
          'top-level-await': true
        }
      }
    });

    await server.listen();
    server.printUrls();
    console.log("\n🚀 Vite + Deno + Kuzu-WASM POC Server Started");
    return { data: undefined };
  } catch (error) {
    return { error: String(error) };
  }
}

// メイン実行
async function main() {
  const result = await startDevServer();
  
  if ('error' in result) {
    console.error('❌ Server startup failed:', result.error);
    Deno.exit(1);
  }
}

if (import.meta.main) {
  main();
}