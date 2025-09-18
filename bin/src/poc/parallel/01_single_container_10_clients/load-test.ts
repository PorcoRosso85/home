/**
 * 負荷テストモジュール
 * 高階関数パターンでモジュール化されたロードテスト機能
 */

// 型定義はこのファイル内で完結

// 定数定義（ハードコード禁止）
export const LOAD_TEST_CONFIG = {
  CLIENTS: 10,
  DURATION_MS: 60000, // 1分間
  REQUEST_INTERVAL_MS: 100, // 各クライアント100ms間隔
  MAX_RESPONSE_TIMES: 1000, // メトリクス保持数
} as const;

// ロードテスト設定型
export type LoadTestConfig = {
  clients: number;
  durationMs: number;
  requestIntervalMs: number;
  targetUrl: string;
};

// リクエスト結果型
export type RequestResult = 
  | { ok: true; status: number; duration: number }
  | { ok: false; error: Error; duration: number };

// ロードテスト結果型
export type LoadTestResults = {
  totalRequests: number;
  totalErrors: number;
  responseTimes: readonly number[];
  errorMessages: readonly string[];
};

// サマリー型
export type LoadTestSummary = {
  totalRequests: number;
  totalErrors: number;
  errorRate: string;
  duration: string;
  throughput: string;
  responseTime: {
    min: number;
    max: number;
    p50: number;
    p95: number;
    p99: number;
    mean: number;
  };
};

// メトリクス取得結果型
export type MetricsResult = 
  | { ok: true; metrics: any }
  | { ok: false; error: Error };

/**
 * HTTPリクエストを実行する関数を作成
 * @param targetUrl リクエスト先URL
 * @returns リクエスト実行関数
 */
export function createRequestFunction(targetUrl: string) {
  /**
   * リクエストを実行
   * @returns リクエスト結果
   */
  return async function makeRequest(): Promise<RequestResult> {
    const start = Date.now();
    
    try {
      const res = await fetch(targetUrl);
      await res.text(); // bodyを消費
      return {
        ok: true,
        status: res.status,
        duration: Date.now() - start,
      };
    } catch (error) {
      return {
        ok: false,
        error: error instanceof Error ? error : new Error(String(error)),
        duration: Date.now() - start,
      };
    }
  };
}

/**
 * クライアントワーカーを作成する高階関数
 * @param config ロードテスト設定
 * @returns クライアント実行関数
 */
export function createClientWorker(config: LoadTestConfig) {
  const makeRequest = createRequestFunction(config.targetUrl);
  
  /**
   * クライアントを実行し、結果を収集
   * @param clientId クライアントID
   * @param endTime 終了時刻
   * @returns 実行結果
   */
  return async function runClient(
    clientId: number, 
    endTime: number
  ): Promise<LoadTestResults> {
    const results: RequestResult[] = [];
    
    while (Date.now() < endTime) {
      const result = await makeRequest();
      results.push(result);
      
      // 指定間隔でリクエスト
      await new Promise(resolve => setTimeout(resolve, config.requestIntervalMs));
    }
    
    // 結果を集計（イミュータブル）
    const successResults = results.filter(r => r.ok);
    const errorResults = results.filter(r => !r.ok);
    
    return {
      totalRequests: successResults.length,
      totalErrors: errorResults.length,
      responseTimes: successResults.map(r => r.duration),
      errorMessages: errorResults.map(r => 
        !r.ok ? r.error.message : ""
      ).filter(msg => msg !== ""),
    };
  };
}

/**
 * 結果を集約する純粋関数
 * @param clientResults 各クライアントの結果
 * @returns 集約された結果
 */
export function aggregateResults(
  clientResults: LoadTestResults[]
): LoadTestResults {
  return clientResults.reduce((acc, result) => ({
    totalRequests: acc.totalRequests + result.totalRequests,
    totalErrors: acc.totalErrors + result.totalErrors,
    responseTimes: [...acc.responseTimes, ...result.responseTimes],
    errorMessages: [...acc.errorMessages, ...result.errorMessages],
  }), {
    totalRequests: 0,
    totalErrors: 0,
    responseTimes: [],
    errorMessages: [],
  });
}

/**
 * サマリーを計算する純粋関数
 * @param results ロードテスト結果
 * @param durationSec 実行時間（秒）
 * @returns サマリー
 */
