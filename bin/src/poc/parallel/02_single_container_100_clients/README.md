# 02_single_container_100_clients

## 概要

単一コンテナで100クライアントの同時接続を処理。前POCの10倍の負荷で、単一コンテナのスケーラビリティと限界点を探ります。

## 目的

- 10倍負荷でのパフォーマンス劣化の観察
- コネクション管理の最適化必要性の確認
- リソース使用効率の評価
- ボトルネックの特定

## アーキテクチャ

```
┌─────────────────────────────────┐
│       Load Generator            │
│   (100 Concurrent Clients)      │
│  ┌─────────────────────────┐    │
│  │ Connection Pool (100)   │    │
│  │ Rate Limiting          │    │
│  │ Metrics Collection     │    │
│  └─────────────────────────┘    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│     Application Container       │
│         Optimized for           │
│      High Concurrency           │
│  ┌─────────────────────────┐    │
│  │ Event Loop (libuv)      │    │
│  │ Worker Threads Pool     │    │
│  │ Connection Queue        │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

## 検証項目

### 1. スケーラビリティ指標
- **線形スケーリング**: 10倍の負荷で性能劣化が2倍以内
- **レスポンスタイム**: P95 < 200ms, P99 < 500ms
- **スループット**: 最低1000 req/s
- **並行性効率**: 同時100接続の維持

### 2. リソース最適化
- **CPU使用率**: < 60%
- **メモリ使用量**: < 1GB
- **ファイルディスクリプタ**: < 500
- **コンテキストスイッチ**: 最小化

### 3. 安定性と予測可能性
- **ジッター**: レスポンスタイムの変動 < 20%
- **エラー率**: < 0.1%
- **リカバリ時間**: 負荷減少後1秒以内に正常化

## TDDアプローチ

### Red Phase (高負荷でのテスト)
```typescript
// scale-100.test.ts
import { assertEquals, assertLess } from "@std/assert";
import { MetricsCollector } from "./test-utils.ts";

Deno.test("test_scale_100_clients_handle_efficiently", async () => {
  const metricsCollector = new MetricsCollector();

    const clients = Array(100).fill(0).map((_, i) => ({
      id: `client-${i}`,
      requests: []
    }));
    
    // 各クライアントが10リクエストを送信
    const testDuration = 10000; // 10秒間
    const results = await Promise.all(
      clients.map(async (client) => {
        const clientResults = [];
        const startTime = Date.now();
        
        while (Date.now() - startTime < testDuration) {
          const reqStart = Date.now();
          try {
            const res = await fetch(`http://localhost:3000/api/data/${client.id}`);
            const duration = Date.now() - reqStart;
            
            clientResults.push({
              status: res.status,
              duration,
              timestamp: Date.now()
            });
          } catch (error) {
            clientResults.push({
              status: 'error',
              error: error.message,
              timestamp: Date.now()
            });
          }
          
          // 適応的な待機時間
          const waitTime = Math.max(10, 100 - clientResults.length);
          await new Promise(resolve => setTimeout(resolve, waitTime));
        }
        
        return {
          clientId: client.id,
          results: clientResults
        };
      })
    );
    
    // 集計
    const allRequests = results.flatMap(r => r.results);
    const successfulRequests = allRequests.filter(r => r.status === 200);
    const errorRequests = allRequests.filter(r => r.status !== 200);
    
    // アサーション
    expect(successfulRequests.length / allRequests.length).toBeGreaterThan(0.999); // 99.9%成功率
    
    // レスポンスタイム分析
    const responseTimes = successfulRequests.map(r => r.duration).sort((a, b) => a - b);
    const p95 = responseTimes[Math.floor(responseTimes.length * 0.95)];
    const p99 = responseTimes[Math.floor(responseTimes.length * 0.99)];
    
    expect(p95).toBeLessThan(200);
    expect(p99).toBeLessThan(500);
});

Deno.test("test_performance_no_degradation_over_time", async () => {
    const measurements = [];
    const measurementInterval = 1000; // 1秒ごと
    const totalDuration = 60000; // 1分間
    
    const measurePerformance = async () => {
      const concurrentRequests = Array(10).fill(0).map(async () => {
        const start = Date.now();
        const res = await fetch('http://localhost:3000/api/health');
        return {
          duration: Date.now() - start,
          status: res.status
        };
      });
      
      const results = await Promise.all(concurrentRequests);
      return {
        timestamp: Date.now(),
        avgDuration: results.reduce((sum, r) => sum + r.duration, 0) / results.length,
        successRate: results.filter(r => r.status === 200).length / results.length
      };
    };
    
    // 定期的に性能測定
    const startTime = Date.now();
    while (Date.now() - startTime < totalDuration) {
      measurements.push(await measurePerformance());
      await new Promise(resolve => setTimeout(resolve, measurementInterval));
    }
    
    // 性能劣化がないことを確認
    const firstHalf = measurements.slice(0, measurements.length / 2);
    const secondHalf = measurements.slice(measurements.length / 2);
    
    const avgFirstHalf = firstHalf.reduce((sum, m) => sum + m.avgDuration, 0) / firstHalf.length;
    const avgSecondHalf = secondHalf.reduce((sum, m) => sum + m.avgDuration, 0) / secondHalf.length;
    
    // 後半が前半より20%以上遅くならないこと
    expect(avgSecondHalf).toBeLessThan(avgFirstHalf * 1.2);
});

