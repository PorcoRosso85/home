# 11_dual_servers_manual_split

## 概要

Phase 3の開始として、2台の物理サーバー（またはVM）に手動でトラフィックを分割します。最もシンプルな水平スケーリングから始め、複数サーバー運用の基礎を確立します。

## 目的

- 複数サーバー環境の構築と検証
- 手動トラフィック分割の実装
- クロスサーバー通信の確立
- 基本的な可用性の向上

## アーキテクチャ

```
┌─────────────────────────────────┐
│         Clients (N)             │
│   Manual Traffic Splitting      │
│     (DNS / App Logic)          │
└────────┬───────────┬────────────┘
         │           │
    50%  │           │  50%
         ▼           ▼
┌─────────────┐ ┌─────────────┐
│  Server-1   │ │  Server-2   │
│ Region: A-M │ │ Region: N-Z │
│             │ │             │
│ ┌─────────┐ │ │ ┌─────────┐ │
│ │ App     │ │ │ │ App     │ │
│ │ DB(A-M) │ │ │ │ DB(N-Z) │ │
│ └─────────┘ │ │ └─────────┘ │
└─────────────┘ └─────────────┘
       │                 │
       └────────┬────────┘
                │
        [Sync/Replication]
```

## 検証項目

### 1. 基本的な分割戦略
- **ユーザーベース分割**: アルファベット順、ID範囲
- **地理的分割**: リージョン、タイムゾーン
- **機能別分割**: 読み取り/書き込み、API/Web
- **負荷ベース分割**: リソース使用量による

### 2. サーバー間通信
- **データ同期**: 必要なデータの複製
- **サービス発見**: 相互のエンドポイント管理
- **ヘルスチェック**: 相互監視
- **フェイルオーバー**: 手動切り替え手順

### 3. 運用上の課題
- **デプロイメント**: 2サーバーへの展開
- **監視**: 統合されたメトリクス
- **ログ管理**: 分散ログの集約
- **トラブルシューティング**: 問題の切り分け

## TDDアプローチ

