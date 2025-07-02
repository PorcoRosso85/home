# 17_cache_layer_single_server

## 概要

単一サーバー環境でのキャッシュレイヤー導入による性能向上と、キャッシュとDBの一貫性問題を実践的に検証します。Write-Through、Write-Behind、Cache-Asideパターンの実装と比較を行います。

## 目的

- キャッシュ導入による性能向上の測定
- キャッシュとDBの一貫性問題の実証
- 各キャッシュパターンの長所と短所の理解
- 補償トランザクションの必要性の確認

## アーキテクチャ

```
┌─────────────────────────────────┐
│         Clients (N)             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│      Application Server         │
│  ┌─────────────────────────┐    │
│  │    Cache Strategy       │    │
│  │  - Write-Through        │    │
│  │  - Write-Behind         │    │
│  │  - Cache-Aside          │    │
│  └─────────┬───────────────┘    │
└────────────┼────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌──────────┐  ┌──────────┐
│  Redis   │  │PostgreSQL│
│  Cache   │  │    DB    │
│          │  │          │
│ ⚠️ Sync  │  │          │
└──────────┘  └──────────┘
```

## ⚠️ 重要な障害点

キャッシュとDBへの二重書き込みにおける**原子性の欠如**による致命的なデータ不整合リスク

## キャッシュ戦略の詳細

### 1. Write-Through (同期書き込み)
```javascript
async function writeThrough(key, value) {
  try {
    // 1. DBに書き込み
    await db.query('UPDATE data SET value = $1 WHERE key = $2', [value, key]);
    
    // 2. 成功したらキャッシュに書き込み
    await redis.set(key, value, 'EX', 3600);
    
    return { success: true };
  } catch (error) {
    // DBエラー時はキャッシュも更新しない
    throw error;
  }
}
```
**問題**: DB成功後のキャッシュ書き込み失敗で不整合

### 2. Write-Behind (非同期書き込み)
```javascript
async function writeBehind(key, value) {
  // 1. キャッシュに即座に書き込み
  await redis.set(key, value, 'EX', 3600);
  
  // 2. DBへの書き込みをキューに追加
  await queue.push({ action: 'write', key, value });
  
  return { success: true };
}

// バックグラウンドワーカー
async function processQueue() {
  while (true) {
    const item = await queue.pop();
    try {
      await db.query('UPDATE data SET value = $1 WHERE key = $2', [item.value, item.key]);
    } catch (error) {
      // エラー時の処理（再試行、DLQ等）
      await handleWriteFailure(item);
    }
  }
}
```
**問題**: システムクラッシュ時のデータロスト

### 3. Cache-Aside (遅延読み込み)
```javascript
async function cacheAside(key) {
  // 1. キャッシュから読み取り
  let value = await redis.get(key);
  
  if (!value) {
    // 2. キャッシュミス時はDBから読み取り
    const result = await db.query('SELECT value FROM data WHERE key = $1', [key]);
    value = result.rows[0]?.value;
    
    if (value) {
      // 3. キャッシュに保存
      await redis.set(key, value, 'EX', 3600);
    }
  }
  
  return value;
}
```
**利点**: 読み取り専用で一貫性問題が少ない

## TDDアプローチ

### Red Phase (問題を露呈するテスト)
```javascript
// test/cache-consistency.test.js
describe('Cache and DB Consistency Issues', () => {
  it('should demonstrate write-through failure', async () => {
    // DB成功、キャッシュ失敗のシミュレーション
    const mockRedis = {
      set: jest.fn().mockRejectedValue(new Error('Redis connection failed'))
    };
    
    const result = await writeThrough('user:1', { balance: 1000 });
    
    // DBには書き込まれたがキャッシュは古いまま
    const dbValue = await db.query('SELECT * FROM users WHERE id = 1');
    const cacheValue = await redis.get('user:1');
    
    expect(dbValue.rows[0].balance).toBe(1000);
    expect(cacheValue).toBeNull(); // または古い値
    expect(dbValue.rows[0].balance).not.toEqual(cacheValue);
  });

  it('should demonstrate write-behind data loss', async () => {
    // キャッシュに書き込み
    await writeBehind('order:123', { status: 'confirmed' });
    
    // キャッシュには存在
    const cacheValue = await redis.get('order:123');
    expect(cacheValue.status).toBe('confirmed');
    
    // サーバークラッシュをシミュレート
    await simulateServerCrash();
    
    // DB確認 - データが失われている
    const dbValue = await db.query('SELECT * FROM orders WHERE id = 123');
    expect(dbValue.rows.length).toBe(0);
  });

  it('should demonstrate cache invalidation race condition', async () => {
    // 初期状態
    await db.query('INSERT INTO products (id, price) VALUES (1, 100)');
    await redis.set('product:1', { price: 100 });
    
    // 並行更新
    const update1 = updateProductPrice(1, 150);
    const update2 = updateProductPrice(1, 200);
    
    await Promise.all([update1, update2]);
    
    // 最終状態の不整合
    const dbValue = await db.query('SELECT price FROM products WHERE id = 1');
    const cacheValue = await redis.get('product:1');
    
    // DBとキャッシュで異なる値の可能性
    console.log('DB:', dbValue.rows[0].price, 'Cache:', cacheValue.price);
    expect(dbValue.rows[0].price).not.toEqual(cacheValue.price);
  });
});
```