Deno.test({
  name: "test_resources_use_efficiently",
  sanitizeOps: false,
  sanitizeResources: false,
}, async () => {
    const resourceSnapshots = [];
    
    // リソース使用状況を監視
    const monitoringInterval = setInterval(async () => {
      const stats = await getContainerStats();
      resourceSnapshots.push({
        timestamp: Date.now(),
        cpu: stats.cpu_stats.cpu_usage.total_usage,
        memory: stats.memory_stats.usage,
        networkRx: stats.networks.eth0.rx_bytes,
        networkTx: stats.networks.eth0.tx_bytes
      });
    }, 100);
    
    // 100クライアントで負荷をかける
    await runLoadTest(100, 10000);
    
    clearInterval(monitoringInterval);
    
    // CPU使用率が60%以下
    const cpuUsages = calculateCpuPercentages(resourceSnapshots);
    const avgCpu = cpuUsages.reduce((a, b) => a + b) / cpuUsages.length;
    expect(avgCpu).toBeLessThan(60);
    
    // メモリ使用量が1GB以下
    const maxMemory = Math.max(...resourceSnapshots.map(s => s.memory));
    expect(maxMemory).toBeLessThan(1024 * 1024 * 1024);
});
```

### Green Phase (最適化された実装)
```typescript
// server.ts
import { createMetricsManager, createHealthResponse, createMetricsResponse } from "../01_single_container_10_clients/mod.ts";
import { Pool } from "./worker-pool.ts";

// ワーカープールの設定
const numWorkers = Math.min(navigator.hardwareConcurrency || 4, 4);
const workerPool = new Pool(numWorkers, "./worker.ts");

// リクエストキューの管理
let activeRequests = 0;
const MAX_CONCURRENT_REQUESTS = 50;

// データキャッシュ（LRU実装）
class LRUCache<T> {
  private cache = new Map<string, { data: T; timestamp: number }>();
  constructor(private maxSize: number, private ttl: number) {}
  
  get(key: string): T | undefined {
    const item = this.cache.get(key);
    if (!item) return undefined;
    
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return undefined;
    }
    
    // LRU: 再度セットして最新に
    this.cache.delete(key);
    this.cache.set(key, item);
    return item.data;
  }
  
  set(key: string, data: T): void {
    // サイズ制限
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }
  
  get size(): number {
    return this.cache.size;
  }
}

const cache = new LRUCache<any>(1000, 60000); // 1000エントリ、TTL 1分

// メトリクス管理
const metricsManager = createMetricsManager({ maxMetricsSize: 10000 });
const startTime = performance.now();

// メモリ使用量を取得
function getMemoryUsage() {
  const usage = Deno.memoryUsage();
  return {
    rss: usage.rss,
    heapTotal: usage.heapTotal,
    heapUsed: usage.heapUsed,
  };
}

// リクエストハンドラー
const requestHandler = async (request: Request): Promise<Response> => {
  const url = new URL(request.url);
  const start = Date.now();
  
  // リクエスト制限
  if (activeRequests >= MAX_CONCURRENT_REQUESTS) {
    metricsManager.recordError();
    return new Response(
      JSON.stringify({
        error: "Server too busy",
        retry_after: 1,
      }),
      {
        status: 503,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
  
  activeRequests++;
  
  try {
    // ヘルスチェックエンドポイント
    if (url.pathname === "/api/health" && request.method === "GET") {
      const health = createHealthResponse(startTime);
      const duration = Date.now() - start;
      metricsManager.recordSuccess(duration);
      return new Response(JSON.stringify(health), {
        headers: { "content-type": "application/json" },
      });
    }
    
    // メトリクスエンドポイント
    if (url.pathname === "/api/metrics" && request.method === "GET") {
      const metrics = metricsManager.getMetrics();
      const memoryUsage = getMemoryUsage();
      const metricsResponse = createMetricsResponse(metrics, memoryUsage);
      const duration = Date.now() - start;
      metricsManager.recordSuccess(duration);
      return new Response(JSON.stringify(metricsResponse), {
        headers: { "content-type": "application/json" },
      });
    }
    
    // データエンドポイント
    const dataMatch = url.pathname.match(/^\/api\/data\/(.+)$/);
    if (dataMatch && request.method === "GET") {
      const clientId = dataMatch[1];
      const cacheKey = `data:${clientId}`;
      
      // キャッシュチェック
      let data = cache.get(cacheKey);
      if (!data) {
        // ワーカープールで処理
        data = await workerPool.run("generateData", clientId);
        cache.set(cacheKey, data);
      }
      
      const duration = Date.now() - start;
      metricsManager.recordSuccess(duration);
      return new Response(JSON.stringify(data), {
        headers: { "Content-Type": "application/json" },
      });
    }
    
    // 404 Not Found
    return new Response("Not Found", { status: 404 });
  } catch (error) {
    metricsManager.recordError();
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : String(error) }),
      {
        status: 500,
        headers: { "content-type": "application/json" },
      },
    );
  } finally {
    activeRequests--;
  }
};

