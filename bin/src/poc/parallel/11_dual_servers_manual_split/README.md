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
```javascript
// test/dual-server-manual.test.js
describe('Dual Server Manual Split Configuration', () => {
  let server1, server2;
  let clients;
  
  beforeAll(async () => {
    // 2つのサーバー環境をセットアップ
    server1 = new ServerEnvironment({
      name: 'server-1',
      host: process.env.SERVER1_HOST || 'localhost:4001',
      dataPartition: 'A-M',
      db: {
        type: 'postgres',
        partition: "WHERE user_id ~ '^[A-M]'"
      }
    });
    
    server2 = new ServerEnvironment({
      name: 'server-2', 
      host: process.env.SERVER2_HOST || 'localhost:4002',
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
      
      expect(response.server).toBe(user.expected);
      expect(response.status).toBe(200);
      
      // データが正しいサーバーに保存されているか
      const data = await response.json();
      expect(data.userId).toBe(user.id);
    }
  });

  it('should handle cross-server queries', async () => {
    // ユーザーAがユーザーNのデータを参照するケース
    const crossServerRequest = await clients.request({
      userId: 'alice123',
      path: '/api/user/nancy789/profile'
    });
    
    expect(crossServerRequest.status).toBe(200);
    
    // 内部でのサーバー間通信を確認
    const logs = await server1.getLogs({ filter: 'cross-server' });
    const crossServerCall = logs.find(log => 
      log.message.includes('Fetching from server-2')
    );
    
    expect(crossServerCall).toBeDefined();
    expect(crossServerCall.latency).toBeLessThan(100); // ms
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
    
    expect(check1.rows[0].value).toBe(true);
    expect(check2.rows[0].value).toBe(true);
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
    
    expect(failedRequest.status).toBe(503);
    
    // 手動フェイルオーバー手順を実行
    const failoverResult = await executeManualFailover({
      from: 'server-1',
      to: 'server-2',
      users: ['A-M']
    });
    
    expect(failoverResult.success).toBe(true);
    
    // 再試行（今度はServer2が処理）
    const retryRequest = await clients.request({
      userId: 'alice123',
      path: '/api/profile'
    });
    
    expect(retryRequest.status).toBe(200);
    expect(retryRequest.server).toBe('server-2');
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
    expect(version1).toBe(newVersion);
    
    // Server2はまだ旧バージョン
    const version2 = await server2.getVersion();
    expect(version2).not.toBe(newVersion);
    
    // この時点でのサービス可用性を確認
    const availability = await measureAvailability(60000); // 1分間
    expect(availability).toBeGreaterThan(0.99); // 99%以上
    
    // ステップ2: Server2をデプロイ
    await deployment.deployToServer(server2, {
      version: newVersion,
      healthCheck: true
    });
    
    // 両方新バージョンに
    expect(await server2.getVersion()).toBe(newVersion);
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
    
    expect(aggregated.totalRequests).toBeGreaterThan(2500);
    expect(aggregated.avgLatency).toBeLessThan(100);
    expect(aggregated.totalErrors / aggregated.totalRequests).toBeLessThan(0.01);
    
    // 負荷分散の均等性
    const distribution = metrics.server1.requests / aggregated.totalRequests;
    expect(distribution).toBeGreaterThan(0.45);
    expect(distribution).toBeLessThan(0.55);
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
    
    expect(results.every(r => r.success)).toBe(true);
  });
});
```

