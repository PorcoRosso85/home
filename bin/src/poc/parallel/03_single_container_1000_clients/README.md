# 03_single_container_1000_clients

## 概要

単一コンテナで1000クライアントの同時接続に挑戦。C10K問題の現代版として、単一コンテナの絶対的な限界を探り、スケールアウトの必要性を実証します。

## 目的

- 単一コンテナの限界点の特定
- C10K問題への現代的アプローチの検証
- イベント駆動アーキテクチャの限界確認
- 水平スケーリングの必要性の定量的証明

## アーキテクチャ

```
┌─────────────────────────────────┐
│      Load Generator Farm        │
│   (1000 Concurrent Clients)     │
│  ┌─────────────────────────┐    │
│  │ Distributed Clients     │    │
│  │ Rate Control           │    │
│  │ Backpressure Handling  │    │
│  └─────────────────────────┘    │
└────────────┬────────────────────┘
             │ Massive Load
             ▼
┌─────────────────────────────────┐
│   Highly Optimized Container    │
│  ┌─────────────────────────┐    │
│  │ Event Loop (epoll/kqueue)│   │
│  │ Zero-Copy Operations    │    │
│  │ Lock-Free Data Structures│   │
│  │ Memory Pool Allocation  │    │
│  │ TCP Tuning (SO_REUSEPORT)│  │
│  └─────────────────────────┘    │
│                                 │
│     [Likely Hitting Limits]     │
└─────────────────────────────────┘
```

## 検証項目

### 1. 限界点の特定
- **最大同時接続数**: 実際に維持できる接続数
- **破綻点**: システムが機能しなくなる負荷レベル
- **劣化曲線**: 負荷増加に対する性能劣化の非線形性
- **回復能力**: 過負荷後の正常化時間

### 2. ボトルネック分析
- **CPU飽和点**: コンテキストスイッチングの影響
- **メモリ枯渇**: 接続あたりのメモリ消費
- **I/O限界**: epoll/kqueueの限界
- **カーネル限界**: システムコールのオーバーヘッド

### 3. 失敗モードの理解
- **接続拒否率**: 新規接続の失敗割合
- **タイムアウト率**: 既存接続のタイムアウト
- **レイテンシ爆発**: P99の急激な悪化
- **カスケード障害**: 部分的失敗の連鎖

## TDDアプローチ

