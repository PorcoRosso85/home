/**
 * サーバーエントリーポイント
 * mod.tsの公開APIを使用してサーバーを起動
 */

import { createServer, setupGracefulShutdown, DEFAULT_CONFIG } from "./mod.ts";

// 設定値（ハードコード禁止のため定数化）
const PORT = parseInt(Deno.env.get("PORT") || String(DEFAULT_CONFIG.PORT));
const MAX_METRICS_SIZE = DEFAULT_CONFIG.MAX_METRICS_SIZE;

// サーバー作成と起動
const server = createServer({
  port: PORT,
  maxMetricsSize: MAX_METRICS_SIZE,
});

const instance = server.start();

// グレースフルシャットダウン設定
const abortController = new AbortController();
setupGracefulShutdown(abortController);

// シャットダウン待機
await instance.finished;