### Green Phase (2サーバー構成の実装)
```javascript
// dual-server-app.js
const express = require('express');
const { Pool } = require('pg');
const axios = require('axios');

class DualServerApplication {
  constructor(config) {
    this.config = config;
    this.app = express();
    this.pool = new Pool(config.database);
    this.partitionKey = config.partitionKey;
    this.peerServer = config.peerServer;
    
    this.setupRoutes();
    this.setupHealthChecks();
  }
  
  setupRoutes() {
    this.app.use(express.json());
    
    // ルーティングミドルウェア
    this.app.use((req, res, next) => {
      const userId = req.headers['x-user-id'] || req.query.userId;
      
      if (userId && !this.isMyPartition(userId)) {
        // 間違ったサーバーへのリクエスト
        res.status(421).json({
          error: 'Misdirected Request',
          correctServer: this.getCorrectServer(userId),
          hint: 'Client should redirect to correct server'
        });
        return;
      }
      
      req.userId = userId;
      next();
    });
    
    // ユーザープロファイル
    this.app.get('/api/profile', async (req, res) => {
      try {
        const profile = await this.getUserProfile(req.userId);
        res.json({
          ...profile,
          server: this.config.name,
          partition: this.config.partitionKey
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
    
    // クロスサーバークエリ
    this.app.get('/api/user/:targetUserId/profile', async (req, res) => {
      const { targetUserId } = req.params;
      
      if (!this.isMyPartition(targetUserId)) {
        // 他のサーバーから取得
        try {
          const response = await this.queryPeerServer(
            `/api/profile`,
            { userId: targetUserId }
          );
          
          res.json({
            ...response.data,
            fetched_from: response.data.server,
            requested_by: req.userId
          });
        } catch (error) {
          res.status(500).json({
            error: 'Cross-server query failed',
            details: error.message
          });
        }
      } else {
        // ローカルで処理
        const profile = await this.getUserProfile(targetUserId);
        res.json(profile);
      }
    });
    
    // グローバル設定（同期が必要）
    this.app.put('/api/global-settings', async (req, res) => {
      const { setting, value } = req.body;
      
      try {
        // ローカルDBに保存
        await this.pool.query(
          'INSERT INTO global_settings (key, value, updated_at) VALUES ($1, $2, NOW()) ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()',
          [setting, value]
        );
        
        // ピアサーバーに同期（非同期）
        this.syncToPeer('/api/sync/global-settings', { setting, value })
          .catch(err => console.error('Sync failed:', err));
        
        res.json({ success: true, server: this.config.name });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
    
    // 同期エンドポイント
    this.app.post('/api/sync/global-settings', async (req, res) => {
      const { setting, value } = req.body;
      
      try {
        await this.pool.query(
          'INSERT INTO global_settings (key, value, updated_at, synced) VALUES ($1, $2, NOW(), true) ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW(), synced = true',
          [setting, value]
        );
        
        res.json({ success: true });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
    
    // メトリクスエンドポイント
    this.app.get('/api/metrics', async (req, res) => {
      const metrics = await this.collectMetrics();
      res.json({
        server: this.config.name,
        partition: this.config.partitionKey,
        ...metrics
      });
    });
  }
  
  setupHealthChecks() {
    // 自己ヘルスチェック
    this.app.get('/health', async (req, res) => {
      try {
        // DB接続確認
        await this.pool.query('SELECT 1');
        
        // ピアサーバー接続確認
        let peerStatus = 'unknown';
        try {
          const peerHealth = await axios.get(`${this.peerServer}/health`, {
            timeout: 2000
          });
          peerStatus = peerHealth.data.status;
        } catch (e) {
          peerStatus = 'unreachable';
        }
        
        res.json({
          status: 'healthy',
          server: this.config.name,
          database: 'connected',
          peer: peerStatus,
          uptime: process.uptime()
        });
      } catch (error) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message
        });
      }
    });
    
    // 相互ヘルスチェック
    setInterval(async () => {
      try {
        const health = await axios.get(`${this.peerServer}/health`, {
          timeout: 5000
        });
        
        this.peerHealthy = health.data.status === 'healthy';
      } catch (error) {
        this.peerHealthy = false;
        console.error('Peer health check failed:', error.message);
      }
    }, 10000); // 10秒ごと
  }
  
  isMyPartition(userId) {
    const firstChar = userId[0].toUpperCase();
    
    if (this.config.partitionKey === 'A-M') {
      return firstChar >= 'A' && firstChar <= 'M';
    } else if (this.config.partitionKey === 'N-Z') {
      return firstChar >= 'N' && firstChar <= 'Z';
    }
    
    return false;
  }
  
  getCorrectServer(userId) {
    return this.isMyPartition(userId) ? this.config.name : this.peerServer;
  }
  
  async getUserProfile(userId) {
    const result = await this.pool.query(
      'SELECT * FROM users WHERE user_id = $1',
      [userId]
    );
    
    if (result.rows.length === 0) {
      // 新規ユーザーの作成
      const insertResult = await this.pool.query(
        'INSERT INTO users (user_id, created_at) VALUES ($1, NOW()) RETURNING *',
        [userId]
      );
      return insertResult.rows[0];
    }
    
    return result.rows[0];
  }
  
  async queryPeerServer(path, params) {
    console.log(`Cross-server query to ${this.peerServer}${path}`);
    
    const response = await axios.get(`${this.peerServer}${path}`, {
      params,
      headers: {
        'X-User-Id': params.userId,
        'X-Requesting-Server': this.config.name
      },
      timeout: 5000
    });
    
    return response;
  }
  
  async syncToPeer(path, data) {
    if (!this.peerHealthy) {
      console.warn('Peer is unhealthy, queuing sync operation');
      await this.queueSyncOperation(path, data);
      return;
    }
    
    await axios.post(`${this.peerServer}${path}`, data, {
      headers: {
        'X-Sync-From': this.config.name
      },
      timeout: 5000
    });
  }
  
  async queueSyncOperation(path, data) {
    // 同期キューに保存（後でリトライ）
    await this.pool.query(
      'INSERT INTO sync_queue (path, data, created_at) VALUES ($1, $2, NOW())',
      [path, JSON.stringify(data)]
    );
  }
  
  async collectMetrics() {
    const result = await this.pool.query(`
      SELECT 
        (SELECT COUNT(*) FROM users) as total_users,
        (SELECT COUNT(*) FROM global_settings) as total_settings,
        (SELECT COUNT(*) FROM sync_queue WHERE processed = false) as pending_syncs
    `);
    
    return {
      ...result.rows[0],
      connections: {
        active: this.pool.totalCount,
        idle: this.pool.idleCount,
        waiting: this.pool.waitingCount
      }
    };
  }
  
  start() {
    const port = this.config.port || 3000;
    
    this.app.listen(port, () => {
      console.log(`Server ${this.config.name} (${this.config.partitionKey}) listening on port ${port}`);
      console.log(`Peer server: ${this.peerServer}`);
    });
  }
}

// 起動スクリプト
if (require.main === module) {
  const config = {
    name: process.env.SERVER_NAME || 'server-1',
    port: process.env.PORT || 3001,
    partitionKey: process.env.PARTITION_KEY || 'A-M',
    peerServer: process.env.PEER_SERVER || 'http://localhost:3002',
    database: {
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'server1_db',
      user: process.env.DB_USER || 'dbuser',
      password: process.env.DB_PASSWORD || 'dbpass'
    }
  };
  
  const server = new DualServerApplication(config);
  server.start();
}

module.exports = DualServerApplication;
```

### デプロイメント設定
```yaml
# docker-compose-server1.yml
version: '3.8'

services:
  app:
    build: .
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
    build: .
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