### Red Phase (2サーバー構成のテスト)
```typescript
// test/dual-server-manual.test.ts
import { assertEquals, assertExists, assert } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeAll } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { ServerEnvironment, ClientManager } from "./test-helpers.ts";

describe('Dual Server Manual Split Configuration', () => {
  let server1: ServerEnvironment, server2: ServerEnvironment;
  let clients: ClientManager;
  
  beforeAll(async () => {
    // 2つのサーバー環境をセットアップ
    server1 = new ServerEnvironment({
      name: 'server-1',
      host: Deno.env.get('SERVER1_HOST') || 'localhost:4001',
      dataPartition: 'A-M',
      db: {
        type: 'postgres',
        partition: "WHERE user_id ~ '^[A-M]'"
      }
    });
    
    server2 = new ServerEnvironment({
      name: 'server-2', 
      host: Deno.env.get('SERVER2_HOST') || 'localhost:4002',
      dataPartition: 'N-Z',
      db: {
        type: 'postgres',
        partition: "WHERE user_id ~ '^[N-Z]'"
      }
    });
    
    await Promise.all([server1.start(), server2.start()]);
    
    // クライアントの初期化
    clients = new ClientManager({
      routing: 'manual',
      servers: [server1, server2]
    });
  });

  it('should route clients based on user ID', async () => {
    const testUsers = [
      { id: 'alice123', expected: 'server-1' },
      { id: 'bob456', expected: 'server-1' },
      { id: 'nancy789', expected: 'server-2' },
      { id: 'oscar012', expected: 'server-2' },
      { id: 'mike345', expected: 'server-1' },
      { id: 'zoe678', expected: 'server-2' }
    ];
    
    for (const user of testUsers) {
      const response = await clients.request({
        userId: user.id,
        path: '/api/profile'
      });
      
      assertEquals(response.server, user.expected);
      assertEquals(response.status, 200);
      
      // データが正しいサーバーに保存されているか
      const data = await response.json();
      assertEquals(data.userId, user.id);
    }
  });

  it('should handle cross-server queries', async () => {
    // ユーザーAがユーザーNのデータを参照するケース
    const crossServerRequest = await clients.request({
      userId: 'alice123',
      path: '/api/user/nancy789/profile'
    });
    
    assertEquals(crossServerRequest.status, 200);
    
    // 内部でのサーバー間通信を確認
    const logs = await server1.getLogs({ filter: 'cross-server' });
    const crossServerCall = logs.find(log => 
      log.message.includes('Fetching from server-2')
    );
    
    assertExists(crossServerCall);
    assert(crossServerCall.latency < 100); // ms
  });

  it('should maintain data consistency', async () => {
    // 両サーバーに影響する操作（例：グローバル設定）
    const globalUpdate = {
      setting: 'maintenance_mode',
      value: true
    };
    
    // Server1で更新
    await clients.request({
      userId: 'admin',
      path: '/api/global-settings',
      method: 'PUT',
      body: globalUpdate
    });
    
    // 同期を待つ
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 両サーバーで確認
    const [check1, check2] = await Promise.all([
      server1.query('SELECT * FROM global_settings WHERE key = $1', ['maintenance_mode']),
      server2.query('SELECT * FROM global_settings WHERE key = $1', ['maintenance_mode'])
    ]);
    
    assertEquals(check1.rows[0].value, true);
    assertEquals(check2.rows[0].value, true);
  });

  it('should handle server failure manually', async () => {
    // Server1を停止
    await server1.stop();
    
    // Server1のユーザーがアクセス
    const failedRequest = await clients.request({
      userId: 'alice123',
      path: '/api/profile',
      timeout: 5000
    });
    
    assertEquals(failedRequest.status, 503);
    
    // 手動フェイルオーバー手順を実行
    const failoverResult = await executeManualFailover({
      from: 'server-1',
      to: 'server-2',
      users: ['A-M']
    });
    
    assertEquals(failoverResult.success, true);
    
    // 再試行（今度はServer2が処理）
    const retryRequest = await clients.request({
      userId: 'alice123',
      path: '/api/profile'
    });
    
    assertEquals(retryRequest.status, 200);
    assertEquals(retryRequest.server, 'server-2');
  });

  it('should test deployment strategies', async () => {
    const newVersion = 'v2.0.0';
    
    // Server1から順番にデプロイ
    const deployment = new DeploymentManager([server1, server2]);
    
    // ステップ1: Server1をデプロイ
    await deployment.deployToServer(server1, {
      version: newVersion,
      healthCheck: true
    });
    
    // Server1の新バージョンを確認
    const version1 = await server1.getVersion();
    assertEquals(version1, newVersion);
    
    // Server2はまだ旧バージョン
    const version2 = await server2.getVersion();
    assert(version2 !== newVersion);
    
    // この時点でのサービス可用性を確認
    const availability = await measureAvailability(60000); // 1分間
    assert(availability > 0.99); // 99%以上
    
    // ステップ2: Server2をデプロイ
    await deployment.deployToServer(server2, {
      version: newVersion,
      healthCheck: true
    });
    
    // 両方新バージョンに
    assertEquals(await server2.getVersion(), newVersion);
  });

  it('should aggregate metrics from both servers', async () => {
    // 負荷を生成
    await generateLoad({
      duration: 30000,
      rps: 100,
      distribution: {
        'A-M': 0.5,
        'N-Z': 0.5
      }
    });
    
    // メトリクスを収集
    const metrics = await collectMetrics([server1, server2]);
    
    // 統合メトリクス
    const aggregated = {
      totalRequests: metrics.server1.requests + metrics.server2.requests,
      avgLatency: (metrics.server1.avgLatency + metrics.server2.avgLatency) / 2,
      totalErrors: metrics.server1.errors + metrics.server2.errors
    };
    
    assert(aggregated.totalRequests > 2500);
    assert(aggregated.avgLatency < 100);
    assert(aggregated.totalErrors / aggregated.totalRequests < 0.01);
    
    // 負荷分散の均等性
    const distribution = metrics.server1.requests / aggregated.totalRequests;
    assert(distribution > 0.45);
    assert(distribution < 0.55);
  });
});

// 手動フェイルオーバーのテスト
describe('Manual Failover Procedures', () => {
  it('should execute failover checklist', async () => {
    const checklist = [
      {
        step: 'Verify target server capacity',
        action: async () => {
          const capacity = await server2.getResourceUsage();
          return capacity.cpu < 50 && capacity.memory < 70;
        }
      },
      {
        step: 'Update DNS/routing configuration',
        action: async () => {
          await updateRoutingConfig({
            'A-M': 'server-2',
            'N-Z': 'server-2'
          });
          return true;
        }
      },
      {
        step: 'Migrate active sessions',
        action: async () => {
          const sessions = await server1.getActiveSessions();
          await server2.importSessions(sessions);
          return true;
        }
      },
      {
        step: 'Verify data accessibility',
        action: async () => {
          const testQueries = [
            "SELECT COUNT(*) FROM users WHERE user_id LIKE 'a%'",
            "SELECT COUNT(*) FROM users WHERE user_id LIKE 'm%'"
          ];
          
          for (const query of testQueries) {
            const result = await server2.query(query);
            if (result.rows[0].count === 0) return false;
          }
          return true;
        }
      }
    ];
    
    const results = [];
    
    for (const item of checklist) {
      console.log(`Executing: ${item.step}`);
      const success = await item.action();
      results.push({ step: item.step, success });
      
      if (!success) {
        throw new Error(`Failover failed at: ${item.step}`);
      }
    }
    
    assert(results.every(r => r.success));
  });
});
```

