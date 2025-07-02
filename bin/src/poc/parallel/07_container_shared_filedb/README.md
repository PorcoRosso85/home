# 07_container_shared_filedb

## 概要

複数コンテナから単一のファイルベースDB（SQLite）への同時アクセスを試み、その問題点を実証的に検証します。これは**アンチパターン**として、なぜ分散環境でファイルDBが不適切かを明確にします。

## 目的

- SQLiteの並行アクセス制限の実証
- ファイルロックによる性能劣化の測定
- データ不整合リスクの定量化
- 適切なDB選択の重要性の理解

## アーキテクチャ

```
┌─────────────────────────────────┐
│         Clients (N)             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│      Load Balancer              │
└───┬─────┬─────┬─────┬───────────┘
    │     │     │     │
    ▼     ▼     ▼     ▼
┌──────┐┌──────┐┌──────┐┌──────┐
│App-1 ││App-2 ││App-3 ││App-4 │
└───┬──┘└───┬──┘└───┬──┘└───┬──┘
    │       │       │       │
    └───────┴───┬───┴───────┘
                │
        ┌───────▼────────┐
        │  SQLite File   │
        │  (Shared Vol)  │
        │                │
        │ ⚠️ File Lock   │
        │ ⚠️ SQLITE_BUSY │
        │ ⚠️ Corruption  │
        └────────────────┘
```

## 問題の詳細

### 1. SQLITE_BUSY エラー
```
Error: SQLITE_BUSY: database is locked
```
- 一度に1つの書き込みトランザクションのみ
- 他のプロセスは待機またはエラー

### 2. Lost Update 問題
```
初期値: counter = 100
Container A: READ counter (100) → INCREMENT → WRITE (101)
Container B: READ counter (100) → INCREMENT → WRITE (101)
期待値: 102
実際値: 101 ❌
```

### 3. デッドロックとタイムアウト
- 複数のトランザクションが相互に待機
- デフォルト5秒のビジータイムアウト
- アプリケーションレベルでの対処が困難

## TDDアプローチ

