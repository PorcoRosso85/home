/**
 * 1000クライアント極限負荷テスト - TDD Red Phase
 * このテストは現在の実装では失敗することが期待される
 */

import { assertEquals, assertExists, assert } from "@std/assert";
import { delay } from "@std/async";

// 分散負荷生成器の型定義
interface LoadGeneratorConfig {
  targetClients: number;
  rampUpTime: number;
  connectionTimeout: number;
  requestTimeout: number;
}

interface StageResult {
  clients: number;
  successfulConnections: number;
  failedConnections: number;
  avgResponseTime: number;
  p95ResponseTime: number;
  p99ResponseTime: number;
  errorRate: number;
  throughput: number;
}

interface TestResults {
  maxSuccessfulConnections: number;
  breakingPoint: number | null;
  performanceMetrics: StageResult[];
  errors: Array<{
    stage: number;
    error: string;
    timestamp: number;
  }>;
}

Deno.test({
  name: "test_extreme_1000_clients_should_hit_limits",
  sanitizeOps: false,
  sanitizeResources: false,
  ignore: false, // このテストは失敗するべき
}, async (t) => {
  
  await t.step("should identify breaking point with 1000 clients", async () => {
    const results: TestResults = {
      maxSuccessfulConnections: 0,
      breakingPoint: null,
      performanceMetrics: [],
      errors: [],
    };
    
    // 段階的に負荷を増加
    const stages = [
      { clients: 100, duration: 10000 },
      { clients: 250, duration: 10000 },
      { clients: 500, duration: 10000 },
      { clients: 750, duration: 10000 },
      { clients: 1000, duration: 30000 },
    ];
    
    for (const stage of stages) {
      console.log(`\n🔥 Testing with ${stage.clients} clients...`);
      
      try {
        const stageResult = await runStage(stage);
        results.performanceMetrics.push(stageResult);
        
        // 成功した最大接続数を記録
        if (stageResult.successfulConnections > results.maxSuccessfulConnections) {
          results.maxSuccessfulConnections = stageResult.successfulConnections;
        }
        
        // 破綻点の検出（エラー率50%以上）
        if (stageResult.errorRate > 0.5 && !results.breakingPoint) {
          results.breakingPoint = stage.clients;
          console.log(`💥 Breaking point detected at ${stage.clients} clients`);
        }
        
        // システムが完全に応答しなくなった場合は中断
        if (stageResult.errorRate > 0.9) {
          console.log('🚨 System is unresponsive, stopping test');
          break;
        }
      } catch (error) {
        results.errors.push({
          stage: stage.clients,
          error: error instanceof Error ? error.message : String(error),
          timestamp: Date.now(),
        });
      }
    }
    
    // これらのアサーションは失敗するべき（Red Phase）
    assert(
      results.maxSuccessfulConnections >= 1000,
      `❌ Expected to handle 1000+ connections, but only handled ${results.maxSuccessfulConnections}`
    );
    
    assertEquals(
      results.breakingPoint,
      null,
      `❌ System broke at ${results.breakingPoint} clients - single container cannot handle 1000 clients`
    );
    
    // パフォーマンス劣化の確認
    const degradation = analyzeDegradation(results.performanceMetrics);
    assert(
      !degradation.isExponential,
      `❌ Performance degradation is exponential: ${JSON.stringify(degradation)}`
    );
  });

  await t.step("should maintain sub-100ms P99 latency with 1000 clients", async () => {
    // 1000クライアントで直接テスト
    console.log("\n🔥 Direct 1000 clients assault...");
    
    const clients = Array(1000).fill(0).map((_, i) => ({
      id: `extreme-client-${i}`,
    }));
    
    const startTime = Date.now();
    const testDuration = 30000; // 30秒
    const results: Array<{ duration: number; status: number | string }> = [];
    
    // バッチで同時接続を試みる
    const batchSize = 100;
    for (let i = 0; i < clients.length; i += batchSize) {
      const batch = clients.slice(i, i + batchSize);
      
      await Promise.all(
        batch.map(async (client) => {
          const reqStart = Date.now();
          try {
            const res = await fetch(`http://localhost:3000/api/data/${client.id}`, {
              signal: AbortSignal.timeout(5000),
            });
            await res.text();
            results.push({
              duration: Date.now() - reqStart,
              status: res.status,
            });
          } catch (error) {
            results.push({
              duration: Date.now() - reqStart,
              status: "error",
            });
          }
        })
      );
      
      // 少し待機してサーバーに呼吸させる
      await delay(100);
    }
    
    // レスポンスタイム分析
    const successfulRequests = results.filter(r => r.status === 200);
    const responseTimes = successfulRequests.map(r => r.duration).sort((a, b) => a - b);
    const p99 = responseTimes[Math.floor(responseTimes.length * 0.99)] || Infinity;
    
    // このアサーションは失敗するべき
    assert(
      p99 < 100,
      `❌ P99 latency ${p99}ms exceeds 100ms limit with 1000 clients`
    );
    
    const errorRate = (results.length - successfulRequests.length) / results.length;
    assert(
      errorRate < 0.01,
      `❌ Error rate ${(errorRate * 100).toFixed(2)}% exceeds 1% limit`
    );
  });

  await t.step("should not exhaust system resources", async () => {
    // リソース枯渇テスト
    console.log("\n🔥 Resource exhaustion test...");
    
    // メトリクスを取得
    const metricsRes = await fetch("http://localhost:3000/api/metrics");
    const metrics = await metricsRes.json();
    
    // メモリ使用量チェック（1GB以下であるべき）
    const memoryUsageMB = metrics.memory.heapUsed / 1024 / 1024;
    assert(
      memoryUsageMB < 1024,
      `❌ Memory usage ${memoryUsageMB.toFixed(2)}MB exceeds 1GB limit`
    );
    
    // ファイルディスクリプタの推定（接続数から）
    const estimatedFDs = metrics.requestCount;
    assert(
      estimatedFDs < 10000,
      `❌ Estimated file descriptors ${estimatedFDs} approaching system limits`
    );
  });
});

