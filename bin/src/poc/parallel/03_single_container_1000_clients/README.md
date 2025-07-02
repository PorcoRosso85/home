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
```javascript
// test/extreme-load.test.js
describe('Single Container - 1000 Clients Extreme Load', () => {
  let loadGenerator;
  let metricsCollector;
  
  beforeAll(() => {
    loadGenerator = new DistributedLoadGenerator({
      targetClients: 1000,
      rampUpTime: 60000, // 1分でランプアップ
      connectionTimeout: 5000,
      requestTimeout: 2000
    });
    
    metricsCollector = new MetricsCollector({
      interval: 100,
      detailed: true
    });
  });

  it('should identify breaking point with 1000 clients', async () => {
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
    expect(results.maxSuccessfulConnections).toBeGreaterThan(500); // 最低500接続は処理できるはず
    expect(results.breakingPoint).toBeDefined(); // 限界点が特定できること
    
    // パフォーマンス劣化の分析
    const degradationAnalysis = analyzeDegradation(results.performanceMetrics);
    expect(degradationAnalysis.isExponential).toBe(true); // 指数的な劣化を確認
  });

  it('should measure resource exhaustion patterns', async () => {
    const resourceMonitor = new ResourceMonitor({
      containerId: process.env.CONTAINER_ID,
      metrics: ['cpu', 'memory', 'network', 'fileDescriptors']
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
    
    expect(firstBottleneck).toBeDefined();
    console.log(`First bottleneck: ${firstBottleneck[0]} at ${firstBottleneck[1].clientCount} clients`);
  });

  it('should test recovery after overload', async () => {
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
    
    expect(recovered).toBe(true);
    expect(recoveryTime).toBeLessThan(30000); // 30秒以内に回復
  });
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
```javascript
// server.js - 極限まで最適化されたサーバー
const cluster = require('cluster');
const os = require('os');
const net = require('net');