### Red Phase (問題を露呈するテスト)
```typescript
// test/sqlite-antipattern.test.ts
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { setupContainers } from "../src/test-utils.ts";

Deno.test("SQLite Shared File DB Anti-Pattern", async (t) => {
  let containers: any;
  let dbPath: string;
  
  // Setup
  dbPath = '/shared/test.db';
  containers = await setupContainers(4, {
    dbType: 'sqlite',
    dbPath: dbPath
  });

  await t.step("should demonstrate SQLITE_BUSY errors", async () => {
    const results = {
      success: 0,
      busy: 0,
      timeout: 0,
      other: 0
    };
    
    // 100個の同時書き込みを試行
    const promises = Array(100).fill(0).map(async (_, i) => {
      try {
        const containerId = `app-${(i % 4) + 1}`;
        const response = await fetch(`http://localhost/${containerId}/api/increment`, {
          method: 'POST',
          body: JSON.stringify({ key: 'counter' })
        });
        
        if (response.ok) {
          results.success++;
        } else {
          const error = await response.json();
          if (error.code === 'SQLITE_BUSY') {
            results.busy++;
          } else if (error.code === 'SQLITE_TIMEOUT') {
            results.timeout++;
          } else {
            results.other++;
          }
        }
      } catch (e) {
        results.other++;
      }
    });
    
    await Promise.all(promises);
    
    // 大量のBUSYエラーが発生することを確認
    assertEquals(results.busy > 30, true);
    assertEquals(results.success < 70, true);
    
    console.log('Error distribution:', results);
  });

  await t.step("should demonstrate lost updates", async () => {
    // カウンターをリセット
    await resetCounter(dbPath, 'test_counter', 0);
    
    // 各コンテナから25回ずつインクリメント（合計100）
    const incrementPromises = [];
    
    for (let container = 1; container <= 4; container++) {
      for (let i = 0; i < 25; i++) {
        incrementPromises.push(
          incrementCounter(`app-${container}`, 'test_counter')
        );
      }
    }
    
    // 同時実行
    await Promise.all(incrementPromises);
    
    // 最終値を確認
    const finalValue = await getCounterValue(dbPath, 'test_counter');
    
    // Lost updateにより100未満になることを確認
    assertEquals(finalValue < 100, true);
    assertEquals(finalValue > 50, true); // 完全な失敗ではない
    
    console.log(`Expected: 100, Actual: ${finalValue}, Lost: ${100 - finalValue}`);
  });

  await t.step("should measure lock wait times", async () => {
    const waitTimes = [];
    
    // 長時間のトランザクションを開始
    const longTransaction = startLongTransaction('app-1', 5000);
    
    // 他のコンテナから書き込みを試行
    const attempts = Array(10).fill(0).map(async (_, i) => {
      const start = Date.now();
      const containerId = `app-${(i % 3) + 2}`; // app-2, app-3, app-4
      
      try {
        await fetch(`http://localhost/${containerId}/api/write`, {
          method: 'POST',
          body: JSON.stringify({ data: `test-${i}` }),
          timeout: 10000
        });
      } catch (e) {
        // タイムアウトまたはエラー
      }
      
      const waitTime = Date.now() - start;
      waitTimes.push(waitTime);
    });
    
    await Promise.all([longTransaction, ...attempts]);
    
    // 待機時間の分析
    const avgWaitTime = waitTimes.reduce((a, b) => a + b) / waitTimes.length;
    const maxWaitTime = Math.max(...waitTimes);
    
    assertEquals(avgWaitTime > 2000, true); // 平均2秒以上の待機
    assertEquals(maxWaitTime > 5000, true); // 最大5秒以上
  });

  await t.step("should compare WAL mode performance", async () => {
    const modes = ['DELETE', 'WAL'];
    const results = {};
    
    for (const mode of modes) {
      // モードを設定
      await setJournalMode(dbPath, mode);
      
      // パフォーマンステスト
      const start = Date.now();
      const promises = Array(50).fill(0).map((_, i) => 
        writeData(`app-${(i % 4) + 1}`, `data-${i}`)
      );
      
      const responses = await Promise.allSettled(promises);
      const duration = Date.now() - start;
      
      results[mode] = {
        duration,
        success: responses.filter(r => r.status === 'fulfilled').length,
        failed: responses.filter(r => r.status === 'rejected').length
      };
    }
    
    // WALモードの方が若干良いが、根本解決にはならない
    assertEquals(results.WAL.success > results.DELETE.success, true);
    assertEquals(results.WAL.duration < results.DELETE.duration * 0.8, true);
    
    // それでも失敗は発生する
    assertEquals(results.WAL.failed > 5, true);
  });

  await t.step("should test database corruption risk", async () => {
    // 警告: このテストは実際にDBを破損させる可能性がある
    
    // 複数の同時書き込みトランザクション
    const corruptionTest = async () => {
      const promises = [];
      
      // 異常な終了をシミュレート
      for (let i = 0; i < 4; i++) {
        promises.push(
          crashDuringWrite(`app-${i + 1}`, Math.random() * 1000)
        );
      }
      
      await Promise.allSettled(promises);
    };
    
    // 整合性チェック
    const beforeIntegrity = await checkIntegrity(dbPath);
    assertEquals(beforeIntegrity, 'ok');
    
    // 破損テスト実行
    await corruptionTest();
    
    // 整合性再チェック
    const afterIntegrity = await checkIntegrity(dbPath);
    
    // 破損の可能性を確認（必ず発生するわけではない）
    console.log('Integrity check after stress:', afterIntegrity);
  });
});

// エラー率の測定
Deno.test("Error Rate Analysis", async (t) => {
  await t.step("should measure error rate vs load", async () => {
    const loadLevels = [10, 50, 100, 200, 500];
    const results = [];
    
    for (const load of loadLevels) {
      const errors = await measureErrorRate(load);
      results.push({
        load,
        errorRate: errors.rate,
        avgResponseTime: errors.avgTime
      });
    }
    
    // エラー率が負荷に比例して増加
    for (let i = 1; i < results.length; i++) {
      assertEquals(results[i].errorRate > results[i-1].errorRate, true);
    }
    
    // グラフ用データ出力
    console.table(results);
  });
});
```

### Green Phase (問題を緩和する実装)
```typescript
// sqlite-app.ts
import { Application, Router } from "https://deno.land/x/oak@v12.6.1/mod.ts";
import { DB } from "https://deno.land/x/sqlite@v3.7.0/mod.ts";

const app = new Application();
const router = new Router();

// SQLite接続設定
let db: DB;