### Red Phase (限界を超えるテスト)
```typescript
// extreme-load.test.ts
import { assertEquals, assertExists } from "@std/assert";
import { DistributedLoadGenerator } from "./load-generator.ts";
import { MetricsCollector } from "./metrics-collector.ts";

Deno.test({
  name: "test_extreme_1000_clients_identify_breaking_point",
  sanitizeOps: false,
  sanitizeResources: false,
}, async () => {
  const loadGenerator = new DistributedLoadGenerator({
    targetClients: 1000,
    rampUpTime: 60000, // 1分でランプアップ
    connectionTimeout: 5000,
    requestTimeout: 2000,
  });
  
  const metricsCollector = new MetricsCollector({
    interval: 100,
    detailed: true,
  });

    const results = {
      maxSuccessfulConnections: 0,
      breakingPoint: null,
      performanceMetrics: [],
      errors: []
    };
    
    // 段階的に負荷を増加
    const stages = [
      { clients: 100, duration: 10000 },
      { clients: 250, duration: 10000 },
      { clients: 500, duration: 10000 },
      { clients: 750, duration: 10000 },
      { clients: 1000, duration: 30000 }
    ];
    
    for (const stage of stages) {
      console.log(`Testing with ${stage.clients} clients...`);
      
      const stageResult = await loadGenerator.runStage({
        targetClients: stage.clients,
        duration: stage.duration,
        onError: (error) => {
          results.errors.push({
            stage: stage.clients,
            error: error.message,
            timestamp: Date.now()
          });
        }
      });
      
      results.performanceMetrics.push({
        clients: stage.clients,
        successfulConnections: stageResult.successfulConnections,
        failedConnections: stageResult.failedConnections,
        avgResponseTime: stageResult.avgResponseTime,
        p95ResponseTime: stageResult.p95ResponseTime,
        p99ResponseTime: stageResult.p99ResponseTime,
        errorRate: stageResult.errorRate,
        throughput: stageResult.throughput
      });
      
      // 成功した最大接続数を記録
      if (stageResult.successfulConnections > results.maxSuccessfulConnections) {
        results.maxSuccessfulConnections = stageResult.successfulConnections;
      }
      
      // 破綻点の検出（エラー率50%以上）
      if (stageResult.errorRate > 0.5 && !results.breakingPoint) {
        results.breakingPoint = stage.clients;
        console.log(`Breaking point detected at ${stage.clients} clients`);
      }
      
      // システムが完全に応答しなくなった場合は中断
      if (stageResult.errorRate > 0.9) {
        console.log('System is unresponsive, stopping test');
        break;
      }
    }
    
    // 結果の分析
    assert(results.maxSuccessfulConnections > 500); // 最低500接続は処理できるはず
    assertExists(results.breakingPoint); // 限界点が特定できること
    
    // パフォーマンス劣化の分析
    const degradationAnalysis = analyzeDegradation(results.performanceMetrics);
    assertEquals(degradationAnalysis.isExponential, true); // 指数的な劣化を確認
});

Deno.test("test_resource_exhaustion_patterns", async () => {
    const resourceMonitor = new ResourceMonitor({
      containerId: Deno.env.get("CONTAINER_ID") || "local",
      metrics: ["cpu", "memory", "network", "fileDescriptors"],
    });
    
    // リソース監視を開始
    resourceMonitor.start();
    
    // 1000クライアントまで段階的に増加
    await loadGenerator.rampUp({
      from: 0,
      to: 1000,
      duration: 120000, // 2分
      steps: 20
    });
    
    const resourceData = resourceMonitor.stop();
    
    // リソース枯渇パターンの分析
    const exhaustionPoints = {
      cpu: findExhaustionPoint(resourceData.cpu, 95),
      memory: findExhaustionPoint(resourceData.memory, 90),
      fileDescriptors: findExhaustionPoint(resourceData.fileDescriptors, 95)
    };
    
    // どのリソースが最初にボトルネックになるか
    const firstBottleneck = Object.entries(exhaustionPoints)
      .filter(([_, point]) => point !== null)
      .sort((a, b) => a[1].timestamp - b[1].timestamp)[0];
    
    assertExists(firstBottleneck);
    console.log(`First bottleneck: ${firstBottleneck[0]} at ${firstBottleneck[1].clientCount} clients`);
});

Deno.test("test_recovery_after_overload", async () => {
    // システムを過負荷状態にする
    await loadGenerator.blast({
      clients: 2000, // 意図的に限界を超える
      duration: 30000
    });
    
    // 負荷を通常レベルに戻す
    const recoveryStart = Date.now();
    await loadGenerator.reduce({
      to: 100,
      duration: 5000
    });
    
    // 回復時間の測定
    let recovered = false;
    let recoveryTime = 0;
    
    while (!recovered && Date.now() - recoveryStart < 60000) {
      const health = await checkHealth();
      
      if (health.responseTime < 100 && health.errorRate < 0.01) {
        recovered = true;
        recoveryTime = Date.now() - recoveryStart;
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    assertEquals(recovered, true);
    assert(recoveryTime < 30000); // 30秒以内に回復
});

// ヘルパー関数
function analyzeDegradation(metrics) {
  // レスポンスタイムの増加率を計算
  const responseTimeGrowth = [];
  
  for (let i = 1; i < metrics.length; i++) {
    const prev = metrics[i - 1];
    const curr = metrics[i];
    
    const clientIncrease = curr.clients / prev.clients;
    const responseTimeIncrease = curr.p99ResponseTime / prev.p99ResponseTime;
    
    responseTimeGrowth.push({
      clientIncrease,
      responseTimeIncrease,
      ratio: responseTimeIncrease / clientIncrease
    });
  }
  
  // 比率が1を大きく超える場合は非線形（指数的）な劣化
  const avgRatio = responseTimeGrowth.reduce((sum, g) => sum + g.ratio, 0) / responseTimeGrowth.length;
  
  return {
    isExponential: avgRatio > 1.5,
    avgGrowthRatio: avgRatio,
    details: responseTimeGrowth
  };
}
```