### Green Phase (2サーバー構成の実装)
```typescript
// dual-server-app.ts
import { Application, Router } from "https://deno.land/x/oak@v12.6.1/mod.ts";
import { Pool } from "https://deno.land/x/postgres@v0.17.0/mod.ts";

class DualServerApplication {
  private config: any;
  private app: Application;
  private router: Router;
  private pool: Pool;
  private partitionKey: string;
  private peerServer: string;
  private peerHealthy: boolean = true;
  
  constructor(config: any) {
    this.config = config;
    this.app = new Application();
    this.router = new Router();
    this.pool = new Pool(config.database, 3);
    this.partitionKey = config.partitionKey;
    this.peerServer = config.peerServer;
    
    this.setupRoutes();
    this.setupHealthChecks();
  }
  
  setupRoutes() {
    // ルーティングミドルウェア
    this.router.use(async (ctx, next) => {
      const userId = ctx.request.headers.get('x-user-id') || ctx.request.url.searchParams.get('userId');
      
      if (userId && !this.isMyPartition(userId)) {
        // 間違ったサーバーへのリクエスト
        ctx.response.status = 421;
        ctx.response.body = {
          error: 'Misdirected Request',
          correctServer: this.getCorrectServer(userId),
          hint: 'Client should redirect to correct server'
        };
        return;
      }
      
      ctx.state.userId = userId;
      await next();
    });
    
    // ユーザープロファイル
    this.router.get('/api/profile', async (ctx) => {
      try {
        const profile = await this.getUserProfile(ctx.state.userId);
        ctx.response.body = {
          ...profile,
          server: this.config.name,
          partition: this.config.partitionKey
        };
      } catch (error) {
        ctx.response.status = 500;
        ctx.response.body = { error: error.message };
      }
    });
    
    // クロスサーバークエリ
    this.router.get('/api/user/:targetUserId/profile', async (ctx) => {
      const { targetUserId } = ctx.params;
      
      if (!this.isMyPartition(targetUserId)) {
        // 他のサーバーから取得
        try {
          const response = await this.queryPeerServer(
            `/api/profile`,
            { userId: targetUserId }
          );
          
          ctx.response.body = {
            ...response,
            fetched_from: response.server,
            requested_by: ctx.state.userId
          };
        } catch (error) {
          ctx.response.status = 500;
          ctx.response.body = {
            error: 'Cross-server query failed',
            details: error.message
          };
        }
      } else {
        // ローカルで処理
        const profile = await this.getUserProfile(targetUserId);
        ctx.response.body = profile;
      }
    });
    
    // グローバル設定（同期が必要）
    this.router.put('/api/global-settings', async (ctx) => {
      const body = await ctx.request.body({ type: 'json' }).value;
      const { setting, value } = body;
      
      try {
        // ローカルDBに保存
        await this.pool.query(
          'INSERT INTO global_settings (key, value, updated_at) VALUES ($1, $2, NOW()) ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()',
          [setting, value]
        );
        
        // ピアサーバーに同期（非同期）
        this.syncToPeer('/api/sync/global-settings', { setting, value })
          .catch(err => console.error('Sync failed:', err));
        
        ctx.response.body = { success: true, server: this.config.name };
      } catch (error) {
        ctx.response.status = 500;
        ctx.response.body = { error: error.message };
      }
    });
    
    // 同期エンドポイント
    this.router.post('/api/sync/global-settings', async (ctx) => {
      const body = await ctx.request.body({ type: 'json' }).value;
      const { setting, value } = body;
      
      try {
        await this.pool.query(
          'INSERT INTO global_settings (key, value, updated_at, synced) VALUES ($1, $2, NOW(), true) ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW(), synced = true',
          [setting, value]
        );
        
        ctx.response.body = { success: true };
      } catch (error) {
        ctx.response.status = 500;
        ctx.response.body = { error: error.message };
      }
    });
    
    // メトリクスエンドポイント
    this.router.get('/api/metrics', async (ctx) => {
      const metrics = await this.collectMetrics();
      ctx.response.body = {
        server: this.config.name,
        partition: this.config.partitionKey,
        ...metrics
      };
    });
    
    this.app.use(this.router.routes());
    this.app.use(this.router.allowedMethods());
  }
  
  setupHealthChecks() {
    // 自己ヘルスチェック
    this.router.get('/health', async (ctx) => {
      try {
        // DB接続確認
        await this.pool.query('SELECT 1');
        
        // ピアサーバー接続確認
        let peerStatus = 'unknown';
        try {
          const peerHealth = await fetch(`${this.peerServer}/health`, {
            signal: AbortSignal.timeout(2000)
          });
          const data = await peerHealth.json();
          peerStatus = data.status;
        } catch (e) {
          peerStatus = 'unreachable';
        }
        
        ctx.response.body = {
          status: 'healthy',
          server: this.config.name,
          database: 'connected',
          peer: peerStatus,
          uptime: performance.now() / 1000
        };
      } catch (error) {
        ctx.response.status = 503;
        ctx.response.body = {
          status: 'unhealthy',
          error: error.message
        };
      }
    });
    
    // 相互ヘルスチェック
    setInterval(async () => {
      try {
        const health = await fetch(`${this.peerServer}/health`, {
          signal: AbortSignal.timeout(5000)
        });
        const data = await health.json();
        
        this.peerHealthy = data.status === 'healthy';
      } catch (error) {
        this.peerHealthy = false;
        console.error('Peer health check failed:', error.message);
      }
    }, 10000); // 10秒ごと
  }
  
  isMyPartition(userId: string): boolean {
    const firstChar = userId[0].toUpperCase();
    
    if (this.config.partitionKey === 'A-M') {
      return firstChar >= 'A' && firstChar <= 'M';
    } else if (this.config.partitionKey === 'N-Z') {
      return firstChar >= 'N' && firstChar <= 'Z';
    }
    
    return false;
  }
  
  getCorrectServer(userId: string): string {
    return this.isMyPartition(userId) ? this.config.name : this.peerServer;
  }
  
  async getUserProfile(userId: string) {
    const client = await this.pool.connect();
    try {
      const result = await client.queryObject(
        'SELECT * FROM users WHERE user_id = $1',
        [userId]
      );
    
      if (result.rows.length === 0) {
        // 新規ユーザーの作成
        const insertResult = await client.queryObject(
          'INSERT INTO users (user_id, created_at) VALUES ($1, NOW()) RETURNING *',
          [userId]
        );
        return insertResult.rows[0];
      }
      
      return result.rows[0];
    } finally {
      client.release();
    }
  }
  
  async queryPeerServer(path: string, params: any) {
    console.log(`Cross-server query to ${this.peerServer}${path}`);
    
    const url = new URL(`${this.peerServer}${path}`);
    Object.keys(params).forEach(key => url.searchParams.set(key, params[key]));
    
    const response = await fetch(url, {
      headers: {
        'X-User-Id': params.userId,
        'X-Requesting-Server': this.config.name
      },
      signal: AbortSignal.timeout(5000)
    });
    
    return await response.json();
  }
  
  async syncToPeer(path: string, data: any) {
    if (!this.peerHealthy) {
      console.warn('Peer is unhealthy, queuing sync operation');
      await this.queueSyncOperation(path, data);
      return;
    }
    
    await fetch(`${this.peerServer}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sync-From': this.config.name
      },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(5000)
    });
  }
  
  async queueSyncOperation(path: string, data: any) {
    // 同期キューに保存（後でリトライ）
    const client = await this.pool.connect();
    try {
      await client.queryObject(
        'INSERT INTO sync_queue (path, data, created_at) VALUES ($1, $2, NOW())',
        [path, JSON.stringify(data)]
      );
    } finally {
      client.release();
    }
  }
  
  async collectMetrics() {
    const client = await this.pool.connect();
    try {
      const result = await client.queryObject(`
        SELECT 
          (SELECT COUNT(*) FROM users) as total_users,
          (SELECT COUNT(*) FROM global_settings) as total_settings,
          (SELECT COUNT(*) FROM sync_queue WHERE processed = false) as pending_syncs
      `);
      
      return {
        ...result.rows[0],
        connections: {
          active: this.pool.size,
          idle: this.pool.available,
          waiting: 0
        }
      };
    } finally {
      client.release();
    }
  }
  
  async start() {
    const port = this.config.port || 3000;
    
    console.log(`Server ${this.config.name} (${this.config.partitionKey}) listening on port ${port}`);
    console.log(`Peer server: ${this.peerServer}`);
    
    await this.app.listen({ port });
  }
}