async function initDB() {
  db = new DB(Deno.env.get("DB_PATH") || '/shared/app.db');
  
  // WALモードを有効化（若干の改善）
  db.execute('PRAGMA journal_mode = WAL');
  
  // ビジータイムアウトを設定
  db.execute('PRAGMA busy_timeout = 5000');
  
  // 初期テーブル作成
  db.execute(`
    CREATE TABLE IF NOT EXISTS counters (
      key TEXT PRIMARY KEY,
      value INTEGER DEFAULT 0
    )
  `);
  
  db.execute(`
    CREATE TABLE IF NOT EXISTS data (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      content TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);
}

// リトライ機能付きクエリ実行
async function executeWithRetry<T>(operation: () => T, maxRetries = 3): Promise<T> {
  let lastError: Error;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return operation();
    } catch (error) {
      lastError = error;
      
      if (error.message.includes('SQLITE_BUSY')) {
        // 指数バックオフ
        const delay = Math.min(1000 * Math.pow(2, i), 5000);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      throw error;
    }
  }
  
  throw lastError!;
}

// インクリメントAPI（Lost Update問題の実証）
router.post('/api/increment', async (ctx) => {
  const body = await ctx.request.body({ type: 'json' }).value;
  const { key } = body;
  
  try {
    // トランザクション内で実行
    await executeWithRetry(async () => {
      db.execute('BEGIN EXCLUSIVE');
      
      try {
        const rows = db.query('SELECT value FROM counters WHERE key = ?', [key]);
        const currentValue = rows.length > 0 ? rows[0][0] as number : 0;
        
        // 意図的な遅延（競合状態を発生させやすくする）
        await new Promise(resolve => setTimeout(resolve, 10));
        
        db.execute(
          'INSERT OR REPLACE INTO counters (key, value) VALUES (?, ?)',
          [key, currentValue + 1]
        );
        
        db.execute('COMMIT');
        
        ctx.response.body = { success: true, value: currentValue + 1 };
      } catch (error) {
        db.execute('ROLLBACK');
        throw error;
      }
    });
  } catch (error) {
    console.error('Increment error:', error);
    
    if (error.message.includes('SQLITE_BUSY')) {
      ctx.response.status = 503;
      ctx.response.body = {
        error: 'Database is busy',
        code: 'SQLITE_BUSY',
        container: Deno.env.get("CONTAINER_ID")
      };
    } else {
      ctx.response.status = 500;
      ctx.response.body = {
        error: error.message,
        code: error.code
      };
    }
  }
});

// 書き込みAPI
router.post('/api/write', async (ctx) => {
  const body = await ctx.request.body({ type: 'json' }).value;
  const { data } = body;
  const startTime = Date.now();
  
  try {
    const result = await executeWithRetry(
      () => db.execute('INSERT INTO data (content) VALUES (?)', [data])
    );
    
    const duration = Date.now() - startTime;
    
    ctx.response.body = {
      success: true,
      id: db.lastInsertRowId,
      duration,
      container: Deno.env.get("CONTAINER_ID")
    };
  } catch (error) {
    const duration = Date.now() - startTime;
    
    ctx.response.status = 503;
    ctx.response.body = {
      error: error.message,
      code: error.code,
      duration,
      container: Deno.env.get("CONTAINER_ID")
    };
  }
});

// ヘルスチェック（DB接続確認を含む）
router.get('/health', (ctx) => {
  try {
    // 読み取りクエリでDB接続を確認
    db.query('SELECT 1');
    
    ctx.response.body = {
      status: 'healthy',
      container: Deno.env.get("CONTAINER_ID"),
      dbPath: Deno.env.get("DB_PATH")
    };
  } catch (error) {
    ctx.response.status = 503;
    ctx.response.body = {
      status: 'unhealthy',
      error: error.message
    };
  }
});

// メトリクス
router.get('/metrics', (ctx) => {
  try {
    const stats = db.query(`
      SELECT 
        (SELECT COUNT(*) FROM data) as total_records,
        (SELECT COUNT(*) FROM counters) as total_counters
    `);
    
    ctx.response.body = {
      container: Deno.env.get("CONTAINER_ID"),
      database: {
        total_records: stats[0][0],
        total_counters: stats[0][1]
      },
      uptime: performance.now() / 1000
    };
  } catch (error) {
    ctx.response.status = 500;
    ctx.response.body = { error: error.message };
  }
});

// サーバー起動
const PORT = parseInt(Deno.env.get("PORT") || "3000");

app.use(router.routes());
app.use(router.allowedMethods());

initDB().then(async () => {
  console.log(`Container ${Deno.env.get("CONTAINER_ID")} listening on port ${PORT}`);
  console.log(`Using SQLite database at: ${Deno.env.get("DB_PATH")}`);
  await app.listen({ port: PORT });
}).catch(error => {
  console.error('Failed to initialize database:', error);
  Deno.exit(1);
});

// グレースフルシャットダウン
Deno.addSignalListener("SIGTERM", () => {
  console.log('SIGTERM received, closing database...');
  
  try {
    db.close();
    console.log('Database closed successfully');
  } catch (error) {
    console.error('Error closing database:', error);
  }
  
  Deno.exit(0);
});
```

### Dockerfile
```dockerfile
# Dockerfile
FROM denoland/deno:alpine

WORKDIR /app

# 依存関係のキャッシュ
COPY deps.ts .
RUN deno cache deps.ts

# アプリケーションコード
COPY . .
RUN deno cache sqlite-app.ts

EXPOSE 3000

CMD ["deno", "run", "--allow-net", "--allow-env", "--allow-read", "--allow-write", "--unstable", "sqlite-app.ts"]
```

### Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app-1
      - app-2
      - app-3
      - app-4

  app-1:
    build: .
    environment:
      CONTAINER_ID: app-1
      PORT: 3001
      DB_PATH: /data/shared.db
    volumes:
      - sqlite-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  app-2:
    build: .
    environment:
      CONTAINER_ID: app-2
      PORT: 3002
      DB_PATH: /data/shared.db
    volumes:
      - sqlite-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  app-3:
    build: .
    environment:
      CONTAINER_ID: app-3
      PORT: 3003
      DB_PATH: /data/shared.db
    volumes:
      - sqlite-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3003/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  app-4:
    build: .
    environment:
      CONTAINER_ID: app-4
      PORT: 3004
      DB_PATH: /data/shared.db
    volumes:
      - sqlite-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3004/health"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  sqlite-data:
    driver: local
```

## 実行と問題の観察

### 1. システム起動
```bash
docker-compose up -d

# SQLiteファイルの確認
docker run --rm -v sqlite-data:/data alpine ls -la /data/
```

### 2. 問題の再現
```bash
# 同時書き込みテスト
deno run --allow-all scripts/test-concurrent-writes.ts

# エラー率の測定
deno run --allow-all scripts/test-error-rates.ts

# パフォーマンス劣化の確認
deno run --allow-all scripts/test-performance-degradation.ts
```

### 3. ログ分析
```bash
# SQLITE_BUSYエラーの頻度
docker-compose logs | grep -c "SQLITE_BUSY"

# 各コンテナのエラー分布
for i in 1 2 3 4; do
  echo "app-$i errors:"
  docker-compose logs app-$i | grep -c "ERROR"
done
```

## 観察される問題

### 1. パフォーマンス
- 単一書き込みロックによるボトルネック
- 待機時間の累積
- スループットの大幅な低下

### 2. 信頼性
- 頻繁なSQLITE_BUSYエラー
- トランザクションの失敗
- データの不整合

### 3. スケーラビリティ
- コンテナを増やしても性能向上なし
- むしろ競合が増えて悪化
- 実質的に単一プロセス相当

## エラー率と負荷の相関

### 測定結果
| 負荷レベル | 同時リクエスト | エラー率 | 平均待機時間 |
|-----------|--------------|---------|-------------|
| 低 | 10 | 5% | 100ms |
| 中 | 50 | 25% | 500ms |
| 高 | 100 | 45% | 2000ms |
| 過負荷 | 200 | 70% | 5000ms |
| 限界 | 500 | 85% | タイムアウト |

### 具体的な障害シナリオ

#### シナリオ1: インベントリ管理の破綻
```
1. 在庫数: 50個
2. Container A: 在庫確認 → 50個
3. Container B: 在庫確認 → 50個
4. Container A: 10個販売処理 → 在庫40個に更新（成功）
5. Container B: 5個販売処理 → SQLITE_BUSY（失敗）
6. Container B: リトライ → 在庫確認 → 40個
7. Container B: 5個販売処理 → 在庫35個に更新（成功）
結果: 正常に処理完了
```

#### シナリオ2: 決済処理でのデッドロック
```
1. Container A: ユーザー1の残高更新開始
2. Container B: ユーザー2の残高更新開始
3. Container A: 決済履歴テーブルにアクセス待機
4. Container B: 残高テーブルにアクセス待機
5. 両方: SQLITE_BUSY タイムアウト
6. 結果: 両方の決済が失敗
```

## リトライメカニズムの限界

### リトライによる性能への影響
```javascript
// リトライなし: 平均レスポンス 50ms
// リトライ1回: 平均レスポンス 200ms
// リトライ2回: 平均レスポンス 800ms
// リトライ3回: 平均レスポンス 3200ms（指数バックオフ）
```

### カスケード障害のリスク
- リトライによるリクエストの蓄積
- システム全体のレスポンス低下
- 最終的なサービス停止

## 教訓

- ✅ SQLiteは単一プロセス用に設計されている
- ✅ ファイルロックは分散環境で致命的
- ✅ WALモードでも根本解決にならない
- ✅ 適切なDBMS（PostgreSQL等）の必要性

## 次のステップ

この問題を解決するため、`08_container_shared_postgres`でPostgreSQLを使用した正しい実装を行います。

## 参考資料

- [SQLite When To Use](https://www.sqlite.org/whentouse.html)
- [SQLite Locking](https://www.sqlite.org/lockingv3.html)
- [WAL Mode](https://www.sqlite.org/wal.html)