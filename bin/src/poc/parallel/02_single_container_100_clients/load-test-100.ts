/**
 * 100クライアント負荷テスト
 */

import { createLoadTestRunner, type LoadTestConfig } from "../01_single_container_10_clients/load-test.ts";
import { delay } from "@std/async";

// 100クライアント用の設定
export const SCALE_TEST_CONFIG: LoadTestConfig = {
  clients: 100,
  durationMs: 180000, // 3分間
  requestIntervalMs: 50, // より高頻度
  targetUrl: "http://localhost:3000/api/data/client-${id}",
};

// ステージ付き負荷テスト実行関数
export async function runStagedLoadTest() {
  const stages = [
    { duration: 30000, targetClients: 50 },   // ウォームアップ
    { duration: 60000, targetClients: 100 },  // 100クライアントまで増加
    { duration: 180000, targetClients: 100 }, // 100クライアントを維持
    { duration: 30000, targetClients: 0 },    // クールダウン
  ];
  
  console.log("🚀 Starting staged load test...");
  console.log("📊 Stages:");
  stages.forEach((stage, i) => {
    console.log(`  ${i + 1}. ${stage.targetClients} clients for ${stage.duration / 1000}s`);
  });
  console.log("");
  
  for (const [index, stage] of stages.entries()) {
    console.log(`\n📍 Stage ${index + 1}: ${stage.targetClients} clients for ${stage.duration / 1000}s`);
    
    if (stage.targetClients === 0) {
      console.log("🔄 Cooling down...");
      await delay(stage.duration);
      continue;
    }
    
    const config: LoadTestConfig = {
      clients: stage.targetClients,
      durationMs: stage.duration,
      requestIntervalMs: SCALE_TEST_CONFIG.requestIntervalMs,
      targetUrl: "http://localhost:3000/api/data/client-test",
    };
    
    const runner = createLoadTestRunner(config);
    const { summary, metrics } = await runner();
    
    // 閾値チェック
    const p95Threshold = 200;
    const p99Threshold = 500;
    const errorRateThreshold = 0.1;
    
    console.log("\n📋 Stage Results:");
    console.log(`  Total Requests: ${summary.totalRequests}`);
    console.log(`  Error Rate: ${summary.errorRate}`);
    console.log(`  Throughput: ${summary.throughput}`);
    console.log(`  P95: ${summary.responseTime.p95}ms ${summary.responseTime.p95 > p95Threshold ? "❌" : "✅"}`);
    console.log(`  P99: ${summary.responseTime.p99}ms ${summary.responseTime.p99 > p99Threshold ? "❌" : "✅"}`);
    
    // 警告表示
    if (summary.responseTime.p95 > p95Threshold) {
      console.error(`⚠️  P95 response time ${summary.responseTime.p95}ms exceeds ${p95Threshold}ms`);
    }
    if (summary.responseTime.p99 > p99Threshold) {
      console.error(`⚠️  P99 response time ${summary.responseTime.p99}ms exceeds ${p99Threshold}ms`);
    }
    if (parseFloat(summary.errorRate) > errorRateThreshold) {
      console.error(`⚠️  Error rate ${summary.errorRate} exceeds ${errorRateThreshold}%`);
    }
    
    // サーバーメトリクス表示
    if (metrics.ok) {
      console.log("\n📊 Server Metrics:");
      console.log(`  Memory: ${Math.round(metrics.metrics.memory.heapUsed / 1024 / 1024)}MB`);
      console.log(`  Cache Hit Rate: ${(metrics.metrics.cache.hitRate * 100).toFixed(2)}%`);
    }
  }
  
  console.log("\n✅ Load test completed!");
}

// リアルタイム監視付き負荷テスト
export async function runMonitoredLoadTest() {
  console.log("🔍 Starting monitored load test with real-time metrics...\n");
  
  const config: LoadTestConfig = {
    ...SCALE_TEST_CONFIG,
    durationMs: 60000, // 1分間のテスト
  };
  
  // モニタリングタスク
  const monitoringInterval = 5000; // 5秒ごと
  const monitoring = setInterval(async () => {
    try {
      const res = await fetch("http://localhost:3000/api/metrics");
      const metrics = await res.json();
      
      console.log(`\n📈 Live Metrics [${new Date().toLocaleTimeString()}]`);
      console.log(`  Requests: ${metrics.requestCount}`);
      console.log(`  Errors: ${metrics.errorCount}`);
      console.log(`  P95: ${metrics.responseTime.p95}ms`);
      console.log(`  Memory: ${Math.round(metrics.memory.heapUsed / 1024 / 1024)}MB`);
      console.log(`  Cache Hit Rate: ${(metrics.cache.hitRate * 100).toFixed(2)}%`);
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
    }
  }, monitoringInterval);
  
  // 負荷テスト実行
  const runner = createLoadTestRunner(config);
  const { summary, metrics } = await runner();
  
  // モニタリング停止
  clearInterval(monitoring);
  
  // 最終結果表示
  console.log("\n🎯 Final Results:");
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
}

// メイン実行
if (import.meta.main) {
  const mode = Deno.args[0] || "staged";
  
  switch (mode) {
    case "staged":
      await runStagedLoadTest();
      break;
    case "monitor":
      await runMonitoredLoadTest();
      break;
    default:
      console.log("Usage: deno run --allow-net load-test-100.ts [staged|monitor]");
      console.log("  staged  - Run staged load test (default)");
      console.log("  monitor - Run with real-time monitoring");
  }
  
  Deno.exit(0);
}