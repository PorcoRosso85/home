/**
 * ロードバランサーと2コンテナの負荷テスト
 * 分散の均等性とパフォーマンスを検証
 */

interface LoadTestConfig {
  url: string;
  duration: number;
  concurrentClients: number;
  requestsPerClient: number;
}

interface TestResult {
  totalRequests: number;
  successCount: number;
  errorCount: number;
  distribution: Record<string, number>;
  avgLatency: number;
  p95Latency: number;
  p99Latency: number;
  throughput: number;
}

class LoadTester {
  private results: {
    latencies: number[];
    errors: number;
    containerDistribution: Record<string, number>;
  } = {
    latencies: [],
    errors: 0,
    containerDistribution: {}
  };

  async runTest(config: LoadTestConfig): Promise<TestResult> {
    console.log("🚀 Starting load test...");
    console.log(`📊 Configuration:`);
    console.log(`   - URL: ${config.url}`);
    console.log(`   - Duration: ${config.duration}ms`);
    console.log(`   - Concurrent clients: ${config.concurrentClients}`);
    console.log(`   - Requests per client: ${config.requestsPerClient}`);
    console.log("");

    const startTime = Date.now();
    const clients: Promise<void>[] = [];

    // クライアントを起動
    for (let i = 0; i < config.concurrentClients; i++) {
      const client = this.runClient(i, config);
      clients.push(client);
    }

    // すべてのクライアントが完了するまで待機
    await Promise.all(clients);

    const endTime = Date.now();
    const testDuration = (endTime - startTime) / 1000; // 秒

    // 結果を集計
    return this.calculateResults(testDuration);
  }

  private async runClient(clientId: number, config: LoadTestConfig): Promise<void> {
    const sessionId = `client-${clientId}-${Date.now()}`;
    
    for (let i = 0; i < config.requestsPerClient; i++) {
      const startTime = performance.now();
      
      try {
        // /api/whoami エンドポイントでコンテナを識別
        const response = await fetch(`${config.url}/api/whoami`, {
          headers: {
            'X-Client-Id': clientId.toString(),
            'X-Request-Id': `${clientId}-${i}`
          }
        });
        
        const latency = performance.now() - startTime;
        this.results.latencies.push(latency);
        
        if (response.ok) {
          const data = await response.json();
          const container = data.container || 'unknown';
          this.results.containerDistribution[container] = 
            (this.results.containerDistribution[container] || 0) + 1;
        } else {
          this.results.errors++;
        }
      } catch (error) {
        this.results.errors++;
        this.results.latencies.push(performance.now() - startTime);
      }
      
      // リクエスト間隔（過負荷を避ける）
      await new Promise(resolve => setTimeout(resolve, 50));
    }
  }

  private calculateResults(duration: number): TestResult {
    const totalRequests = this.results.latencies.length;
    const successCount = totalRequests - this.results.errors;
    
    // レイテンシー統計
    const sortedLatencies = [...this.results.latencies].sort((a, b) => a - b);
    const avgLatency = sortedLatencies.reduce((a, b) => a + b, 0) / sortedLatencies.length;
    const p95Index = Math.floor(sortedLatencies.length * 0.95);
    const p99Index = Math.floor(sortedLatencies.length * 0.99);
    
    return {
      totalRequests,
      successCount,
      errorCount: this.results.errors,
      distribution: this.results.containerDistribution,
      avgLatency: Math.round(avgLatency),
      p95Latency: Math.round(sortedLatencies[p95Index] || 0),
      p99Latency: Math.round(sortedLatencies[p99Index] || 0),
      throughput: Math.round(totalRequests / duration)
    };
  }
}

// 結果の可視化
function printResults(result: TestResult) {
  console.log("\n📊 Test Results:");
  console.log("================");
  
  console.log(`\n✅ Success Rate: ${((result.successCount / result.totalRequests) * 100).toFixed(2)}%`);
  console.log(`   - Total requests: ${result.totalRequests}`);
  console.log(`   - Successful: ${result.successCount}`);
  console.log(`   - Failed: ${result.errorCount}`);
  
  console.log(`\n⚖️  Load Distribution:`);
  const total = Object.values(result.distribution).reduce((a, b) => a + b, 0);
  Object.entries(result.distribution).forEach(([container, count]) => {
    const percentage = (count / total) * 100;
    const bar = '█'.repeat(Math.round(percentage / 2));
    console.log(`   ${container}: ${bar} ${percentage.toFixed(1)}% (${count} requests)`);
  });
  
  console.log(`\n⏱️  Latency Statistics:`);
  console.log(`   - Average: ${result.avgLatency}ms`);
  console.log(`   - P95: ${result.p95Latency}ms`);
  console.log(`   - P99: ${result.p99Latency}ms`);
  
  console.log(`\n🚀 Throughput: ${result.throughput} req/s`);
  
  // 分散の均等性を評価
  const containers = Object.keys(result.distribution);
  if (containers.length === 2) {
    const expectedPerContainer = total / 2;
    const deviations = Object.values(result.distribution).map(
      count => Math.abs(count - expectedPerContainer) / expectedPerContainer
    );
    const maxDeviation = Math.max(...deviations);
    
    console.log(`\n📏 Distribution Quality:`);
    if (maxDeviation < 0.1) {
      console.log("   ✅ Excellent - deviation < 10%");
    } else if (maxDeviation < 0.2) {
      console.log("   ⚠️  Good - deviation < 20%");
    } else {
      console.log("   ❌ Poor - deviation > 20%");
    }
  }
}

// フェイルオーバーテスト
async function testFailover(tester: LoadTester) {
  console.log("\n🔥 Testing Failover Scenario...");
  console.log("================================");
  
  // 通常の負荷テスト
  const normalResult = await tester.runTest({
    url: "http://localhost:8080",
    duration: 10000,
    concurrentClients: 20,
    requestsPerClient: 50
  });
  
  console.log("\n📊 Normal Operation:");
  printResults(normalResult);
  
  console.log("\n⚠️  Simulating container failure...");
  console.log("   (In real test, one container would be stopped)");
  
  // フェイルオーバー時のテスト
  const failoverResult = await tester.runTest({
    url: "http://localhost:8080",
    duration: 10000,
    concurrentClients: 20,
    requestsPerClient: 50
  });
  
  console.log("\n📊 During Failover:");
  printResults(failoverResult);
}

// メイン実行
if (import.meta.main) {
  const tester = new LoadTester();
  
  // 基本的な負荷テスト
  const result = await tester.runTest({
    url: Deno.args[0] || "http://localhost:8080",
    duration: 30000, // 30秒
    concurrentClients: 50,
    requestsPerClient: 100
  });
  
  printResults(result);
  
  // フェイルオーバーテストを実行するかどうか
  if (Deno.args.includes("--failover")) {
    await testFailover(new LoadTester());
  }
}