// 起動スクリプト
if (import.meta.main) {
  const config = {
    name: Deno.env.get('SERVER_NAME') || 'server-1',
    port: parseInt(Deno.env.get('PORT') || '3001'),
    partitionKey: Deno.env.get('PARTITION_KEY') || 'A-M',
    peerServer: Deno.env.get('PEER_SERVER') || 'http://localhost:3002',
    database: {
      hostname: Deno.env.get('DB_HOST') || 'localhost',
      port: parseInt(Deno.env.get('DB_PORT') || '5432'),
      database: Deno.env.get('DB_NAME') || 'server1_db',
      user: Deno.env.get('DB_USER') || 'dbuser',
      password: Deno.env.get('DB_PASSWORD') || 'dbpass'
    }
  };
  
  const server = new DualServerApplication(config);
  await server.start();
}

export { DualServerApplication };
```

### デプロイメント設定
```yaml
# docker-compose-server1.yml
version: '3.8'

services:
  app:
    image: denoland/deno:alpine
    command: run --allow-net --allow-env --allow-read dual-server-app.ts
    volumes:
      - ./:/app
    working_dir: /app
    ports:
      - "4001:3000"
    environment:
      SERVER_NAME: server-1
      PORT: 3000
      PARTITION_KEY: A-M
      PEER_SERVER: http://server2.example.com:4002
      DB_HOST: postgres
      DB_NAME: server1_db
    depends_on:
      - postgres
      
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: server1_db
      POSTGRES_USER: dbuser
      POSTGRES_PASSWORD: dbpass
    volumes:
      - postgres-data-1:/var/lib/postgresql/data

