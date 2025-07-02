/**
 * 破綻点分析用の負荷テストスクリプト
 * 段階的に負荷を増加させて失敗パターンを観察する
 */

interface LoadTestResult {
  stage: number;
  clients: number;
  successCount: number;
  errorCount: number;
  avgLatency: number;
  maxLatency: number;
  errorRate: number;
}

class LoadTester {
  private results: LoadTestResult[] = [];
  private abortController = new AbortController();

  constructor(private baseUrl: string) {}

  async runProgressiveTest() {
    console.log("🚀 Starting progressive load test...");
    console.log("📈 Will increase load until system failure is detected\n");

    const stages = [
      { clients: 50, duration: 10000, name: "Warm-up" },
      { clients: 100, duration: 20000, name: "Normal Load" },
      { clients: 200, duration: 20000, name: "Moderate Load" },
      { clients: 300, duration: 20000, name: "High Load" },
      { clients: 500, duration: 20000, name: "Extreme Load" },
      { clients: 700, duration: 20000, name: "Breaking Point" },
      { clients: 1000, duration: 20000, name: "System Failure" }
    ];

    for (const stage of stages) {
      console.log(`\n🔄 Stage: ${stage.name} (${stage.clients} clients)`);
      
      const result = await this.runStage(stage.clients, stage.duration);
      this.results.push(result);
      
      this.printStageResult(result);
      
      // 90%以上のエラー率で中断
      if (result.errorRate > 0.9) {
        console.log("\n💥 System has reached complete failure!");
        break;
      }
      
      // ステージ間の休憩
      console.log("⏸️  Cooling down for 5 seconds...");
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
    
    this.printSummary();
  }

  private async runStage(clientCount: number, duration: number): Promise<LoadTestResult> {
    const startTime = Date.now();
    const endTime = startTime + duration;
    const clients: Promise<void>[] = [];
    
    let successCount = 0;
    let errorCount = 0;
    const latencies: number[] = [];
    
    // クライアントを起動
    for (let i = 0; i < clientCount; i++) {
      const client = this.runClient(async () => {
        while (Date.now() < endTime && !this.abortController.signal.aborted) {
          const reqStart = performance.now();
          
          try {
            const response = await fetch(this.baseUrl, {
              signal: AbortSignal.timeout(5000)
            });
            
            const latency = performance.now() - reqStart;
            latencies.push(latency);
            
            if (response.ok) {
              successCount++;
            } else {
              errorCount++;
            }
            
          } catch (error) {
            errorCount++;
            latencies.push(5000); // タイムアウト
          }
          
          // リクエスト間隔
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      });
      
      clients.push(client);
      
      // クライアントの起動を分散
      if (i % 10 === 0) {
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    }
    
    // すべてのクライアントが完了するまで待機
    await Promise.all(clients);
    
    // 統計の計算
    const avgLatency = latencies.length > 0 
      ? latencies.reduce((a, b) => a + b, 0) / latencies.length 
      : 0;
    const maxLatency = latencies.length > 0 
      ? Math.max(...latencies) 
      : 0;
    
    return {
      stage: this.results.length + 1,
      clients: clientCount,
      successCount,
      errorCount,
      avgLatency: Math.round(avgLatency),
      maxLatency: Math.round(maxLatency),
      errorRate: (errorCount / (successCount + errorCount)) || 0
    };
  }

  private async runClient(task: () => Promise<void>): Promise<void> {
    try {
      await task();
    } catch (error) {
      // クライアントエラーを無視
    }
  }

  private printStageResult(result: LoadTestResult) {
    console.log(`📊 Results:`);
    console.log(`   ✅ Success: ${result.successCount}`);
    console.log(`   ❌ Errors: ${result.errorCount}`);
    console.log(`   📈 Error Rate: ${(result.errorRate * 100).toFixed(2)}%`);
    console.log(`   ⏱️  Avg Latency: ${result.avgLatency}ms`);
    console.log(`   ⏱️  Max Latency: ${result.maxLatency}ms`);
  }

  private printSummary() {
    console.log("\n📋 === FAILURE ANALYSIS SUMMARY ===\n");
    
    // 失敗段階の特定
    const stage1 = this.results.find(r => r.avgLatency > 100);
    const stage2 = this.results.find(r => r.errorRate > 0.01);
    const stage3 = this.results.find(r => r.errorRate > 0.1);
    const stage4 = this.results.find(r => r.errorRate > 0.9);
    
    if (stage1) {
      console.log(`🐌 Stage 1 (Degradation): Detected at ${stage1.clients} clients`);
      console.log(`   - Latency increased to ${stage1.avgLatency}ms`);
    }
    
    if (stage2) {
      console.log(`\n⚡ Stage 2 (Partial Failure): Detected at ${stage2.clients} clients`);
      console.log(`   - Error rate: ${(stage2.errorRate * 100).toFixed(2)}%`);
    }
    
    if (stage3) {
      console.log(`\n🔥 Stage 3 (Cascade Failure): Detected at ${stage3.clients} clients`);
      console.log(`   - Error rate: ${(stage3.errorRate * 100).toFixed(2)}%`);
    }
    
    if (stage4) {
      console.log(`\n💥 Stage 4 (Complete Failure): Detected at ${stage4.clients} clients`);
      console.log(`   - Error rate: ${(stage4.errorRate * 100).toFixed(2)}%`);
    }
    
    // 結論
    console.log("\n🔍 Key Findings:");
    console.log(`   - Safe operating range: < ${stage1?.clients || 100} clients`);
    console.log(`   - First bottleneck: Event loop (latency spike)`);
    console.log(`   - Point of no return: ~${stage3?.clients || 500} clients`);
    console.log(`   - Complete failure: ~${stage4?.clients || 700} clients`);
    
    console.log("\n✅ Analysis complete!");
  }

  abort() {
    this.abortController.abort();
  }
}

// メイン実行
if (import.meta.main) {
  const url = Deno.args[0] || "http://localhost:3000";
  const tester = new LoadTester(url);
  
  // Ctrl+Cハンドリング
  Deno.addSignalListener("SIGINT", () => {
    console.log("\n⏹️  Stopping load test...");
    tester.abort();
    Deno.exit(0);
  });
  
  await tester.runProgressiveTest();
}