### Green Phase (極限最適化の実装)
```typescript
// server.ts - 極限まで最適化されたサーバー
import { serve } from "@std/http/server";
import { Pool } from "./worker-pool.ts";
import { BufferPool } from "./buffer-pool.ts";

// TCPサーバーの低レベル実装
const listener = Deno.listen({ port: 3000 });
console.log(`Server listening on port 3000`);

// 接続プールとバッファプール
const connectionPool = new Map<string, Connection>();
const bufferPool = new BufferPool(1000, 4096); // 1000個の4KBバッファ

// パフォーマンスカウンター
let requestCount = 0;
let errorCount = 0;

// ワーカープールでの並列処理
const numWorkers = navigator.hardwareConcurrency || 4;
const workerPool = new Pool(numWorkers, "./tcp-worker.ts");

// 接続ハンドラー
async function handleConnection(conn: Deno.Conn) {
  const connectionId = generateConnectionId();
  const buffer = bufferPool.acquire();
  
  const connection: Connection = {
    id: connectionId,
    conn,
    buffer,
    state: "connected",
    lastActivity: Date.now(),
  };
  
  connectionPool.set(connectionId, connection);
  
  try {
    // 接続設定
    // DenoではTCP_NODELAYがデフォルトで有効
    
    const decoder = new TextDecoder();
    const encoder = new TextEncoder();
    
    // リクエスト読み取りループ
    for await (const chunk of conn.readable) {
      const data = decoder.decode(chunk);
      
      // ワーカープールで非同期処理
      queueMicrotask(async () => {
        try {
          const response = await handleRequest(connection, data);
          await conn.write(encoder.encode(response));
          requestCount++;
          
          // バッチでメトリクス更新
          if (requestCount % 100 === 0) {
            await workerPool.run("updateMetrics", {
              requests: 100,
              errors: errorCount,
            });
            errorCount = 0;
          }
        } catch (error) {
          errorCount++;
          console.error("Request handling error:", error);
        }
      });
      
      connection.lastActivity = Date.now();
    }
  } catch (error) {
    errorCount++;
    console.error("Connection error:", error);
  } finally {
    connectionPool.delete(connectionId);
    bufferPool.release(buffer);
    try {
      conn.close();
    } catch {}
  }
}

// HTTPプロトコルの最小実装
async function handleRequest(connection: Connection, data: string): Promise<string> {
  // シンプルなHTTPレスポンス（パース処理を最小化）
  if (data.indexOf("GET /api/health") === 0) {
    return "HTTP/1.1 200 OK\r\n" +
           "Content-Type: application/json\r\n" +
           "Content-Length: 15\r\n" +
           "Connection: keep-alive\r\n" +
           "\r\n" +
           '{"status":"ok"}';
  } else if (data.indexOf("GET /api/data") === 0) {
    // より複雑なレスポンス
    const jsonData = JSON.stringify({
      id: connection.id,
      timestamp: Date.now(),
      worker: Deno.pid,
    });
    
    return `HTTP/1.1 200 OK\r\n` +
           `Content-Type: application/json\r\n` +
           `Content-Length: ${jsonData.length}\r\n` +
           `Connection: keep-alive\r\n` +
           `\r\n` +
           jsonData;
  }
  
  return "HTTP/1.1 404 Not Found\r\n" +
         "Content-Length: 0\r\n" +
         "\r\n";
}

// 定期的なクリーンアップ
setInterval(() => {
  const now = Date.now();
  const timeout = 60000; // 1分
  
  for (const [id, connection] of connectionPool) {
    if (now - connection.lastActivity > timeout) {
      try {
        connection.conn.close();
      } catch {}
      connectionPool.delete(id);
    }
  }
}, 10000); // 10秒ごと

// メインループ
for await (const conn of listener) {
  // 非同期で接続を処理
  handleConnection(conn).catch(console.error);
}

// グレースフルシャットダウン
Deno.addSignalListener("SIGTERM", () => {
  listener.close();
  connectionPool.forEach((conn) => {
    try {
      conn.conn.close();
    } catch {}
  });
  workerPool.terminate();
  Deno.exit(0);
});

// バッファプール実装
export class BufferPool {
  private buffers: Uint8Array[] = [];
  
  constructor(private size: number, private bufferSize: number) {
    // 事前割り当て
    for (let i = 0; i < size; i++) {
      this.buffers.push(new Uint8Array(bufferSize));
    }
  }
  
  acquire(): Uint8Array {
    return this.buffers.pop() || new Uint8Array(this.bufferSize);
  }
  
  release(buffer: Uint8Array): void {
    if (this.buffers.length < 1000) {
      buffer.fill(0); // セキュリティのためクリア
      this.buffers.push(buffer);
    }
  }
}

// 接続情報の型
interface Connection {
  id: string;
  conn: Deno.Conn;
  buffer: Uint8Array;
  state: string;
  lastActivity: number;
}

// 高速ID生成
let idCounter = 0;
function generateConnectionId(): string {
  return `${Deno.pid}-${Date.now()}-${++idCounter}`;
}
```

