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
```javascript
// test/scale-100.test.js
describe('Single Container - 100 Clients Scale Test', () => {
  let metricsCollector;
  
  beforeAll(() => {
    metricsCollector = new MetricsCollector();
  });

  it('should handle 100 concurrent connections efficiently', async () => {
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

  it('should not degrade performance over time', async () => {
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

  it('should efficiently use resources', async () => {
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
});
```

### Green Phase (最適化された実装)
```javascript
// server.js
const cluster = require('cluster');
const os = require('os');
const express = require('express');

if (cluster.isMaster) {
  // CPUコア数に基づいてワーカーを起動
  const numCPUs = os.cpus().length;
  const numWorkers = Math.min(numCPUs, 4); // 最大4ワーカー
  
  console.log(`Master ${process.pid} is running`);
  console.log(`Forking ${numWorkers} workers...`);
  
  // ワーカーの起動
  for (let i = 0; i < numWorkers; i++) {
    cluster.fork();
  }
  
  // ワーカーの監視と再起動
  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died`);
    console.log('Starting a new worker...');
    cluster.fork();
  });
  
  // グレースフルシャットダウン
  process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully...');
    for (const id in cluster.workers) {
      cluster.workers[id].kill();
    }
  });
} else {
  // ワーカープロセス
  const app = express();
  
  // 最適化されたミドルウェア
  app.use(express.json({ limit: '1mb' }));
  
  // コネクションプールの設定
  const http = require('http');
  const server = http.createServer(app);
  server.keepAliveTimeout = 65000;
  server.headersTimeout = 66000;
  
  // リクエストキューの管理
  let activeRequests = 0;
  const MAX_CONCURRENT_REQUESTS = 50;
  
  app.use((req, res, next) => {
    if (activeRequests >= MAX_CONCURRENT_REQUESTS) {
      res.status(503).json({
        error: 'Server too busy',
        retry_after: 1
      });
      return;
    }
    
    activeRequests++;
    res.on('finish', () => {
      activeRequests--;
    });
    
    next();
  });
  
  // データキャッシュ（簡易実装）
  const cache = new Map();
  const CACHE_TTL = 60000; // 1分
  
  // APIエンドポイント
  app.get('/api/data/:clientId', async (req, res) => {
    const { clientId } = req.params;
    const cacheKey = `data:${clientId}`;
    
    // キャッシュチェック
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return res.json(cached.data);
    }
    
    // データ生成（実際の処理をシミュレート）
    const data = {
      clientId,
      timestamp: Date.now(),
      workerId: process.pid,
      data: generateData(clientId)
    };
    
    // キャッシュに保存
    cache.set(cacheKey, {
      data,
      timestamp: Date.now()
    });
    
    // キャッシュサイズ制限
    if (cache.size > 1000) {
      const oldestKey = cache.keys().next().value;
      cache.delete(oldestKey);
    }
    
    res.json(data);
  });
  
  // ヘルスチェック（軽量）
  app.get('/api/health', (req, res) => {
    res.status(200).json({
      status: 'healthy',
      worker: process.pid,
      activeRequests,
      cacheSize: cache.size
    });
  });
  
  // メトリクスエンドポイント
  app.get('/api/metrics', (req, res) => {
    const usage = process.memoryUsage();
    res.json({
      process: {
        pid: process.pid,
        uptime: process.uptime(),
        activeRequests
      },
      memory: {
        rss: usage.rss,
        heapTotal: usage.heapTotal,
        heapUsed: usage.heapUsed,
        external: usage.external
      },
      cache: {
        size: cache.size,
        hitRate: calculateCacheHitRate()
      }
    });
  });
  
  const PORT = process.env.PORT || 3000;
  server.listen(PORT, () => {
    console.log(`Worker ${process.pid} started on port ${PORT}`);
  });
}

// ヘルパー関数
function generateData(clientId) {
  // 実際のビジネスロジックをシミュレート
  return {
    id: clientId,
    value: Math.random() * 1000,
    items: Array(10).fill(0).map((_, i) => ({
      index: i,
      data: `Item ${i} for client ${clientId}`
    }))
  };
}

