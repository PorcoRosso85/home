/**
 * POC 01_single_container_10_clients
 * 
 * 単一コンテナで10クライアントの並行接続を処理するPOC
 * 
 * ## 使用例
 * 
 * ### サーバー起動
 * ```typescript
 * import { createServer, setupGracefulShutdown } from "./mod.ts";
 * 
 * const server = createServer({
 *   port: 3000,
 *   maxMetricsSize: 1000
 * });
 * 
 * const instance = server.start();
 * 
 * // グレースフルシャットダウン設定
 * const abortController = new AbortController();
 * setupGracefulShutdown(abortController);
 * 
 * await instance.finished;
 * ```
 * 
 * ### カスタム設定での起動
 * ```typescript
 * const server = createServer({
 *   port: parseInt(Deno.env.get("PORT") || "8080"),
 *   maxMetricsSize: 2000
 * });
 * ```
 * 
 * ### APIエンドポイント
 * - GET /api/health - ヘルスチェック
 * - GET /api/metrics - メトリクス取得
 */

// 型定義
export type {
  Metrics,
  ResponseTimeStats,
  MemoryUsage,
  MetricsResponse,
  HealthResponse,
  HandlerResult,
  ServerConfig,
} from "./types.ts";

// コア機能
export {
  createMetricsManager,
  calculateResponseTimeStats,
  createHealthResponse,
  createMetricsResponse,
} from "./core.ts";

// アダプター
export {
  createServer,
  setupGracefulShutdown,
  getMemoryUsage,
} from "./adapters.ts";

// デフォルト設定
export const DEFAULT_CONFIG = {
  PORT: 3000,
  MAX_METRICS_SIZE: 1000,
} as const;