// ヘルパー関数：ステージ実行
async function runStage(stage: { clients: number; duration: number }): Promise<StageResult> {
  const results: Array<{
    status: number | string;
    duration: number;
  }> = [];
  
  const clients = Array(stage.clients).fill(0).map((_, i) => ({
    id: `client-${i}`,
  }));
  
  const startTime = Date.now();
  let totalRequests = 0;
  
  // 並列でクライアントを実行
  await Promise.all(
    clients.map(async (client) => {
      while (Date.now() - startTime < stage.duration) {
        const reqStart = Date.now();
        try {
          const res = await fetch(`http://localhost:3000/api/data/${client.id}`, {
            signal: AbortSignal.timeout(2000),
          });
          await res.text();
          results.push({
            status: res.status,
            duration: Date.now() - reqStart,
          });
        } catch (error) {
          results.push({
            status: "error",
            duration: Date.now() - reqStart,
          });
        }
        totalRequests++;
        
        // 負荷調整
        await delay(Math.random() * 100);
      }
    })
  );
  
  // 結果を集計
  const successfulRequests = results.filter(r => r.status === 200);
  const errorRequests = results.filter(r => r.status !== 200);
  const responseTimes = successfulRequests.map(r => r.duration).sort((a, b) => a - b);
  
  const actualDuration = (Date.now() - startTime) / 1000;
  
  return {
    clients: stage.clients,
    successfulConnections: successfulRequests.length,
    failedConnections: errorRequests.length,
    avgResponseTime: responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length || 0,
    p95ResponseTime: responseTimes[Math.floor(responseTimes.length * 0.95)] || 0,
    p99ResponseTime: responseTimes[Math.floor(responseTimes.length * 0.99)] || 0,
    errorRate: errorRequests.length / results.length || 0,
    throughput: successfulRequests.length / actualDuration,
  };
}

