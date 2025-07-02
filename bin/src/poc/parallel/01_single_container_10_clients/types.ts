/**
 * POC 01_single_container_10_clients の型定義
 */

// メトリクスデータ型
export type Metrics = {
  requestCount: number;
  errorCount: number;
  responseTimes: number[];
};

// レスポンスタイム統計
export type ResponseTimeStats = {
  p50: number;
  p95: number;
  p99: number;
  mean: number;
};

// メモリ使用量
export type MemoryUsage = {
  rss: number;
  heapTotal: number;
  heapUsed: number;
};

// メトリクスレスポンス
export type MetricsResponse = {
  requestCount: number;
  errorCount: number;
  responseTime: ResponseTimeStats;
  memory: MemoryUsage;
};

// ヘルスレスポンス
export type HealthResponse = {
  status: "healthy" | "unhealthy";
  timestamp: string;
  uptime: number;
};

// APIハンドラーの結果型
export type HandlerResult = 
  | { ok: true; data: Response }
  | { ok: false; error: Error };

// サーバー設定
export type ServerConfig = {
  port: number;
  maxMetricsSize: number;
};