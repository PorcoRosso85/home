# 01_single_container_10_clients

## 概要

単一コンテナで10クライアントの同時接続を処理する基本構成。システムの基礎的な性能特性を把握し、後続のスケーリング検証の基準値を確立します。

## 目的

- ベースライン性能の測定
- 基本的なメトリクス収集の仕組み構築
- TDDサイクルの確立
- 単一コンテナの効率的な動作確認

## アーキテクチャ

```
┌─────────────────────────────────┐
│         Load Generator          │
│      (10 Concurrent Clients)    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│      Application Container      │
│         (Node.js/Go/Rust)       │
│          Port: 3000             │
│  ┌─────────────────────────┐    │
│  │    HTTP Server          │    │
│  │    Connection Pool      │    │
│  │    Request Handler      │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

## 検証項目

### 1. 基本性能指標
- **レスポンスタイム**: P50, P95, P99 < 100ms
- **スループット**: 最低100 req/s
- **エラー率**: 0%
- **同時接続数**: 10を安定して維持

### 2. リソース使用状況
- **CPU使用率**: < 20%
- **メモリ使用量**: < 500MB
- **ファイルディスクリプタ**: < 100
- **ネットワーク帯域**: < 1Mbps

### 3. 安定性指標
- **連続稼働時間**: 最低1時間エラーなし
- **メモリリーク**: なし
- **レスポンスタイムの分散**: 標準偏差 < 10ms

## TDDアプローチ

### Red Phase (失敗するテストを書く)
```javascript
// test/baseline.test.js
describe('Single Container - 10 Clients Baseline', () => {
  it('should handle 10 concurrent connections', async () => {
    const clients = Array(10).fill(0).map((_, i) => ({
      id: `client-${i}`,
      startTime: Date.now()
    }));
    
    const results = await Promise.all(
      clients.map(client => 
        fetch('http://localhost:3000/api/health')
          .then(res => ({
            ...client,
            status: res.status,
            duration: Date.now() - client.startTime
          }))
      )
    );
    
    // すべて成功すること
    expect(results.every(r => r.status === 200)).toBe(true);
    
    // レスポンスタイムが100ms以内
    expect(results.every(r => r.duration < 100)).toBe(true);
  });

  it('should maintain consistent performance', async () => {
    const measurements = [];
    
    // 100回連続でリクエスト
    for (let i = 0; i < 100; i++) {
      const start = Date.now();
      const res = await fetch('http://localhost:3000/api/health');
      const duration = Date.now() - start;
      
      measurements.push({
        iteration: i,
        status: res.status,
        duration
      });
      
      // 10ms待機（負荷を現実的に）
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    // 標準偏差を計算
    const durations = measurements.map(m => m.duration);
    const mean = durations.reduce((a, b) => a + b) / durations.length;
    const variance = durations.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / durations.length;
    const stdDev = Math.sqrt(variance);
    
    expect(stdDev).toBeLessThan(10);
  });

  it('should not leak memory', async () => {
    const initialMemory = await getContainerMemoryUsage();
    
    // 1000回リクエスト
    for (let i = 0; i < 1000; i++) {
      await fetch('http://localhost:3000/api/health');
    }
    
    // GCを待つ
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const finalMemory = await getContainerMemoryUsage();
    const memoryIncrease = finalMemory - initialMemory;
    
    // メモリ増加が10MB以内
    expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
  });
});
```

### Green Phase (テストを通す実装)
```javascript
// server.js
const express = require('express');
const app = express();

// メトリクス収集
const metrics = {
  requestCount: 0,
  errorCount: 0,
  responseTimes: []
};

// ミドルウェア：レスポンスタイム計測
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    metrics.responseTimes.push(duration);
    metrics.requestCount++;
    
    // 最新1000件のみ保持（メモリリーク防止）
    if (metrics.responseTimes.length > 1000) {
      metrics.responseTimes.shift();
    }
  });
  
  next();
});

