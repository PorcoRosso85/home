/**
 * ビジネスロジック - メトリクス管理とレスポンス生成
 */

import type { 
  Metrics, 
  ResponseTimeStats, 
  MetricsResponse, 
  HealthResponse,
  MemoryUsage,
  ServerConfig
} from "./types.ts";

/**
 * メトリクスマネージャーを作成する高階関数
 * @param config サーバー設定
 * @returns メトリクス操作関数
 */
export function createMetricsManager(config: ServerConfig) {
  const metrics: Metrics = {
    requestCount: 0,
    errorCount: 0,
    responseTimes: [],
  };

  return {
    /**
     * リクエスト成功を記録
     * @param responseTime レスポンスタイム（ミリ秒）
     */
    recordSuccess(responseTime: number): void {
      metrics.requestCount++;
      metrics.responseTimes.push(responseTime);
      
      // メモリリーク防止のため最新N件のみ保持
      if (metrics.responseTimes.length > config.maxMetricsSize) {
        metrics.responseTimes.shift();
      }
    },

    /**
     * エラーを記録
     */
    recordError(): void {
      metrics.errorCount++;
    },

    /**
     * 現在のメトリクスを取得
     * @returns メトリクスのスナップショット
     */
    getMetrics(): Metrics {
      return {
        requestCount: metrics.requestCount,
        errorCount: metrics.errorCount,
        responseTimes: [...metrics.responseTimes],
      };
    }
  };
}

/**
 * レスポンスタイム統計を計算
 * @param responseTimes レスポンスタイムの配列
 * @returns 統計情報
 */
export function calculateResponseTimeStats(responseTimes: number[]): ResponseTimeStats {
  if (responseTimes.length === 0) {
    return { p50: 0, p95: 0, p99: 0, mean: 0 };
  }

  const sorted = [...responseTimes].sort((a, b) => a - b);
  
  return {
    p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
    p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
    p99: sorted[Math.floor(sorted.length * 0.99)] || 0,
    mean: sorted.reduce((a, b) => a + b, 0) / sorted.length || 0,
  };
}

/**
 * ヘルスレスポンスを生成
 * @param startTime サーバー開始時刻
 * @returns ヘルスレスポンス
 */
export function createHealthResponse(startTime: number): HealthResponse {
  return {
    status: "healthy",
    timestamp: new Date().toISOString(),
    uptime: (performance.now() - startTime) / 1000, // seconds
  };
}

/**
 * メトリクスレスポンスを生成
 * @param metrics 現在のメトリクス
 * @param memoryUsage メモリ使用量
 * @returns メトリクスレスポンス
 */
export function createMetricsResponse(
  metrics: Metrics, 
  memoryUsage: MemoryUsage
): MetricsResponse {
  return {
    requestCount: metrics.requestCount,
    errorCount: metrics.errorCount,
    responseTime: calculateResponseTimeStats(metrics.responseTimes),
    memory: memoryUsage,
  };
}