### 具体的な障害シナリオ

#### シナリオ1: 決済処理での致命的エラー
```
1. ユーザーが1000円の決済実行
2. DB更新成功（残高: 5000円 → 4000円）
3. キャッシュ更新失敗 ❌
4. 次回読み取り時、キャッシュから5000円を返却
5. ユーザーは二重決済可能に 💸
```

#### シナリオ2: 在庫管理での問題
```
1. 在庫10個の商品
2. キャッシュ更新成功（10 → 9）
3. DB更新失敗 ❌
4. システム再起動後、DBから10個を読み込み
5. 超過販売のリスク 📦
```

## 解決パターン

### パターン1: 2フェーズコミット
```javascript
async function twoPhaseCommit(key, value) {
  const redisTransaction = redis.multi();
  const dbClient = await db.connect();
  
  try {
    // Prepare phase
    await dbClient.query('BEGIN');
    redisTransaction.set(key, JSON.stringify(value));
    
    // Commit phase
    await dbClient.query('UPDATE data SET value = $1 WHERE key = $2', [value, key]);
    await dbClient.query('COMMIT');
    await redisTransaction.exec();
    
    return { success: true };
  } catch (error) {
    // Rollback
    await dbClient.query('ROLLBACK');
    redisTransaction.discard();
    throw error;
  } finally {
    dbClient.release();
  }
}
```

### パターン2: Sagaパターン
```javascript
class CacheSaga {
  constructor() {
    this.steps = [
      { 
        action: this.updateDB.bind(this), 
        compensation: this.rollbackDB.bind(this) 
      },
      { 
        action: this.updateCache.bind(this), 
        compensation: this.invalidateCache.bind(this) 
      }
    ];
  }
  
  async execute(key, value) {
    const completedSteps = [];
    
    try {
      for (const step of this.steps) {
        await step.action(key, value);
        completedSteps.push(step);
      }
    } catch (error) {
      // 補償トランザクション実行
      for (const step of completedSteps.reverse()) {
        await step.compensation(key, value);
      }
      throw error;
    }
  }
}
```

### パターン3: イベントソーシング
```javascript
class EventSourcingCache {
  async write(key, value) {
    // 1. イベントをログに追加（真実の源）
    const event = {
      id: uuid(),
      type: 'DataUpdated',
      key,
      value,
      timestamp: Date.now()
    };
    
    await eventLog.append(event);
    
    // 2. 投影を非同期で更新
    await Promise.all([
      this.projectToDB(event),
      this.projectToCache(event)
    ]);
  }
}
```

## パフォーマンス測定

### キャッシュヒット率の影響
```javascript
async function measureCachePerformance() {
  const scenarios = [
    { hitRate: 0, name: 'No Cache' },
    { hitRate: 0.5, name: '50% Hit Rate' },
    { hitRate: 0.9, name: '90% Hit Rate' },
    { hitRate: 0.99, name: '99% Hit Rate' }
  ];
  
  for (const scenario of scenarios) {
    const results = await runLoadTest({
      duration: 60000,
      concurrency: 100,
      cacheHitRate: scenario.hitRate
    });
    
    console.log(`${scenario.name}:`, {
      avgLatency: results.avgLatency,
      throughput: results.throughput,
      dbLoad: results.dbLoad
    });
  }
}
```

### 期待される結果
| キャッシュヒット率 | 平均レイテンシ | スループット | DB負荷 |
|-----------------|--------------|------------|--------|
| 0% (No Cache) | 50ms | 200 req/s | 100% |
| 50% | 26ms | 380 req/s | 50% |
| 90% | 6ms | 1600 req/s | 10% |
| 99% | 1.5ms | 6400 req/s | 1% |

## 実装

### Docker Compose設定
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      REDIS_URL: redis://redis:6379
      DATABASE_URL: postgresql://user:pass@postgres:5432/db
      CACHE_STRATEGY: write-through
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  redis-data:
  postgres-data:
```

## 監視とアラート

### キャッシュ・DB不整合検出
```javascript
async function consistencyCheck() {
  const samples = await db.query('SELECT key FROM data ORDER BY RANDOM() LIMIT 100');
  
  let inconsistencies = 0;
  for (const row of samples.rows) {
    const dbValue = row.value;
    const cacheValue = await redis.get(row.key);
    
    if (cacheValue && JSON.stringify(dbValue) !== cacheValue) {
      inconsistencies++;
      console.log(`Inconsistency detected for key ${row.key}`);
    }
  }
  
  return {
    sampleSize: samples.rows.length,
    inconsistencies,
    inconsistencyRate: inconsistencies / samples.rows.length
  };
}
```

## ベストプラクティス

1. **Cache-Asideパターンを優先**: 書き込み時の不整合リスクが最小
2. **TTLを適切に設定**: 自動的な不整合解消
3. **キャッシュウォーミング**: 起動時の負荷スパイク防止
4. **サーキットブレーカー**: キャッシュ障害時の自動フォールバック
5. **メトリクス監視**: ヒット率、レイテンシ、不整合率

## 次のステップ

この単一サーバーでの学びを基に、`18_cache_layer_multi_server`で分散環境でのキャッシュ管理を実装します。

## 参考資料

- [Redis Transactions](https://redis.io/docs/manual/transactions/)
- [Database Caching Strategies](https://aws.amazon.com/caching/database-caching/)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)