export function calculateSummary(
  results: LoadTestResults, 
  durationSec: number
): LoadTestSummary {
  const sorted = [...results.responseTimes].sort((a, b) => a - b);
  
  return {
    totalRequests: results.totalRequests,
    totalErrors: results.totalErrors,
    errorRate: results.totalRequests > 0 
      ? ((results.totalErrors / (results.totalRequests + results.totalErrors)) * 100).toFixed(2) + "%" 
      : "0.00%",
    duration: durationSec.toFixed(0) + "s",
    throughput: Math.round(results.totalRequests / durationSec) + " req/s",
    responseTime: {
      min: sorted[0] || 0,
      max: sorted[sorted.length - 1] || 0,
      p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
      p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
      p99: sorted[Math.floor(sorted.length * 0.99)] || 0,
      mean: sorted.length > 0 
        ? Math.round(sorted.reduce((a, b) => a + b, 0) / sorted.length) 
        : 0,
    },
  };
}

/**
 * メトリクスを取得する関数
 * @param metricsUrl メトリクスエンドポイントURL
 * @returns メトリクス取得結果
 */
export async function fetchMetrics(metricsUrl: string): Promise<MetricsResult> {
  try {
    const res = await fetch(metricsUrl);
    const metrics = await res.json();
    return { ok: true, metrics };
  } catch (error) {
    return { 
      ok: false, 
      error: error instanceof Error ? error : new Error(String(error))
    };
  }
}

/**
 * ロードテストランナーを作成する高階関数
 * @param config ロードテスト設定
 * @returns ロードテスト実行関数
 */
export function createLoadTestRunner(config: LoadTestConfig) {
  const runClient = createClientWorker(config);
  
  /**
   * ロードテストを実行
   * @returns テスト結果とサマリー
   */
  return async function runLoadTest(): Promise<{
    results: LoadTestResults;
    summary: LoadTestSummary;
    metrics: MetricsResult;
  }> {
    console.log(`Starting load test with ${config.clients} concurrent clients...`);
    
    const startTime = Date.now();
    const endTime = startTime + config.durationMs;
    
    // 並行してクライアントを実行
    const clientPromises = Array(config.clients).fill(0).map((_, i) => 
      runClient(i, endTime)
    );
    
    const clientResults = await Promise.all(clientPromises);
    
    // 結果を集約
    const aggregatedResults = aggregateResults(clientResults);
    const actualDuration = (Date.now() - startTime) / 1000;
    const summary = calculateSummary(aggregatedResults, actualDuration);
    
    // メトリクスを取得
    const metricsUrl = config.targetUrl.replace("/api/health", "/api/metrics");
    const metrics = await fetchMetrics(metricsUrl);
    
    return { results: aggregatedResults, summary, metrics };
  };
}

/**
 * 結果を表示する関数
 * @param summary サマリー
 * @param metrics メトリクス結果
 */
export function displayResults(summary: LoadTestSummary, metrics: MetricsResult): void {
  console.log("\nLoad Test Results:");
  console.log("==================");
  console.log(`Total Requests: ${summary.totalRequests}`);
  console.log(`Total Errors: ${summary.totalErrors}`);
  console.log(`Error Rate: ${summary.errorRate}`);
  console.log(`Duration: ${summary.duration}`);
  console.log(`Throughput: ${summary.throughput}`);
  console.log("\nResponse Time (ms):");
  console.log(`  Min: ${summary.responseTime.min}`);
  console.log(`  Max: ${summary.responseTime.max}`);
  console.log(`  P50: ${summary.responseTime.p50}`);
  console.log(`  P95: ${summary.responseTime.p95}`);
  console.log(`  P99: ${summary.responseTime.p99}`);
  console.log(`  Mean: ${summary.responseTime.mean}`);
  
  if (metrics.ok) {
    console.log("\nServer Metrics:");
    console.log(`  Request Count: ${metrics.metrics.requestCount}`);
    console.log(`  Memory RSS: ${Math.round(metrics.metrics.memory.rss / 1024 / 1024)}MB`);
    console.log(`  Heap Used: ${Math.round(metrics.metrics.memory.heapUsed / 1024 / 1024)}MB`);
  } else {
    console.log("\nServer Metrics: Failed to fetch");
    console.log(`  Error: ${metrics.error.message}`);
  }
}

// メイン実行（モジュール実行時のみ）
if (import.meta.main) {
  const config: LoadTestConfig = {
    clients: LOAD_TEST_CONFIG.CLIENTS,
    durationMs: LOAD_TEST_CONFIG.DURATION_MS,
    requestIntervalMs: LOAD_TEST_CONFIG.REQUEST_INTERVAL_MS,
    targetUrl: "http://localhost:3000/api/health",
  };
  
  const runLoadTest = createLoadTestRunner(config);
  
  runLoadTest()
    .then(({ summary, metrics }) => {
      displayResults(summary, metrics);
      console.log("\nLoad test completed successfully");
      Deno.exit(0);
    })
    .catch((error) => {
      console.error("Load test failed:", error);
      Deno.exit(1);
    });
}