if (cluster.isMaster) {
  // 全CPUコアを使用
  const numCPUs = os.cpus().length;
  
  console.log(`Master ${process.pid} starting ${numCPUs} workers...`);
  
  // SO_REUSEPORTを有効にしてワーカーを起動
  for (let i = 0; i < numCPUs; i++) {
    const worker = cluster.fork();
    worker.on('message', (msg) => {
      if (msg.cmd === 'notifyRequest') {
        // グローバルメトリクスの更新
        updateMetrics(msg.data);
      }
    });
  }
  
  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died, restarting...`);
    cluster.fork();
  });
} else {
  // ワーカープロセス - 低レベル最適化
  const server = net.createServer({
    pauseOnConnect: false, // 接続時の一時停止を無効化
    noDelay: true // Nagleアルゴリズムを無効化
  });
  
  // 接続プールとバッファプール
  const connectionPool = new Map();
  const bufferPool = new BufferPool(1000, 4096); // 1000個の4KBバッファ
  
  // パフォーマンスカウンター
  let requestCount = 0;
  let errorCount = 0;
  
  server.on('connection', (socket) => {
    // ソケット最適化
    socket.setNoDelay(true);
    socket.setKeepAlive(true, 60000);
    
    // タイムアウト設定
    socket.setTimeout(30000);
    
    // 接続管理
    const connectionId = generateConnectionId();
    const connection = {
      id: connectionId,
      socket: socket,
      buffer: bufferPool.acquire(),
      state: 'connected',
      lastActivity: Date.now()
    };
    
    connectionPool.set(connectionId, connection);
    
    // 非同期でリクエスト処理
    socket.on('data', (data) => {
      setImmediate(() => {
        try {
          handleRequest(connection, data);
        } catch (error) {
          errorCount++;
          socket.destroy();
        }
      });
    });
    
    socket.on('close', () => {
      connectionPool.delete(connectionId);
      bufferPool.release(connection.buffer);
    });
    
    socket.on('error', (err) => {
      errorCount++;
      connectionPool.delete(connectionId);
    });
    
    socket.on('timeout', () => {
      socket.destroy();
    });
  });
  
  // HTTPプロトコルの最小実装
  function handleRequest(connection, data) {
    const { buffer, socket } = connection;
    
    // シンプルなHTTPレスポンス（パース処理を最小化）
    if (data.indexOf('GET /api/health') === 0) {
      const response = 'HTTP/1.1 200 OK\r\n' +
                      'Content-Type: application/json\r\n' +
                      'Content-Length: 15\r\n' +
                      'Connection: keep-alive\r\n' +
                      '\r\n' +
                      '{"status":"ok"}';
      
      socket.write(response);
      requestCount++;
      
      // バッチでマスターに通知（オーバーヘッド削減）
      if (requestCount % 100 === 0) {
        process.send({
          cmd: 'notifyRequest',
          data: {
            requests: 100,
            errors: errorCount
          }
        });
        errorCount = 0;
      }
    } else if (data.indexOf('GET /api/data') === 0) {
      // より複雑なレスポンス
      const jsonData = JSON.stringify({
        id: connection.id,
        timestamp: Date.now(),
        worker: process.pid
      });
      
      const response = `HTTP/1.1 200 OK\r\n` +
                      `Content-Type: application/json\r\n` +
                      `Content-Length: ${jsonData.length}\r\n` +
                      `Connection: keep-alive\r\n` +
                      `\r\n` +
                      jsonData;
      
      socket.write(response);
      requestCount++;
    }
    
    connection.lastActivity = Date.now();
  }
  
  // 定期的なクリーンアップ
  setInterval(() => {
    const now = Date.now();
    const timeout = 60000; // 1分
    
    for (const [id, connection] of connectionPool) {
      if (now - connection.lastActivity > timeout) {
        connection.socket.destroy();
        connectionPool.delete(id);
      }
    }
  }, 10000); // 10秒ごと
  
  // サーバー起動
  const PORT = 3000 + cluster.worker.id - 1;
  server.listen(PORT, () => {
    console.log(`Worker ${process.pid} listening on port ${PORT}`);
  });
  
  // グレースフルシャットダウン
  process.on('SIGTERM', () => {
    server.close(() => {
      connectionPool.forEach(conn => conn.socket.destroy());
      process.exit(0);
    });
  });
}

// バッファプール実装
class BufferPool {
  constructor(size, bufferSize) {
    this.buffers = [];
    this.bufferSize = bufferSize;
    
    // 事前割り当て
    for (let i = 0; i < size; i++) {
      this.buffers.push(Buffer.allocUnsafe(bufferSize));
    }
  }
  
  acquire() {
    return this.buffers.pop() || Buffer.allocUnsafe(this.bufferSize);
  }
  
  release(buffer) {
    if (this.buffers.length < 1000) {
      buffer.fill(0); // セキュリティのためクリア
      this.buffers.push(buffer);
    }
  }
}

// 高速ID生成
let idCounter = 0;
function generateConnectionId() {
  return `${process.pid}-${Date.now()}-${++idCounter}`;
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
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM alpine:3.18

# 最小限のランタイム
RUN apk add --no-cache nodejs tini

WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .

# セキュリティ設定
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

EXPOSE 3000-3015

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "--max-old-space-size=2048", "--max-semi-space-size=128", "server.js"]
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
      NODE_ENV: production
      UV_THREADPOOL_SIZE: 128
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
```javascript
// metrics-collector.js
class MetricsCollector {
  constructor() {
    this.metrics = {
      connections: new Map(),
      performance: [],
      resources: []
    };
  }
  
  collectSystemMetrics() {
    const usage = process.memoryUsage();
    const cpuUsage = process.cpuUsage();
    
    return {
      timestamp: Date.now(),
      memory: {
        rss: usage.rss,
        heapTotal: usage.heapTotal,
        heapUsed: usage.heapUsed,
        external: usage.external,
        arrayBuffers: usage.arrayBuffers
      },
      cpu: {
        user: cpuUsage.user,
        system: cpuUsage.system
      },
      connections: this.metrics.connections.size,
      eventLoop: this.measureEventLoopLag()
    };
  }
  
  measureEventLoopLag() {
    const start = process.hrtime.bigint();
    
    setImmediate(() => {
      const lag = Number(process.hrtime.bigint() - start) / 1e6;
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
- [Node.js Under The Hood](https://nodejs.org/en/docs/guides/)