let cacheHits = 0;
let cacheMisses = 0;

function calculateCacheHitRate() {
  const total = cacheHits + cacheMisses;
  return total > 0 ? cacheHits / total : 0;
}
```

### Refactor Phase (さらなる最適化)
```javascript
// optimizations.js

// 1. 非同期処理の最適化
const pLimit = require('p-limit');
const limit = pLimit(10); // 同時実行数を制限

// 2. メモリプールの実装
class ObjectPool {
  constructor(factory, reset, maxSize = 100) {
    this.factory = factory;
    this.reset = reset;
    this.pool = [];
    this.maxSize = maxSize;
  }
  
  acquire() {
    return this.pool.pop() || this.factory();
  }
  
  release(obj) {
    if (this.pool.length < this.maxSize) {
      this.reset(obj);
      this.pool.push(obj);
    }
  }
}

// 3. バッチ処理の実装
class BatchProcessor {
  constructor(processFn, batchSize = 10, flushInterval = 100) {
    this.processFn = processFn;
    this.batchSize = batchSize;
    this.flushInterval = flushInterval;
    this.batch = [];
    this.timer = null;
  }
  
  add(item) {
    this.batch.push(item);
    
    if (this.batch.length >= this.batchSize) {
      this.flush();
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), this.flushInterval);
    }
  }
  
  flush() {
    if (this.batch.length === 0) return;
    
    const items = this.batch.splice(0);
    this.processFn(items);
    
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }
}
```

## 実装手順

### 1. Docker設定の最適化
```dockerfile
# Dockerfile
FROM node:20-alpine

# システムの最適化
RUN apk add --no-cache tini

WORKDIR /app

# マルチステージビルド
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY . .

# Node.js最適化フラグ
ENV NODE_ENV=production
ENV UV_THREADPOOL_SIZE=8

EXPOSE 3000

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "--max-old-space-size=768", "server.js"]
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
```javascript
// k6-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // ウォームアップ
    { duration: '1m', target: 100 },   // 100クライアントまで増加
    { duration: '3m', target: 100 },   // 100クライアントを維持
    { duration: '30s', target: 0 },    // クールダウン
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    errors: ['rate<0.001'], // 0.1%未満のエラー率
  },
};

export default function () {
  const clientId = `client-${__VU}`;
  const res = http.get(`http://localhost:3000/api/data/${clientId}`);
  
  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  errorRate.add(!success);
  
  sleep(0.1); // 100ms間隔
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
npm test

# 4. k6による負荷テスト
k6 run k6-load-test.js

# 5. リアルタイムモニタリング
docker stats
watch -n 1 'curl -s http://localhost:3000/api/metrics | jq'

# 6. ログ確認
docker-compose logs -f
```

## パフォーマンスチューニング

### 1. Node.js最適化
```bash
# V8オプション
--max-old-space-size=768  # ヒープサイズ制限
--optimize-for-size       # メモリ最適化
--gc-interval=100        # GC頻度調整
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
- クラスタリングによる並列処理
- キャッシング戦略
- コネクションプーリング
- 非同期バッチ処理

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
```javascript
// ヒープダンプ取得
process.on('SIGUSR2', () => {
  const heapdump = require('heapdump');
  heapdump.writeSnapshot(`heap-${Date.now()}.heapsnapshot`);
});
```

### 問題: CPU使用率が高い
```bash
# プロファイリング実行
node --prof server.js
node --prof-process isolate-*.log > profile.txt
```

## 次のステップ

100クライアントでの安定動作を確認後、`03_single_container_1000_clients`で10倍の1000クライアントに挑戦し、単一コンテナの限界を探ります。

## 学んだこと

- 単純な10倍スケールは線形ではない
- リソース管理とキャッシングが重要
- クラスタリングで効率的な並列処理
- 適切な監視とメトリクスが必須

## 参考資料

- [Node.js Cluster Documentation](https://nodejs.org/api/cluster.html)
- [High Performance Node.js](https://nodejs.org/en/docs/guides/simple-profiling/)
- [k6 Load Testing Guide](https://k6.io/docs/)
- [Docker Resource Management](https://docs.docker.com/config/containers/resource_constraints/)