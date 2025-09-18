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
 * ### ロードテスト実行
 * ```typescript
 * import { createLoadTestRunner, displayResults } from "./mod.ts";
 * 
 * const runner = createLoadTestRunner({
 *   clients: 10,
 *   durationMs: 60000,
 *   requestIntervalMs: 100,
 *   targetUrl: "http://localhost:3000/api/health"
 * });
 * 
 * const { summary, metrics } = await runner();
 * displayResults(summary, metrics);
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

// 負荷テスト機能
export {
  createLoadTestRunner,
  createRequestFunction,
  createClientWorker,
  aggregateResults,
  calculateSummary,
  fetchMetrics,
  displayResults,
  LOAD_TEST_CONFIG,
} from "./load-test.ts";

export type {
  LoadTestConfig,
  RequestResult,
  LoadTestResults,
  LoadTestSummary,
  MetricsResult,
} from "./load-test.ts";

// デフォルト設定
export const DEFAULT_CONFIG = {
  PORT: 3000,
  MAX_METRICS_SIZE: 1000,
} as const;