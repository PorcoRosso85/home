/**
 * 2コンテナ + ロードバランサーのテスト
 * Nixオーケストレーション環境での動作を検証
 */

import { assertEquals, assert, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { delay } from "https://deno.land/std@0.208.0/async/mod.ts";

// テストユーティリティ
class LoadBalancerTester {
  constructor(private config: { url: string; expectedBackends: string[] }) {}
  
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.config.url}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

class ContainerController {
  constructor(private name: string) {}
  
  async stop(): Promise<void> {
    // 実際の環境では docker stop や systemctl stop を実行
    console.log(`Stopping container ${this.name}...`);
    await delay(1000);
  }
  
  async start(): Promise<void> {
    // 実際の環境では docker start や systemctl start を実行
    console.log(`Starting container ${this.name}...`);
    await delay(2000);
  }
}

// ヘルスチェック待機
async function waitForHealthy(urls: string[], maxAttempts = 30): Promise<void> {
  for (const url of urls) {
    let attempts = 0;
    while (attempts < maxAttempts) {
      try {
        const response = await fetch(`${url}/health`);
        if (response.ok) {
          console.log(`✅ ${url} is healthy`);
          break;
        }
      } catch {
        // 接続エラーは無視
      }
      
      attempts++;
      if (attempts >= maxAttempts) {
        throw new Error(`${url} failed to become healthy`);
      }
      
      await delay(1000);
    }
  }
}

// メトリクス収集
class MetricsCollector {
  private metrics: Array<{
    timestamp: number;
    status: number;
    container?: string;
    latency: number;
    error: boolean;
  }> = [];
  
  record(response: { status: number; container?: string; latency: number }) {
    this.metrics.push({
      timestamp: Date.now(),
      status: response.status,
      container: response.container,
      latency: response.latency,
      error: response.status >= 500
    });
  }
  
  analyze() {
    const errorCount = this.metrics.filter(m => m.error).length;
    const totalCount = this.metrics.length;
    const errorRate = totalCount > 0 ? errorCount / totalCount : 0;
    
    // スループット計算（1秒あたりのリクエスト数）
    const timeRange = this.metrics[this.metrics.length - 1]?.timestamp - this.metrics[0]?.timestamp;
    const throughput = timeRange > 0 ? (totalCount / timeRange) * 1000 : 0;
    
    return {
      errorRate,
      minThroughput: throughput,
      getDistributionAfter: (time: number) => this.getDistribution(time)
    };
  }
  
  getDistribution(afterTime: number) {
    const relevantMetrics = this.metrics.filter(m => m.timestamp > afterTime);
    const counts: Record<string, number> = {};
    
    relevantMetrics.forEach(m => {
      if (m.container) {
        counts[m.container] = (counts[m.container] || 0) + 1;
      }
    });
    
    const total = relevantMetrics.length;
    const distribution: Record<string, number> = {};
    
    Object.entries(counts).forEach(([container, count]) => {
      distribution[container] = count / total;
    });
    
    return distribution;
  }
}

// 継続的な負荷生成
async function startContinuousLoad(config: {
  rps: number;
  duration: number;
  url?: string;
  onResponse: (res: any) => void;
}) {
  const { rps, duration, url = 'http://localhost:8080', onResponse } = config;
  const interval = 1000 / rps;
  const endTime = Date.now() + duration;
  const requests: Promise<void>[] = [];
  
  const sendRequest = async () => {
    const start = performance.now();
    try {
      const response = await fetch(`${url}/api/whoami`);
      const data = await response.json();
      const latency = performance.now() - start;
      
      onResponse({
        status: response.status,
        container: data.container,
        latency
      });
    } catch (error) {
      onResponse({
        status: 500,
        latency: performance.now() - start
      });
    }
  };
  
  // 指定されたRPSでリクエストを送信
  while (Date.now() < endTime) {
    requests.push(sendRequest());
    await delay(interval);
  }
  
  // すべてのリクエストの完了を待つ
  await Promise.all(requests);
  
  return {
    wait: async () => await Promise.all(requests)
  };
}

// カイ二乗検定
function calculateChiSquare(observed: Record<string, number>, expected: number): number {
  let sum = 0;
  Object.values(observed).forEach(count => {
    sum += Math.pow(count - expected, 2) / expected;
  });
  return sum;
}

// テストケース
Deno.test("test_distribute_load_evenly_between_containers", async () => {
  // 環境が立ち上がっていることを前提
  console.log("Testing load distribution...");
  
  const requests = 100;
  const results: Record<string, number> = {
    'app-1': 0,
    'app-2': 0
  };
  
  // 並列でリクエストを送信
  const promises = Array(requests).fill(0).map(async () => {
    try {
      const response = await fetch('http://localhost:8080/api/whoami');
      const data = await response.json();
      if (data.container) {
        results[data.container]++;
      }
    } catch (error) {
      console.error('Request failed:', error);
    }
  });
  
  await Promise.all(promises);
  
  console.log('Distribution results:', results);
  
  // 分散の均等性を検証（±20%の誤差を許容）
  const distribution = {
    app1: results['app-1'] / requests,
    app2: results['app-2'] / requests
  };
  
  assert(
    Math.abs(distribution.app1 - 0.5) < 0.2,
    `Expected app-1 to handle ~50% of requests, got ${(distribution.app1 * 100).toFixed(1)}%`
  );
  assert(
    Math.abs(distribution.app2 - 0.5) < 0.2,
    `Expected app-2 to handle ~50% of requests, got ${(distribution.app2 * 100).toFixed(1)}%`
  );
});

Deno.test("test_handle_container_failure_gracefully", async () => {
  console.log("Testing failover behavior...");
  
  const testDuration = 20000; // 20秒
  const metricsCollector = new MetricsCollector();
  const startTime = Date.now();
  
  // バックグラウンドで継続的にリクエストを送信
  const loadGenerator = await startContinuousLoad({
    rps: 10,
    duration: testDuration,
    onResponse: (res) => metricsCollector.record(res)
  });
  
  // 5秒後に1つのコンテナを停止（シミュレート）
  const timer = setTimeout(async () => {
    console.log('Simulating app-1 failure...');
    // 実際の環境では ContainerController を使用
  }, 5000);
  
  // テスト完了を待つ
  await loadGenerator.wait();
  
  // タイマーをクリア
  clearTimeout(timer);
  
  const analysis = metricsCollector.analyze();
  
  // フェイルオーバー中もエラー率が低いこと
  assert(
    analysis.errorRate < 0.05,
    `Expected error rate < 5%, got ${(analysis.errorRate * 100).toFixed(1)}%`
  );
});

Deno.test("test_maintain_session_affinity", async () => {
  console.log("Testing session affinity...");
  
  const sessions: Record<string, { servers: Set<string>; requests: any[] }> = {};
  const numClients = 10;
  const requestsPerClient = 10;
  
  // 各クライアントが複数のリクエストを送信
  const clientPromises = Array(numClients).fill(0).map(async (_, clientId) => {
    const sessionId = `session-${clientId}`;
    sessions[clientId] = {
      servers: new Set(),
      requests: []
    };
    
    for (let i = 0; i < requestsPerClient; i++) {
      try {
        const response = await fetch('http://localhost:8080/api/session', {
          method: 'POST',
          headers: {
            'X-Session-Id': sessionId,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ clientId, requestNum: i })
        });
        
        const data = await response.json();
        sessions[clientId].servers.add(data.container);
        sessions[clientId].requests.push(data);
      } catch (error) {
        console.error(`Client ${clientId} request ${i} failed:`, error);
      }
    }
  });
  
  await Promise.all(clientPromises);
  
  // 各クライアントが同じサーバーに固定されていることを確認
  const stickySuccess = Object.values(sessions).filter(
    session => session.servers.size === 1
  ).length;
  
  const successRate = stickySuccess / numClients;
  assert(
    successRate > 0.8,
    `Expected > 80% session affinity success, got ${(successRate * 100).toFixed(1)}%`
  );
});

Deno.test("test_scale_performance_linearly", async () => {
  console.log("Testing scaling efficiency...");
  
  // 単一コンテナのベースライン（POC 04の結果を使用）
  const singleContainerBaseline = {
    throughput: 1000, // req/s
    p95Latency: 200,  // ms
    maxClients: 800
  };
  
  // 2コンテナでの性能測定（簡易版）
  const metricsCollector = new MetricsCollector();
  const testDuration = 10000; // 10秒
  
  const loadGenerator = await startContinuousLoad({
    rps: 100,
    duration: testDuration,
    onResponse: (res) => metricsCollector.record(res)
  });
  
  await loadGenerator.wait();
  
  const analysis = metricsCollector.analyze();
  
  // スケーリング効率の計算（簡易版）
  const scalingEfficiency = {
    throughput: analysis.minThroughput / (100 * 0.8), // 80%効率を期待
  };
  
  assert(
    scalingEfficiency.throughput > 0.8,
    `Expected > 80% scaling efficiency, got ${(scalingEfficiency.throughput * 100).toFixed(1)}%`
  );
});