# 18_cache_layer_multi_server

## 概要

マルチサーバー環境でのキャッシュレイヤー実装。分散キャッシュの一貫性、キャッシュ無効化の伝播、そしてスプリットブレイン問題への対処法を実践的に学びます。

## 目的

- 分散キャッシュアーキテクチャの構築
- キャッシュ無効化戦略の実装
- レプリケーション遅延の影響測定
- 分散環境特有の問題解決

## アーキテクチャ

```
┌─────────────────────────────────────┐
│           Clients (N)               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│        Load Balancer                │
└──┬──────┬──────┬──────┬────────────┘
   │      │      │      │
   ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐┌──────┐
│Server││Server││Server││Server│
│  1   ││  2   ││  3   ││  4   │
│Local ││Local ││Local ││Local │
│Cache ││Cache ││Cache ││Cache │
└──┬───┘└──┬───┘└──┬───┘└──┬───┘
   │       │       │       │
   └───────┴───┬───┴───────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌──────────┐      ┌──────────┐
│  Redis   │      │PostgreSQL│
│ Cluster  │      │  Primary │
│(Sharded) │      │    +     │
│          │      │ Replicas │
└──────────┘      └──────────┘
      │                 
      ▼                 
┌──────────────────────┐
│   Message Bus       │
│ (Invalidation Events)│
└──────────────────────┘
```

## 分散キャッシュの課題

### 1. キャッシュ無効化の遅延
```javascript
// Server 1がデータを更新
async function updateOnServer1(key, value) {
  // 1. DB更新
  await db.update(key, value);
  
  // 2. ローカルキャッシュ更新
  await localCache.set(key, value);
  
  // 3. 無効化イベント発行
  await messageBus.publish('cache.invalidate', { key });
  
  // 問題: 他のサーバーへの伝播に時間がかかる
}

// Server 2-4での無効化受信
messageBus.subscribe('cache.invalidate', async (event) => {
  // 遅延して無効化される
  await localCache.delete(event.key);
});
```

### 2. スプリットブレイン問題
```javascript
// ネットワーク分断時の問題
async function handleNetworkPartition() {
  // Partition A: Server 1,2
  // Partition B: Server 3,4
  
  // 両方のパーティションで異なる更新
  // Partition A
  await updateInPartitionA('user:1', { balance: 1000 });
  
  // Partition B（同時）
  await updateInPartitionB('user:1', { balance: 2000 });
  
  // ネットワーク復旧後の不整合
  // どちらの値が正しい？
}
```

## TDDアプローチ

### Red Phase (分散環境の問題を検証)
```javascript
describe('Distributed Cache Challenges', () => {
  it('should demonstrate cache invalidation delay', async () => {
    const servers = await setupServers(4);
    
    // Server 1でデータ更新
    await servers[0].update('product:1', { price: 100 });
    
    // 即座に他のサーバーから読み取り
    const immediateReads = await Promise.all([
      servers[1].read('product:1'),
      servers[2].read('product:1'),
      servers[3].read('product:1')
    ]);
    
    // 古いデータが返される可能性
    const inconsistentReads = immediateReads.filter(
      data => data.price !== 100
    );
    expect(inconsistentReads.length).toBeGreaterThan(0);
    
    // 1秒待機後
    await delay(1000);
    
    const delayedReads = await Promise.all([
      servers[1].read('product:1'),
      servers[2].read('product:1'),
      servers[3].read('product:1')
    ]);
    
    // 全て一致するはず
    expect(delayedReads.every(data => data.price === 100)).toBe(true);
  });

  it('should handle thundering herd problem', async () => {
    const servers = await setupServers(4);
    
    // 全サーバーのキャッシュを無効化
    await invalidateAllCaches('popular:item');
    
    // 1000クライアントが同時にアクセス
    const clients = Array(1000).fill(0).map((_, i) => ({
      id: i,
      server: servers[i % 4]
    }));
    
    const dbQueryCount = await monitorDBQueries(async () => {
      await Promise.all(
        clients.map(c => c.server.read('popular:item'))
      );
    });
    
    // 理想は1回、実際は複数回DBアクセスが発生
    expect(dbQueryCount).toBeGreaterThan(1);
    expect(dbQueryCount).toBeLessThan(100); // でも制御されている
  });

  it('should demonstrate cache stampede protection', async () => {
    // Distributed lock を使った保護
    const cache = new DistributedCache({
      lockTimeout: 5000,
      lockRetry: 100
    });
    
    // 複数サーバーから同時に同じキーを要求
    const results = await Promise.all(
      Array(10).fill(0).map(() => 
        cache.getWithLock('expensive:calculation', async () => {
          // 高コストな計算
          await delay(1000);
          return Math.random();
        })
      )
    );
    
    // 全て同じ値（1回だけ計算された）
    expect(new Set(results).size).toBe(1);
  });
});
```

## 実装パターン

