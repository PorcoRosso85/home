/**
 * 100クライアント対応テスト
 */

import { assertEquals, assert } from "@std/assert";
import { delay } from "@std/async";

// テスト用の型定義
interface TestResult {
  clientId: string;
  results: Array<{
    status: number | string;
    duration: number;
    timestamp: number;
    error?: string;
  }>;
}

Deno.test({
  name: "test_scale_100_clients_handle_efficiently",
  sanitizeOps: false,
  sanitizeResources: false,
}, async (t) => {
  await t.step("should handle 100 concurrent connections", async () => {
    const clients = Array(100).fill(0).map((_, i) => ({
      id: `client-${i}`,
      requests: [] as any[],
    }));
    
    // 10秒間のテスト
    const testDuration = 10000;
    const results = await Promise.all(
      clients.map(async (client): Promise<TestResult> => {
        const clientResults: any[] = [];
        const startTime = Date.now();
        
        while (Date.now() - startTime < testDuration) {
          const reqStart = Date.now();
          try {
            const res = await fetch(`http://localhost:3000/api/data/${client.id}`);
            const duration = Date.now() - reqStart;
            
            clientResults.push({
              status: res.status,
              duration,
              timestamp: Date.now(),
            });
            
            await res.text(); // bodyを消費
          } catch (error) {
            clientResults.push({
              status: "error",
              error: error instanceof Error ? error.message : String(error),
              timestamp: Date.now(),
              duration: Date.now() - reqStart,
            });
          }
          
          // 適応的な待機時間
          const waitTime = Math.max(10, 100 - clientResults.length);
          await delay(waitTime);
        }
        
        return {
          clientId: client.id,
          results: clientResults,
        };
      })
    );
    
    // 集計
    const allRequests = results.flatMap(r => r.results);
    const successfulRequests = allRequests.filter(r => r.status === 200);
    const errorRequests = allRequests.filter(r => r.status !== 200);
    
    // アサーション
    const successRate = successfulRequests.length / allRequests.length;
    assert(successRate > 0.999, `Success rate ${successRate} should be > 99.9%`);
    
    // レスポンスタイム分析
    const responseTimes = successfulRequests
      .map(r => r.duration)
      .sort((a, b) => a - b);
    const p95 = responseTimes[Math.floor(responseTimes.length * 0.95)] || 0;
    const p99 = responseTimes[Math.floor(responseTimes.length * 0.99)] || 0;
    
    assert(p95 < 200, `P95 response time ${p95}ms should be < 200ms`);
    assert(p99 < 500, `P99 response time ${p99}ms should be < 500ms`);
    
    console.log(`✅ Handled ${successfulRequests.length} requests successfully`);
    console.log(`📊 P95: ${p95}ms, P99: ${p99}ms`);
  });

  await t.step("should maintain consistent performance over time", async () => {
    const measurements: Array<{
      timestamp: number;
      avgDuration: number;
      successRate: number;
    }> = [];
    
    const measurementInterval = 1000; // 1秒ごと
    const totalDuration = 30000; // 30秒間
    
    const measurePerformance = async () => {
      const concurrentRequests = Array(10).fill(0).map(async () => {
        const start = Date.now();
        try {
          const res = await fetch("http://localhost:3000/api/health");
          await res.text();
          return {
            duration: Date.now() - start,
            status: res.status,
          };
        } catch {
          return {
            duration: Date.now() - start,
            status: 0,
          };
        }
      });
      
      const results = await Promise.all(concurrentRequests);
      return {
        timestamp: Date.now(),
        avgDuration: results.reduce((sum, r) => sum + r.duration, 0) / results.length,
        successRate: results.filter(r => r.status === 200).length / results.length,
      };
    };
    
    // 定期的に性能測定
    const startTime = Date.now();
    while (Date.now() - startTime < totalDuration) {
      measurements.push(await measurePerformance());
      await delay(measurementInterval);
    }
    
    // 性能劣化がないことを確認
    const firstHalf = measurements.slice(0, measurements.length / 2);
    const secondHalf = measurements.slice(measurements.length / 2);
    
    const avgFirstHalf = firstHalf.reduce((sum, m) => sum + m.avgDuration, 0) / firstHalf.length;
    const avgSecondHalf = secondHalf.reduce((sum, m) => sum + m.avgDuration, 0) / secondHalf.length;
    
    // 後半が前半より20%以上遅くならないこと
    assert(
      avgSecondHalf < avgFirstHalf * 1.2,
      `Performance degradation: ${avgSecondHalf}ms > ${avgFirstHalf * 1.2}ms`
    );
    
    console.log(`✅ Performance stable over time`);
    console.log(`📊 First half avg: ${avgFirstHalf.toFixed(2)}ms`);
    console.log(`📊 Second half avg: ${avgSecondHalf.toFixed(2)}ms`);
  });
});