// サーバー起動
const port = parseInt(Deno.env.get("PORT") || "3000");
const server = Deno.serve(
  { port },
  requestHandler
);

console.log(`Server running on port ${port}`);
console.log(`Process ID: ${Deno.pid}`);
console.log(`Deno version: ${Deno.version.deno}`);

// グレースフルシャットダウン
Deno.addSignalListener("SIGTERM", () => {
  console.log("\nReceived SIGTERM, shutting down gracefully...");
  workerPool.terminate();
  server.shutdown();
});

Deno.addSignalListener("SIGINT", () => {
  console.log("\nReceived SIGINT, shutting down gracefully...");
  workerPool.terminate();
  server.shutdown();
});

await server.finished;

// worker.ts - ワーカープロセスでの処理
self.onmessage = (e: MessageEvent) => {
  const { id, method, args } = e.data;
  
  if (method === "generateData") {
    const clientId = args[0];
    const data = {
      id: clientId,
      value: Math.random() * 1000,
      workerId: self.name,
      items: Array(10).fill(0).map((_, i) => ({
        index: i,
        data: `Item ${i} for client ${clientId}`,
      })),
    };
    
    self.postMessage({ id, result: data });
  }
};
```

### Refactor Phase (さらなる最適化)
```typescript
// optimizations.ts

// 1. 非同期処理の最適化
export class ConcurrencyLimiter {
  private queue: Array<() => void> = [];
  private running = 0;
  
  constructor(private limit: number) {}
  
  async run<T>(fn: () => Promise<T>): Promise<T> {
    while (this.running >= this.limit) {
      await new Promise<void>((resolve) => this.queue.push(resolve));
    }
    
    this.running++;
    try {
      return await fn();
    } finally {
      this.running--;
      const next = this.queue.shift();
      if (next) next();
    }
  }
}

// 2. メモリプールの実装
export class ObjectPool<T> {
  private pool: T[] = [];
  
  constructor(
    private factory: () => T,
    private reset: (obj: T) => void,
    private maxSize = 100,
  ) {}
  
  acquire(): T {
    return this.pool.pop() || this.factory();
  }
  
  release(obj: T): void {
    if (this.pool.length < this.maxSize) {
      this.reset(obj);
      this.pool.push(obj);
    }
  }
}

// 3. バッチ処理の実装
export class BatchProcessor<T> {
  private batch: T[] = [];
  private timer?: number;
  
  constructor(
    private processFn: (items: T[]) => void | Promise<void>,
    private batchSize = 10,
    private flushInterval = 100,
  ) {}
  
  add(item: T): void {
    this.batch.push(item);
    
    if (this.batch.length >= this.batchSize) {
      this.flush();
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), this.flushInterval);
    }
  }
  
  flush(): void {
    if (this.batch.length === 0) return;
    
    const items = this.batch.splice(0);
    this.processFn(items);
    
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = undefined;
    }
  }
}
```

## 実装手順

### 1. Docker設定の最適化
```dockerfile
# Dockerfile
FROM denoland/deno:alpine-2.0.0

# システムの最適化
RUN apk add --no-cache tini

WORKDIR /app

# 依存関係のキャッシュ
COPY deno.json deno.lock ./
RUN deno cache --lock=deno.lock deno.json

# アプリケーションコピー
COPY . .

# 事前コンパイル
RUN deno cache server.ts

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["deno", "run", "--allow-net", "--allow-env", "--allow-read", "server.ts"]
```

### 2. Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: production
      PORT: 3000
      WORKERS: 4
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '1.0'
          memory: 512M
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    sysctls:
      net.core.somaxconn: 1024
      net.ipv4.tcp_tw_reuse: 1
```