### 1. 分散キャッシュ with Redis Cluster
```javascript
class DistributedCacheManager {
  constructor() {
    this.redis = new Redis.Cluster([
      { port: 7000, host: '127.0.0.1' },
      { port: 7001, host: '127.0.0.1' },
      { port: 7002, host: '127.0.0.1' }
    ]);
    
    this.localCache = new NodeCache({ stdTTL: 60 });
    this.messageBus = new EventEmitter();
  }
  
  async get(key) {
    // 1. ローカルキャッシュ確認
    let value = this.localCache.get(key);
    if (value) return value;
    
    // 2. 分散キャッシュ確認
    value = await this.redis.get(key);
    if (value) {
      this.localCache.set(key, value);
      return JSON.parse(value);
    }
    
    // 3. DB読み取り（分散ロック付き）
    return await this.getWithLock(key);
  }
  
  async getWithLock(key) {
    const lockKey = `lock:${key}`;
    const lockValue = uuid();
    
    // 分散ロック取得
    const acquired = await this.redis.set(
      lockKey, 
      lockValue, 
      'PX', 5000, 
      'NX'
    );
    
    if (!acquired) {
      // 他のサーバーが処理中 - 待機
      await this.waitForValue(key);
      return await this.get(key);
    }
    
    try {
      // DBから読み取り
      const value = await db.query(
        'SELECT * FROM data WHERE key = $1', 
        [key]
      );
      
      // キャッシュに保存
      await this.set(key, value.rows[0]);
      
      return value.rows[0];
    } finally {
      // ロック解放
      await this.releaseLock(lockKey, lockValue);
    }
  }
  
  async set(key, value) {
    // 1. 分散キャッシュに保存
    await this.redis.setex(
      key, 
      3600, 
      JSON.stringify(value)
    );
    
    // 2. ローカルキャッシュに保存
    this.localCache.set(key, value);
    
    // 3. 無効化イベント発行
    await this.publishInvalidation(key);
  }
  
  async publishInvalidation(key) {
    await this.redis.publish('cache:invalidate', JSON.stringify({
      key,
      server: process.env.SERVER_ID,
      timestamp: Date.now()
    }));
  }
}
```

### 2. キャッシュウォーミング戦略
```javascript
class CacheWarmer {
  constructor(cache, db) {
    this.cache = cache;
    this.db = db;
  }
  
  async warmCache() {
    // 1. 人気アイテムの事前読み込み
    const popularItems = await this.db.query(`
      SELECT key, value 
      FROM data 
      WHERE access_count > 1000 
      ORDER BY access_count DESC 
      LIMIT 100
    `);
    
    // 2. バッチでキャッシュに投入
    const batchSize = 10;
    for (let i = 0; i < popularItems.rows.length; i += batchSize) {
      const batch = popularItems.rows.slice(i, i + batchSize);
      
      await Promise.all(
        batch.map(item => 
          this.cache.set(item.key, item.value, { 
            ttl: 7200 // 長めのTTL
          })
        )
      );
      
      // サーバー負荷を考慮して待機
      await delay(100);
    }
  }
  
  async scheduleWarming() {
    // 定期的なウォーミング
    setInterval(() => {
      this.warmCache().catch(console.error);
    }, 3600000); // 1時間ごと
  }
}
```

### 3. 一貫性保証レベル
```javascript
class ConsistencyManager {
  async read(key, consistencyLevel = 'eventual') {
    switch (consistencyLevel) {
      case 'strong':
        // 常にDBから読む
        return await this.db.query(
          'SELECT * FROM data WHERE key = $1', 
          [key]
        );
        
      case 'bounded':
        // 一定時間以内のキャッシュを許可
        const cached = await this.cache.get(key);
        if (cached && cached.timestamp > Date.now() - 5000) {
          return cached.value;
        }
        return await this.readThrough(key);
        
      case 'eventual':
      default:
        // キャッシュ優先
        return await this.cache.get(key) || 
               await this.readThrough(key);
    }
  }
}
```

## パフォーマンステスト

### マルチサーバーでのスケーラビリティ
```javascript
async function testScalability() {
  const configurations = [
    { servers: 1, cacheNodes: 1 },
    { servers: 2, cacheNodes: 3 },
    { servers: 4, cacheNodes: 6 },
    { servers: 8, cacheNodes: 12 }
  ];
  
  for (const config of configurations) {
    const result = await runLoadTest({
      servers: config.servers,
      cacheNodes: config.cacheNodes,
      duration: 60000,
      concurrentClients: 1000,
      readWriteRatio: 9 // 90% read, 10% write
    });
    
    console.log(`Config: ${JSON.stringify(config)}`);
    console.log(`Throughput: ${result.throughput} req/s`);
    console.log(`Cache Hit Rate: ${result.cacheHitRate}%`);
    console.log(`Avg Latency: ${result.avgLatency}ms`);
    console.log('---');
  }
}
```