### システムチューニング
```bash
#!/bin/bash
# system-tuning.sh

# カーネルパラメータの最適化
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w net.core.netdev_max_backlog=65535

# ファイルディスクリプタ
ulimit -n 1048576

# TCPチューニング
sysctl -w net.ipv4.tcp_fin_timeout=15
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_keepalive_time=300
sysctl -w net.ipv4.tcp_keepalive_probes=5
sysctl -w net.ipv4.tcp_keepalive_intvl=15

# メモリチューニング
sysctl -w vm.swappiness=10
sysctl -w vm.dirty_ratio=15
sysctl -w vm.dirty_background_ratio=5
```

## 実装手順

### 1. 最適化されたDockerfile
```dockerfile
# Dockerfile
FROM denoland/deno:alpine-2.0.0 AS builder

WORKDIR /app
COPY deno.json deno.lock ./
RUN deno cache --lock=deno.lock deno.json

COPY . .
RUN deno cache server.ts

FROM denoland/deno:alpine-2.0.0

# 最小限のランタイム
RUN apk add --no-cache tini

WORKDIR /app
COPY --from=builder /app .

# セキュリティ設定
RUN addgroup -g 1001 -S deno && \
    adduser -S deno -u 1001

USER deno

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["deno", "run", "--allow-net", "--allow-env", "--allow-read", "--allow-write", "--v8-flags=--max-old-space-size=2048,--max-semi-space-size=128", "server.ts"]
```

### 2. Docker Compose with システムチューニング
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000-3015:3000-3015"
    environment:
      DENO_DIR: /app/.deno
      RUST_BACKTRACE: 1
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G
    ulimits:
      nofile:
        soft: 1048576
        hard: 1048576
      nproc:
        soft: 65535
        hard: 65535
    sysctls:
      - net.core.somaxconn=65535
      - net.ipv4.tcp_max_syn_backlog=65535
      - net.core.netdev_max_backlog=65535
      - net.ipv4.tcp_fin_timeout=15
      - net.ipv4.tcp_tw_reuse=1
    cap_add:
      - NET_ADMIN
    volumes:
      - deno-cache:/app/.deno

volumes:
  deno-cache:
```

## パフォーマンス分析

### 予想される限界点
```
接続数:
- 500: 安定動作
- 750: 性能劣化開始
- 1000: 深刻な劣化
- 1200+: システム不安定

ボトルネック:
1. コンテキストスイッチング
2. メモリ帯域幅
3. カーネルのスケジューリング
4. TCPバッファの枯渇
```

### メトリクス収集
```typescript
// metrics-collector.ts
export class MetricsCollector {
  private metrics = {
    connections: new Map<string, any>(),
    performance: [] as any[],
    resources: [] as any[],
    eventLoopLag: 0,
  };
  
  collectSystemMetrics() {
    const memoryUsage = Deno.memoryUsage();
    
    return {
      timestamp: Date.now(),
      memory: {
        rss: memoryUsage.rss,
        heapTotal: memoryUsage.heapTotal,
        heapUsed: memoryUsage.heapUsed,
        external: memoryUsage.external,
      },
      connections: this.metrics.connections.size,
      eventLoop: this.measureEventLoopLag(),
    };
  }
  
  measureEventLoopLag(): number {
    const start = performance.now();
    
    queueMicrotask(() => {
      const lag = performance.now() - start;
      this.metrics.eventLoopLag = lag;
    });
    
    return this.metrics.eventLoopLag || 0;
  }
}
```

## 失敗の分析

### 典型的な失敗パターン
1. **TCPバックログオーバーフロー**
   - SYN_RECEIVEDステートの接続が蓄積
   - 新規接続の拒否

2. **メモリ断片化**
   - 長時間運用でのメモリ効率低下
   - GCの頻発

3. **イベントループの飽和**
   - 処理遅延の累積
   - タイムアウトの連鎖

## 次のステップ

この限界を突破するため、`04_single_container_failure_point`で詳細な失敗分析を行い、その後の水平スケーリング（Phase 2）への移行を正当化します。

## 学んだこと

- 単一コンテナには物理的限界がある
- 最適化にも限界があり、アーキテクチャ変更が必要
- C10K問題は解決されたが、スケールには依然として課題
- 監視とメトリクスが限界を理解する鍵

## 参考資料

- [The C10K Problem](http://www.kegel.com/c10k.html)
- [Linux Kernel Tuning for C500K](https://www.kernel.org/doc/Documentation/networking/scaling.txt)
- [High Performance Browser Networking](https://hpbn.co/)
- [Deno Runtime API](https://docs.deno.com/runtime/manual)