// ヘルスチェックエンドポイント
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// メトリクスエンドポイント
app.get('/api/metrics', (req, res) => {
  const responseTimes = [...metrics.responseTimes];
  const sorted = responseTimes.sort((a, b) => a - b);
  
  res.json({
    requestCount: metrics.requestCount,
    errorCount: metrics.errorCount,
    responseTime: {
      p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
      p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
      p99: sorted[Math.floor(sorted.length * 0.99)] || 0,
      mean: sorted.reduce((a, b) => a + b, 0) / sorted.length || 0
    },
    memory: {
      rss: process.memoryUsage().rss,
      heapTotal: process.memoryUsage().heapTotal,
      heapUsed: process.memoryUsage().heapUsed
    }
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### Refactor Phase (最適化)
- コネクションプーリングの調整
- Keep-Aliveの有効化
- 圧縮の追加（必要に応じて）

## データベース統合パターン

### DB接続プール管理
```javascript
// db-pool.js
const { Pool } = require('pg');

const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'testdb',
  user: 'user',
  password: 'password',
  max: 10, // 10クライアント用の適切なプールサイズ
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// エラーハンドリング
pool.on('error', (err, client) => {
  console.error('Unexpected error on idle client', err);
  process.exit(-1);
});

module.exports = pool;
```

### トランザクション一貫性パターン
```javascript
// transaction-handler.js
async function handleTransaction(operation) {
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');
    const result = await operation(client);
    await client.query('COMMIT');
    return result;
  } catch (e) {
    await client.query('ROLLBACK');
    throw e;
  } finally {
    client.release();
  }
}

// 使用例
app.post('/api/transfer', async (req, res) => {
  try {
    const result = await handleTransaction(async (client) => {
      // 複数のDB操作をトランザクション内で実行
      await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, fromId]);
      await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, toId]);
      return { success: true };
    });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

## 実装手順

### 1. 環境構築
```bash
# Nix開発環境に入る
nix develop

# 依存関係のインストール
npm init -y
npm install express
npm install -D jest node-fetch @types/jest
```

### 2. Dockerイメージの作成
```dockerfile
# Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

### 3. Docker Composeの設定
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
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
      reservations:
        cpus: '0.25'
        memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 4. 負荷テストスクリプト
```javascript
// load-test.js
const http = require('http');

const agent = new http.Agent({
  keepAlive: true,
  maxSockets: 10
});

async function runLoadTest() {
  const clients = Array(10).fill(0).map((_, i) => i);
  const duration = 60000; // 1分間
  const startTime = Date.now();
  
  const results = {
    requests: 0,
    errors: 0,
    responseTimes: []
  };
  
  await Promise.all(clients.map(async (clientId) => {
    while (Date.now() - startTime < duration) {
      const reqStart = Date.now();
      
      try {
        await makeRequest();
        results.requests++;
        results.responseTimes.push(Date.now() - reqStart);
      } catch (error) {
        results.errors++;
      }
      
      // 各クライアント100ms間隔でリクエスト
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }));
  
  return results;
}

function makeRequest() {
  return new Promise((resolve, reject) => {
    const req = http.get({
      hostname: 'localhost',
      port: 3000,
      path: '/api/health',
      agent: agent
    }, (res) => {
      res.on('data', () => {});
      res.on('end', resolve);
    });
    
    req.on('error', reject);
    req.setTimeout(1000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
  });
}
```

## 実行方法

```bash
# 1. テスト実行（Red）
npm test

# 2. アプリケーション起動
docker-compose up -d

# 3. テスト再実行（Green）
npm test

# 4. 負荷テスト実行
node load-test.js

# 5. メトリクス確認
curl http://localhost:3000/api/metrics | jq
```

## 成功基準

- [ ] すべてのテストがグリーン
- [ ] 1時間の連続稼働でエラーなし
- [ ] メモリ使用量が安定（500MB以下）
- [ ] P99レスポンスタイム < 100ms
- [ ] CPU使用率 < 20%

## 次のステップ

このPOCで確立したベースラインを基に、次の`02_single_container_100_clients`では10倍の負荷での動作を検証します。

## トラブルシューティング

### 問題: レスポンスタイムが遅い
- Node.jsのイベントループをブロックしていないか確認
- `--inspect`フラグでプロファイリング実行

### 問題: メモリ使用量が増加
- `process.memoryUsage()`で詳細確認
- ヒープダンプを取得して分析

### 問題: 接続エラー
- ulimitの設定確認
- Keep-Aliveの設定確認

## 参考資料

- [Node.js Performance Best Practices](https://nodejs.org/en/docs/guides/simple-profiling/)
- [Docker Resource Constraints](https://docs.docker.com/config/containers/resource_constraints/)
- [Express.js Production Best Practices](https://expressjs.com/en/advanced/best-practice-performance.html)