### 3. 負荷テストツール設定
```typescript
// load-test-100.ts
import { createLoadTestRunner, LOAD_TEST_CONFIG } from "../01_single_container_10_clients/load-test.ts";

export const SCALE_TEST_CONFIG = {
  ...LOAD_TEST_CONFIG,
  CLIENTS: 100,
  DURATION_MS: 180000, // 3分間
  REQUEST_INTERVAL_MS: 50, // より高頻度

};

// ステージ付き負荷テスト
export async function runStagedLoadTest() {
  const stages = [
    { duration: 30000, targetClients: 50 },   // ウォームアップ
    { duration: 60000, targetClients: 100 },  // 100クライアントまで増加
    { duration: 180000, targetClients: 100 }, // 100クライアントを維持
    { duration: 30000, targetClients: 0 },    // クールダウン
  ];
  
  console.log("Starting staged load test...");
  
  for (const stage of stages) {
    console.log(`Stage: ${stage.targetClients} clients for ${stage.duration / 1000}s`);
    
    const config = {
      ...SCALE_TEST_CONFIG,
      clients: stage.targetClients,
      durationMs: stage.duration,
      targetUrl: "http://localhost:3000/api/data/client-${id}",
    };
    
    const runner = createLoadTestRunner(config);
    const { summary, metrics } = await runner();
    
    // 閾値チェック
    if (summary.responseTime.p95 > 200) {
      console.error(`❌ P95 response time ${summary.responseTime.p95}ms exceeds 200ms`);
    }
    if (summary.responseTime.p99 > 500) {
      console.error(`❌ P99 response time ${summary.responseTime.p99}ms exceeds 500ms`);
    }
    if (parseFloat(summary.errorRate) > 0.1) {
      console.error(`❌ Error rate ${summary.errorRate} exceeds 0.1%`);
    }
  }
}

if (import.meta.main) {
  await runStagedLoadTest();
}
```

## 実行方法

```bash
# 1. ビルドと起動
docker-compose build
docker-compose up -d

# 2. ヘルスチェック
curl http://localhost:3000/api/health

# 3. 単体テスト実行
deno test --allow-net scale-100.test.ts

# 4. 負荷テスト実行
deno run --allow-net load-test-100.ts

# 5. リアルタイムモニタリング
docker stats
watch -n 1 'curl -s http://localhost:3000/api/metrics'

# 6. ログ確認
docker-compose logs -f
```

## パフォーマンスチューニング

### 1. Deno最適化
```bash
# V8オプション
--v8-flags=--max-old-space-size=768  # ヒープサイズ制限
--v8-flags=--optimize-for-size       # メモリ最適化
--v8-flags=--gc-interval=100         # GC頻度調整
```

### 2. OS最適化
```bash
# ファイルディスクリプタ
ulimit -n 65536

# TCPチューニング
sysctl -w net.core.somaxconn=1024
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.ip_local_port_range="1024 65535"
```

### 3. アプリケーション最適化
- Web Workersによる並列処理
- LRUキャッシング戦略
- 非同期リクエスト制限
- バッチ処理パターン

## 成功基準

- [ ] 100同時接続で安定動作（1時間）
- [ ] P95 < 200ms, P99 < 500ms
- [ ] エラー率 < 0.1%
- [ ] CPU使用率 < 60%
- [ ] メモリ使用量 < 1GB
- [ ] キャッシュヒット率 > 50%

## トラブルシューティング

### 問題: "Too many open files"エラー
```bash
# 現在の制限確認
ulimit -n

# 制限を増やす
ulimit -n 65536

# Dockerコンテナ内でも設定
docker run --ulimit nofile=65536:65536 ...
```

### 問題: メモリ使用量が増加し続ける
```typescript
// ヒープダンプ取得
Deno.addSignalListener("SIGUSR2", async () => {
  const snapshot = await Deno.core.takeHeapSnapshot();
  await Deno.writeTextFile(`heap-${Date.now()}.heapsnapshot`, snapshot);
});
```

### 問題: CPU使用率が高い
```bash
# プロファイリング実行
deno run --inspect-brk --allow-net --allow-env server.ts
# Chrome DevToolsでプロファイリング
```

## 次のステップ

100クライアントでの安定動作を確認後、`03_single_container_1000_clients`で10倍の1000クライアントに挑戦し、単一コンテナの限界を探ります。

## 学んだこと

- 単純な10倍スケールは線形ではない
- リソース管理とキャッシングが重要
- Web Workersで効率的な並列処理
- 適切な監視とメトリクスが必須

## 参考資料

- [Deno Workers Documentation](https://docs.deno.com/runtime/manual/runtime/workers)
- [High Performance Deno](https://deno.land/manual/runtime/performance)
- [Deno Testing Guide](https://docs.deno.com/runtime/manual/basics/testing/)
- [Docker Resource Management](https://docs.docker.com/config/containers/resource_constraints/)