### 期待される結果
| サーバー数 | キャッシュノード | スループット | ヒット率 | レイテンシ |
|----------|--------------|------------|---------|-----------|
| 1 | 1 | 1,000 req/s | 85% | 10ms |
| 2 | 3 | 1,900 req/s | 87% | 11ms |
| 4 | 6 | 3,700 req/s | 89% | 12ms |
| 8 | 12 | 7,200 req/s | 91% | 13ms |

## 障害シナリオと対策

### 1. Redis Cluster ノード障害
```javascript
async function handleNodeFailure() {
  try {
    await cache.get('critical:data');
  } catch (error) {
    if (error.code === 'CLUSTERDOWN') {
      // フォールバック: 直接DBアクセス
      console.log('Cache cluster down, falling back to DB');
      return await db.query('SELECT * FROM data WHERE key = $1', ['critical:data']);
    }
    throw error;
  }
}
```

### 2. ネットワークパーティション対策
```javascript
class PartitionTolerantCache {
  async write(key, value) {
    // Quorum書き込み
    const nodes = this.getHealthyNodes();
    const quorum = Math.floor(nodes.length / 2) + 1;
    
    const results = await Promise.allSettled(
      nodes.map(node => node.set(key, value))
    );
    
    const successes = results.filter(r => r.status === 'fulfilled').length;
    
    if (successes < quorum) {
      throw new Error('Failed to achieve write quorum');
    }
  }
}
```

## 監視とメトリクス

```javascript
class CacheMetrics {
  constructor() {
    this.metrics = {
      hits: 0,
      misses: 0,
      errors: 0,
      latencies: []
    };
  }
  
  recordHit() { this.metrics.hits++; }
  recordMiss() { this.metrics.misses++; }
  recordError() { this.metrics.errors++; }
  recordLatency(ms) { 
    this.metrics.latencies.push(ms);
    if (this.metrics.latencies.length > 1000) {
      this.metrics.latencies.shift();
    }
  }
  
  getStats() {
    const total = this.metrics.hits + this.metrics.misses;
    const hitRate = total > 0 ? (this.metrics.hits / total) * 100 : 0;
    
    const latencies = [...this.metrics.latencies].sort((a, b) => a - b);
    const p50 = latencies[Math.floor(latencies.length * 0.5)] || 0;
    const p99 = latencies[Math.floor(latencies.length * 0.99)] || 0;
    
    return {
      hitRate: `${hitRate.toFixed(2)}%`,
      totalRequests: total,
      errors: this.metrics.errors,
      latency: { p50, p99 }
    };
  }
}
```

## Docker Compose設定

```yaml
version: '3.8'

services:
  # アプリケーションサーバー群
  app-1:
    build: .
    environment:
      SERVER_ID: app-1
      REDIS_CLUSTER: redis-1:7000,redis-2:7001,redis-3:7002
      DB_URL: postgresql://user:pass@postgres:5432/db
    depends_on:
      - redis-1
      - redis-2
      - redis-3
      - postgres

  app-2:
    build: .
    environment:
      SERVER_ID: app-2
      REDIS_CLUSTER: redis-1:7000,redis-2:7001,redis-3:7002
      DB_URL: postgresql://user:pass@postgres:5432/db
    depends_on:
      - redis-1
      - redis-2
      - redis-3
      - postgres

  # Redis Cluster
  redis-1:
    image: redis:7-alpine
    command: >
      redis-server
      --port 7000
      --cluster-enabled yes
      --cluster-config-file nodes.conf
      --cluster-node-timeout 5000
      --appendonly yes

  redis-2:
    image: redis:7-alpine
    command: >
      redis-server
      --port 7001
      --cluster-enabled yes
      --cluster-config-file nodes.conf
      --cluster-node-timeout 5000
      --appendonly yes

  redis-3:
    image: redis:7-alpine
    command: >
      redis-server
      --port 7002
      --cluster-enabled yes
      --cluster-config-file nodes.conf
      --cluster-node-timeout 5000
      --appendonly yes

  # データベース
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  # メッセージバス（無効化イベント用）
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "15672:15672"
      - "5672:5672"
```

## ベストプラクティス

1. **階層型キャッシュ**: L1（ローカル）→ L2（分散）→ DB
2. **適切なTTL設定**: データの特性に応じた有効期限
3. **キャッシュスタンピード対策**: 分散ロックまたは確率的早期失効
4. **モニタリング**: ヒット率、レイテンシ、エラー率の継続的監視
5. **グレースフルデグレード**: キャッシュ障害時のフォールバック

## まとめ

分散キャッシュは性能向上に大きく貢献しますが、一貫性、可用性、分断耐性のトレードオフを慎重に管理する必要があります。

## 次のステップ

このマルチサーバーキャッシュの知見を活かし、`19_write_read_separation`で読み書き分離パターンを実装します。

## 参考資料

- [Redis Cluster Specification](https://redis.io/docs/manual/scaling/)
- [Distributed Caching Best Practices](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/)
- [Cache Stampede Prevention](https://en.wikipedia.org/wiki/Cache_stampede)
- [Consistency Models in Distributed Systems](https://jepsen.io/consistency)