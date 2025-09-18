/**
 * 極限負荷テスト - 1000クライアント
 */

import { delay } from "@std/async";

interface LoadTestResult {
  phase: string;
  clients: number;
  duration: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  avgResponseTime: number;
  p95ResponseTime: number;
  p99ResponseTime: number;
  maxResponseTime: number;
  throughput: number;
  errorRate: number;
}

// 段階的負荷テスト
async function runStagedAssault() {
  console.log(`
🚀 EXTREME LOAD TEST - 1000 CLIENT ASSAULT
==========================================
`);
  
  const stages = [
    { name: "Warm-up", clients: 50, duration: 10000 },
    { name: "Ramp-up", clients: 100, duration: 15000 },
    { name: "Stress", clients: 250, duration: 20000 },
    { name: "Heavy", clients: 500, duration: 20000 },
    { name: "Extreme", clients: 750, duration: 20000 },
    { name: "INSANE", clients: 1000, duration: 30000 },
  ];
  
  const results: LoadTestResult[] = [];
  
  for (const stage of stages) {
    console.log(`\n🔥 Phase: ${stage.name} (${stage.clients} clients)`);
    console.log("=".repeat(50));
    
    try {
      const result = await runLoadPhase(stage);
      results.push(result);
      
      // 結果表示
      console.log(`✅ Completed: ${result.successfulRequests} successful requests`);
      console.log(`❌ Failed: ${result.failedRequests} requests`);
      console.log(`📊 Throughput: ${result.throughput.toFixed(2)} req/s`);
      console.log(`⏱️  P95: ${result.p95ResponseTime}ms, P99: ${result.p99ResponseTime}ms`);
      console.log(`🎯 Error rate: ${(result.errorRate * 100).toFixed(2)}%`);
      
      // 破綻点検出
      if (result.errorRate > 0.1) {
        console.warn(`\n⚠️  HIGH ERROR RATE DETECTED!`);
      }
      
      if (result.p99ResponseTime > 1000) {
        console.warn(`⚠️  EXTREME LATENCY DETECTED!`);
      }
      
      // サーバーが完全に応答しなくなった場合
      if (result.errorRate > 0.9) {
        console.error(`\n💀 SERVER UNRESPONSIVE - STOPPING TEST`);
        break;
      }
      
      // ステージ間の休憩
      console.log(`\n⏸️  Cooling down for 5 seconds...`);
      await delay(5000);
      
    } catch (error) {
      console.error(`\n❌ Stage failed:`, error);
      break;
    }
  }
  
  // 最終レポート
  generateReport(results);
}

// 負荷フェーズ実行
async function runLoadPhase(stage: {
  name: string;
  clients: number;
  duration: number;
}): Promise<LoadTestResult> {
  const startTime = Date.now();
  const responseTimes: number[] = [];
  let successCount = 0;
  let errorCount = 0;
  
  // クライアントプール
  const clientPromises: Promise<void>[] = [];
  
  for (let i = 0; i < stage.clients; i++) {
    const clientId = `extreme-${stage.name}-${i}`;
    
    clientPromises.push(
      runClient(clientId, startTime + stage.duration, responseTimes)
        .then(({ success, errors }) => {
          successCount += success;
          errorCount += errors;
        })
    );
    
    // クライアントを段階的に起動（サーバーへの急激な負荷を避ける）
    if (i % 10 === 0) {
      await delay(10);
    }
  }
  
  // 全クライアント完了待機
  await Promise.all(clientPromises);
  
  // 統計計算
  const actualDuration = (Date.now() - startTime) / 1000;
  const totalRequests = successCount + errorCount;
  
  responseTimes.sort((a, b) => a - b);
  
  return {
    phase: stage.name,
    clients: stage.clients,
    duration: actualDuration,
    totalRequests,
    successfulRequests: successCount,
    failedRequests: errorCount,
    avgResponseTime: responseTimes.length > 0
      ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
      : 0,
    p95ResponseTime: responseTimes[Math.floor(responseTimes.length * 0.95)] || 0,
    p99ResponseTime: responseTimes[Math.floor(responseTimes.length * 0.99)] || 0,
    maxResponseTime: responseTimes[responseTimes.length - 1] || 0,
    throughput: successCount / actualDuration,
    errorRate: totalRequests > 0 ? errorCount / totalRequests : 0,
  };
}