Deno.test("test_cache_effectiveness", async () => {
  const clientId = "test-cache-client";
  const numRequests = 100;
  
  // 最初のリクエスト（キャッシュミス）
  const firstStart = Date.now();
  const firstRes = await fetch(`http://localhost:3000/api/data/${clientId}`);
  const firstDuration = Date.now() - firstStart;
  const firstData = await firstRes.json();
  
  // 後続のリクエスト（キャッシュヒット期待）
  const cachedDurations: number[] = [];
  
  for (let i = 0; i < numRequests; i++) {
    const start = Date.now();
    const res = await fetch(`http://localhost:3000/api/data/${clientId}`);
    const duration = Date.now() - start;
    const data = await res.json();
    
    cachedDurations.push(duration);
    
    // データが同じであることを確認（キャッシュから返却）
    assertEquals(data.id, firstData.id);
    assertEquals(data.value, firstData.value);
  }
  
  const avgCachedDuration = cachedDurations.reduce((a, b) => a + b, 0) / cachedDurations.length;
  
  // キャッシュヒットは最初のリクエストより速いはず
  assert(
    avgCachedDuration < firstDuration * 0.5,
    `Cached requests (${avgCachedDuration}ms) should be faster than first request (${firstDuration}ms)`
  );
  
  console.log(`✅ Cache working effectively`);
  console.log(`📊 First request: ${firstDuration}ms`);
  console.log(`📊 Avg cached: ${avgCachedDuration.toFixed(2)}ms`);
});

Deno.test("test_metrics_accuracy", async () => {
  // メトリクスをリセットするため、少し待機
  await delay(1000);
  
  // 既知の数のリクエストを送信
  const numRequests = 50;
  let successCount = 0;
  
  for (let i = 0; i < numRequests; i++) {
    try {
      const res = await fetch("http://localhost:3000/api/health");
      if (res.status === 200) successCount++;
      await res.text();
    } catch {
      // エラーは無視
    }
  }
  
  // メトリクスを取得
  const metricsRes = await fetch("http://localhost:3000/api/metrics");
  const metrics = await metricsRes.json();
  
  // リクエスト数が記録されているか確認
  assert(
    metrics.requestCount >= successCount,
    `Metrics request count ${metrics.requestCount} should be >= ${successCount}`
  );
  
  // キャッシュ統計が含まれているか確認
  assertExists(metrics.cache, "Cache metrics should exist");
  assert(metrics.cache.hitRate >= 0, "Cache hit rate should be >= 0");
  
  console.log(`✅ Metrics tracking accurately`);
  console.log(`📊 Total requests: ${metrics.requestCount}`);
  console.log(`📊 Cache hit rate: ${(metrics.cache.hitRate * 100).toFixed(2)}%`);
});

// ヘルパー関数
function assertExists<T>(value: T | null | undefined, msg?: string): asserts value is T {
  if (value === null || value === undefined) {
    throw new Error(msg || "Value should exist");
  }
}