/**
 * サーバーエントリーポイント - 100クライアント対応版
 */

import { createExtendedServer } from "./core.ts";
import { setupGracefulShutdown } from "../01_single_container_10_clients/mod.ts";
import type { ExtendedServerConfig } from "./types.ts";

// 設定
const config: ExtendedServerConfig = {
  port: parseInt(Deno.env.get("PORT") || "3000"),
  maxMetricsSize: 10000, // 100クライアント用に拡大
  maxConcurrentRequests: 50,
  cacheSize: 1000,
  cacheTTL: 60000, // 1分
  numWorkers: 0, // Workerを一旦無効化（デバッグのため）
};

// サーバー作成と起動
const server = createExtendedServer(config);
const instance = server.start();

// グレースフルシャットダウン設定
const abortController = new AbortController();
setupGracefulShutdown(abortController);

// ワーカープール終了処理
Deno.addSignalListener("SIGTERM", () => {
  server.stop();
});

// シャットダウン待機
await instance.finished;