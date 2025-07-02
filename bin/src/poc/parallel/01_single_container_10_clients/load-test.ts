// 定数定義（ハードコード禁止）
const LOAD_TEST_CONFIG = {
  CLIENTS: 10,
  DURATION_MS: 60000, // 1分間
  REQUEST_INTERVAL_MS: 100, // 各クライアント100ms間隔
  MAX_RESPONSE_TIMES: 1000, // メトリクス保持数
} as const;

type Results = {
  requests: number;
  errors: number;
  responseTimes: number[];
};

async function makeRequest(): Promise<{ status: number; duration: number }> {
  const start = Date.now();
  
  try {
    const res = await fetch("http://localhost:3000/api/health");
    await res.text(); // bodyを消費
    return {
      status: res.status,
      duration: Date.now() - start,
    };
  } catch (error) {
    return {
      status: 0,
      duration: Date.now() - start,
    };
  }
}

async function runClient(clientId: number, results: Results, endTime: number) {
  while (Date.now() < endTime) {
    const result = await makeRequest();
    
    if (result.status === 200) {
      results.requests++;
      results.responseTimes.push(result.duration);
    } else {
      results.errors++;
    }
    
    // 各クライアントは指定間隔でリクエスト
    await new Promise(resolve => setTimeout(resolve, LOAD_TEST_CONFIG.REQUEST_INTERVAL_MS));
  }
}

async function runLoadTest() {
  const results: Results = {
    requests: 0,
    errors: 0,
    responseTimes: [],
  };
  
  console.log(`Starting load test with ${LOAD_TEST_CONFIG.CLIENTS} concurrent clients...`);
  
  const startTime = Date.now();
  const endTime = startTime + LOAD_TEST_CONFIG.DURATION_MS;
  
  // 並行してクライアントを実行
  const clientPromises = Array(LOAD_TEST_CONFIG.CLIENTS).fill(0).map((_, i) => 
    runClient(i, results, endTime)
  );
  
  await Promise.all(clientPromises);
  
  // 結果の集計
  const sorted = results.responseTimes.sort((a, b) => a - b);
  const actualDuration = (Date.now() - startTime) / 1000;
  
  const summary = {
    totalRequests: results.requests,
    totalErrors: results.errors,
    errorRate: results.requests > 0 
      ? (results.errors / (results.requests + results.errors) * 100).toFixed(2) + "%" 
      : "0.00%",
    duration: actualDuration.toFixed(0) + "s",
    throughput: Math.round(results.requests / actualDuration) + " req/s",
    responseTime: {
      min: sorted[0] || 0,
      max: sorted[sorted.length - 1] || 0,
      p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
      p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
      p99: sorted[Math.floor(sorted.length * 0.99)] || 0,
      mean: Math.round(sorted.reduce((a, b) => a + b, 0) / sorted.length) || 0,
    },
  };
  
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
  
  // メトリクスの取得
  try {
    const metricsRes = await fetch("http://localhost:3000/api/metrics");
    const metrics = await metricsRes.json();
    
    console.log("\nServer Metrics:");
    console.log(`  Request Count: ${metrics.requestCount}`);
    console.log(`  Memory RSS: ${Math.round(metrics.memory.rss / 1024 / 1024)}MB`);
    console.log(`  Heap Used: ${Math.round(metrics.memory.heapUsed / 1024 / 1024)}MB`);
  } catch (error) {
    console.error("Failed to fetch metrics:", error);
  }
  
  return summary;
}

// メイン実行
if (import.meta.main) {
  runLoadTest()
    .then(() => {
      console.log("\nLoad test completed successfully");
      Deno.exit(0);
    })
    .catch((error) => {
      console.error("Load test failed:", error);
      Deno.exit(1);
    });
}