volumes:
  postgres-data-1:
```

```yaml
# docker-compose-server2.yml
version: '3.8'

services:
  app:
    image: denoland/deno:alpine
    command: run --allow-net --allow-env --allow-read dual-server-app.ts
    volumes:
      - ./:/app
    working_dir: /app
    ports:
      - "4002:3000"
    environment:
      SERVER_NAME: server-2
      PORT: 3000
      PARTITION_KEY: N-Z
      PEER_SERVER: http://server1.example.com:4001
      DB_HOST: postgres
      DB_NAME: server2_db
    depends_on:
      - postgres
      
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: server2_db
      POSTGRES_USER: dbuser
      POSTGRES_PASSWORD: dbpass
    volumes:
      - postgres-data-2:/var/lib/postgresql/data

volumes:
  postgres-data-2:
```

## 実行と検証

### 1. 両サーバーの起動
```bash
# Server 1
cd server1
docker-compose -f docker-compose-server1.yml up -d

# Server 2
cd server2
docker-compose -f docker-compose-server2.yml up -d
```

### 2. 手動ルーティングテスト
```bash
# A-Mユーザー
curl -H "X-User-Id: alice123" http://server1:4001/api/profile

# N-Zユーザー
curl -H "X-User-Id: nancy789" http://server2:4002/api/profile

# 間違ったサーバーへのアクセス
curl -H "X-User-Id: nancy789" http://server1:4001/api/profile
# Expected: 421 Misdirected Request
```

### 3. フェイルオーバー手順
```bash
# 手動フェイルオーバースクリプト
./scripts/manual-failover.sh --from server1 --to server2
```

## 成功基準

- [ ] 2サーバーへの正しいトラフィック分割
- [ ] サーバー間通信の成功
- [ ] 手動フェイルオーバーの実行（5分以内）
- [ ] 両サーバーのメトリクス統合
- [ ] 99%以上の可用性維持

## 運用手順書

### デプロイメント手順
1. Server1のヘルスチェック無効化
2. Server1へのコードデプロイ
3. Server1の起動とヘルスチェック
4. Server1のヘルスチェック有効化
5. Server2で1-4を繰り返し

### 障害対応手順
1. 障害サーバーの特定
2. トラフィックの手動切り替え
3. データ同期状態の確認
4. 障害サーバーの調査・復旧
5. 正常状態への復帰

## 次のステップ

手動分割の基礎を確立後、`12_dual_servers_with_haproxy`でHAProxyによる自動化された負荷分散を実装します。

## 学んだこと

- 最もシンプルな水平スケーリング
- サーバー間通信の基礎
- 手動運用の限界と自動化の必要性
- 分散システムの複雑性の始まり

## 参考資料

- [Horizontal Scaling Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/sharding)
- [Database Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Manual Failover Procedures](https://www.percona.com/blog/2018/10/02/manual-failover-mysql-replication/)
- [Multi-Region Deployment](https://aws.amazon.com/builders-library/going-global-multi-region/)