// 個別クライアント実行
async function runClient(
  clientId: string,
  endTime: number,
  responseTimes: number[]
): Promise<{ success: number; errors: number }> {
  let success = 0;
  let errors = 0;
  
  while (Date.now() < endTime) {
    const start = Date.now();
    
    try {
      const response = await fetch(`http://localhost:3000/api/data/${clientId}`, {
        signal: AbortSignal.timeout(5000), // 5秒タイムアウト
      });
      
      if (response.ok) {
        await response.text(); // bodyを消費
        const duration = Date.now() - start;
        responseTimes.push(duration);
        success++;
      } else {
        errors++;
      }
    } catch (error) {
      errors++;
    }
    
    // リクエスト間隔（負荷調整）
    await delay(50 + Math.random() * 50); // 50-100ms
  }
  
  return { success, errors };
}

// 最終レポート生成
function generateReport(results: LoadTestResult[]) {
  console.log(`
  
📊 EXTREME LOAD TEST REPORT
===========================
`);
  
  // 表形式で結果表示
  console.log("Phase     | Clients | Success | Failed | Throughput | P95   | P99   | Error%");
  console.log("----------|---------|---------|--------|------------|-------|-------|-------");
  
  for (const r of results) {
    console.log(
      `${r.phase.padEnd(9)} | ` +
      `${r.clients.toString().padStart(7)} | ` +
      `${r.successfulRequests.toString().padStart(7)} | ` +
      `${r.failedRequests.toString().padStart(6)} | ` +
      `${r.throughput.toFixed(1).padStart(10)} | ` +
      `${r.p95ResponseTime.toString().padStart(5)} | ` +
      `${r.p99ResponseTime.toString().padStart(5)} | ` +
      `${(r.errorRate * 100).toFixed(1).padStart(6)}%`
    );
  }
  
  // 限界点の特定
  const breakingPoint = results.find(r => r.errorRate > 0.1);
  if (breakingPoint) {
    console.log(`
⚠️  BREAKING POINT: ${breakingPoint.clients} clients
   Error rate exceeded 10% threshold
`);
  }
  
  // 最大成功クライアント数
  const maxSuccess = results
    .filter(r => r.errorRate < 0.01)
    .sort((a, b) => b.clients - a.clients)[0];
    
  if (maxSuccess) {
    console.log(`
✅ MAX STABLE CLIENTS: ${maxSuccess.clients}
   Maintained <1% error rate
`);
  }
  
  // メトリクス取得
  fetchServerMetrics();
}

// サーバーメトリクス取得
async function fetchServerMetrics() {
  try {
    const response = await fetch("http://localhost:3000/api/metrics");
    const metrics = await response.json();
    
    console.log(`
📈 SERVER METRICS
=================
Active Connections: ${metrics.performance.activeConnections}
Total Connections: ${metrics.performance.totalConnections}
Rejected Connections: ${metrics.performance.rejectedConnections}
Total Requests: ${metrics.performance.totalRequests}
Dropped Requests: ${metrics.performance.droppedRequests}
Avg Processing Time: ${metrics.performance.avgProcessingTime.toFixed(2)}ms

Buffer Pool:
  Total: ${metrics.pools.buffer.total}
  Used: ${metrics.pools.buffer.used}
  Utilization: ${(metrics.pools.buffer.utilization * 100).toFixed(2)}%

Connection Pool:
  Total: ${metrics.pools.connection.total}
  By State: ${JSON.stringify(metrics.pools.connection.byState)}

Memory:
  Heap Used: ${(metrics.memory.heapUsed / 1024 / 1024).toFixed(2)}MB
  RSS: ${(metrics.memory.rss / 1024 / 1024).toFixed(2)}MB
`);
  } catch (error) {
    console.error("Failed to fetch server metrics:", error);
  }
}

// メイン実行
if (import.meta.main) {
  console.log("Starting in 3 seconds...");
  await delay(3000);
  
  await runStagedAssault();
  
  console.log("\n🏁 Test completed!");
  Deno.exit(0);
}