// パフォーマンス劣化分析
function analyzeDegradation(metrics: StageResult[]) {
  const responseTimeGrowth: Array<{
    clientIncrease: number;
    responseTimeIncrease: number;
    ratio: number;
  }> = [];
  
  for (let i = 1; i < metrics.length; i++) {
    const prev = metrics[i - 1];
    const curr = metrics[i];
    
    if (prev.clients === 0 || prev.p99ResponseTime === 0) continue;
    
    const clientIncrease = curr.clients / prev.clients;
    const responseTimeIncrease = curr.p99ResponseTime / prev.p99ResponseTime;
    
    responseTimeGrowth.push({
      clientIncrease,
      responseTimeIncrease,
      ratio: responseTimeIncrease / clientIncrease,
    });
  }
  
  // 比率が1を大きく超える場合は非線形（指数的）な劣化
  const avgRatio = responseTimeGrowth.length > 0
    ? responseTimeGrowth.reduce((sum, g) => sum + g.ratio, 0) / responseTimeGrowth.length
    : 0;
  
  return {
    isExponential: avgRatio > 1.5,
    avgGrowthRatio: avgRatio,
    details: responseTimeGrowth,
  };
}

// リソース監視テスト
Deno.test({
  name: "test_resource_monitoring_shows_system_limits",
  sanitizeOps: false,
  sanitizeResources: false,
  ignore: false,
}, async () => {
  console.log("\n📊 Monitoring resource usage under extreme load...");
  
  const resourceSnapshots: Array<{
    timestamp: number;
    memory: any;
    connections: number;
  }> = [];
  
  // 30秒間のリソース監視
  const monitoringDuration = 30000;
  const monitoringInterval = 1000;
  
  const monitoring = setInterval(async () => {
    try {
      const res = await fetch("http://localhost:3000/api/metrics");
      const metrics = await res.json();
      
      resourceSnapshots.push({
        timestamp: Date.now(),
        memory: metrics.memory,
        connections: metrics.requestCount,
      });
    } catch (error) {
      console.error("Failed to collect metrics:", error);
    }
  }, monitoringInterval);
  
  // 並行して負荷をかける
  const loadPromise = (async () => {
    const clients = 500; // 500クライアントでも限界に近いはず
    const promises = [];
    
    for (let i = 0; i < clients; i++) {
      promises.push(
        (async () => {
          const clientId = `monitor-client-${i}`;
          for (let j = 0; j < 100; j++) {
            try {
              await fetch(`http://localhost:3000/api/data/${clientId}`);
              await delay(50);
            } catch {
              // エラーは想定内
            }
          }
        })()
      );
    }
    
    await Promise.all(promises);
  })();
  
  // 監視期間待機
  await delay(monitoringDuration);
  clearInterval(monitoring);
  await loadPromise;
  
  // リソース使用量の分析
  const maxMemory = Math.max(...resourceSnapshots.map(s => s.memory.heapUsed));
  const avgMemory = resourceSnapshots.reduce((sum, s) => sum + s.memory.heapUsed, 0) / resourceSnapshots.length;
  
  console.log(`\n📈 Resource Usage Summary:`);
  console.log(`  Max Memory: ${(maxMemory / 1024 / 1024).toFixed(2)}MB`);
  console.log(`  Avg Memory: ${(avgMemory / 1024 / 1024).toFixed(2)}MB`);
  console.log(`  Snapshots: ${resourceSnapshots.length}`);
  
  // メモリが指数的に増加していないか確認（これは失敗するべき）
  const memoryGrowthRate = (maxMemory - resourceSnapshots[0].memory.heapUsed) / resourceSnapshots[0].memory.heapUsed;
  assert(
    memoryGrowthRate < 0.5,
    `❌ Memory growth rate ${(memoryGrowthRate * 100).toFixed(2)}% indicates resource exhaustion`
  );
});