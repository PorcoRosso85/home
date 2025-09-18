import { assertEquals, assertLess } from "@std/assert";

// Helper function to get container memory usage
async function getContainerMemoryUsage(): Promise<number> {
  const res = await fetch("http://localhost:3000/api/metrics");
  const data = await res.json();
  return data.memory.rss;
}

Deno.test("test_concurrent_connections_10_clients_all_succeed", async () => {
  const clients = Array(10).fill(0).map((_, i) => ({
    id: `client-${i}`,
    startTime: Date.now(),
  }));
  
  const results = await Promise.all(
    clients.map(async (client) => {
      const res = await fetch("http://localhost:3000/api/health");
      await res.text(); // bodyを消費
      return {
        ...client,
        status: res.status,
        duration: Date.now() - client.startTime,
      };
    })
  );
  
  // すべて成功すること
  assertEquals(results.every(r => r.status === 200), true);
  
  // レスポンスタイムが100ms以内
  assertEquals(results.every(r => r.duration < 100), true);
});

Deno.test("test_performance_100_requests_low_variance", async () => {
  const measurements: Array<{ iteration: number; status: number; duration: number }> = [];
  
  // 100回連続でリクエスト
  for (let i = 0; i < 100; i++) {
    const start = Date.now();
    const res = await fetch("http://localhost:3000/api/health");
    await res.text(); // bodyを消費
    const duration = Date.now() - start;
    
    measurements.push({
      iteration: i,
      status: res.status,
      duration,
    });
    
    // 10ms待機（負荷を現実的に）
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  
  // 標準偏差を計算
  const durations = measurements.map(m => m.duration);
  const mean = durations.reduce((a, b) => a + b) / durations.length;
  const variance = durations.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / durations.length;
  const stdDev = Math.sqrt(variance);
  
  assertLess(stdDev, 10);
});

Deno.test({
  name: "test_memory_1000_requests_no_leak",
  sanitizeOps: false,
  sanitizeResources: false,
}, async () => {
  const initialMemory = await getContainerMemoryUsage();
  
  // 1000回リクエスト
  for (let i = 0; i < 1000; i++) {
    const res = await fetch("http://localhost:3000/api/health");
    await res.text(); // bodyを消費
  }
  
  // GCを待つ
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  const finalMemory = await getContainerMemoryUsage();
  const memoryIncrease = finalMemory - initialMemory;
  
  // メモリ増加が10MB以内
  assertLess(memoryIncrease, 10 * 1024 * 1024);
});

Deno.test("test_metrics_endpoint_after_requests_valid_structure", async () => {
  // Send some requests first
  for (let i = 0; i < 10; i++) {
    const res = await fetch("http://localhost:3000/api/health");
    await res.text(); // bodyを消費
  }
  
  const res = await fetch("http://localhost:3000/api/metrics");
  assertEquals(res.status, 200);
  
  const metrics = await res.json();
  
  // Verify metrics structure
  assertEquals(typeof metrics.requestCount, "number");
  assertEquals(typeof metrics.errorCount, "number");
  assertEquals(typeof metrics.responseTime, "object");
  assertEquals(typeof metrics.responseTime.p50, "number");
  assertEquals(typeof metrics.responseTime.p95, "number");
  assertEquals(typeof metrics.responseTime.p99, "number");
  assertEquals(typeof metrics.memory, "object");
  
  // Verify metrics values
  assertEquals(metrics.requestCount > 0, true);
  assertEquals(metrics.errorCount, 0);
});

Deno.test("test_memory_usage_normal_operation_under_500mb", async () => {
  const res = await fetch("http://localhost:3000/api/metrics");
  const metrics = await res.json();
  
  // Memory should be less than 500MB
  assertLess(metrics.memory.heapUsed, 500 * 1024 * 1024);
});