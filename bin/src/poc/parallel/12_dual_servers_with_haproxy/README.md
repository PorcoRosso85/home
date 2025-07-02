# 12_dual_servers_with_haproxy

## 概要

HAProxyを導入し、2台のサーバー間で自動的な負荷分散とフェイルオーバーを実現します。手動分割から自動化への重要な進化です。

## 目的

- HAProxyによる高度な負荷分散
- 自動ヘルスチェックとフェイルオーバー
- スティッキーセッションの実装
- 統計情報とリアルタイム監視

## アーキテクチャ

```
┌─────────────────────────────────┐
│         Clients (N)             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│         HAProxy                 │
│  ┌─────────────────────────┐    │
│  │ - Health Checks         │    │
│  │ - Load Balancing        │    │
│  │ - Sticky Sessions       │    │
│  │ - Stats Dashboard       │    │
│  └─────────────────────────┘    │
└────────┬───────────┬────────────┘
         │           │
    Auto │           │ Auto
         ▼           ▼
┌─────────────┐ ┌─────────────┐
│  Server-1   │ │  Server-2   │
│  Primary    │ │  Secondary  │
│             │ │             │
│ ┌─────────┐ │ │ ┌─────────┐ │
│ │ App     │ │ │ │ App     │ │
│ │ Full DB │ │ │ │ Full DB │ │
│ └─────────┘ │ │ └─────────┘ │
└─────────────┘ └─────────────┘
       │                 │
       └────────┬────────┘
                │
        [DB Replication]
```

## 検証項目

### 1. HAProxy設定
- **負荷分散アルゴリズム**: roundrobin, leastconn, source
- **ヘルスチェック**: HTTP, TCP, カスタム
- **セッション永続性**: cookie, source IP
- **SSL/TLS終端**: HTTPS対応

### 2. 高可用性機能
- **自動フェイルオーバー**: ヘルスチェック失敗時
- **グレースフル停止**: 既存接続の維持
- **バックアップサーバー**: フォールバック設定
- **リトライメカニズム**: 失敗時の再試行

### 3. 監視と統計
- **リアルタイム統計**: 接続数、転送量、エラー率
- **サーバー状態**: UP/DOWN/DRAIN
- **レスポンスタイム**: 各バックエンドの遅延
- **エラー分析**: 5xx, 4xx, タイムアウト

## TDDアプローチ

### Red Phase (HAProxy機能のテスト)
```javascript
// test/haproxy-loadbalancing.test.js
describe('HAProxy Load Balancing', () => {
  let haproxy;
  let server1, server2;
  let statsClient;
  
  beforeAll(async () => {
    // HAProxyとバックエンドサーバーの起動
    [haproxy, server1, server2] = await Promise.all([
      startHAProxy({
        config: './haproxy.cfg',
        stats: { enabled: true, port: 8404 }
      }),
      startServer({ name: 'server1', port: 3001 }),
      startServer({ name: 'server2', port: 3002 })
    ]);
    
    statsClient = new HAProxyStatsClient('http://localhost:8404');
    
    // 起動完了を待つ
    await waitForHealthy([haproxy, server1, server2]);
  });

  it('should distribute load evenly with round-robin', async () => {
    const requests = 1000;
    const responses = [];
    
    // 連続リクエストを送信
    for (let i = 0; i < requests; i++) {
      const response = await fetch('http://localhost/api/whoami');
      const data = await response.json();
      responses.push(data.server);
    }
    
    // 分散を確認
    const distribution = countBy(responses);
    
    expect(distribution.server1).toBeCloseTo(500, -1); // ±10
    expect(distribution.server2).toBeCloseTo(500, -1); // ±10
    
    // 統計情報での確認
    const stats = await statsClient.getStats();
    const backend = stats.backends.find(b => b.name === 'webservers');
    
    expect(backend.servers[0].requests).toBeCloseTo(500, -1);
    expect(backend.servers[1].requests).toBeCloseTo(500, -1);
  });

  it('should handle automatic failover', async () => {
    // 継続的なリクエスト送信
    const requestLoop = async () => {
      const results = {
        success: 0,
        failed: 0,
        servers: { server1: 0, server2: 0 }
      };
      
      for (let i = 0; i < 200; i++) {
        try {
          const response = await fetch('http://localhost/api/health', {
            timeout: 1000
          });
          
          if (response.ok) {
            const data = await response.json();
            results.success++;
            results.servers[data.server]++;
          } else {
            results.failed++;
          }
        } catch (error) {
          results.failed++;
        }
        
        await sleep(100); // 100ms間隔
      }
      
      return results;
    };
    
    // バックグラウンドでリクエスト開始
    const requestPromise = requestLoop();
    
    // 5秒後にserver1を停止
    await sleep(5000);
    console.log('Stopping server1...');
    await server1.stop();
    
    // 結果を待つ
    const results = await requestPromise;
    
    // フェイルオーバーの確認
    expect(results.success).toBeGreaterThan(195); // 97.5%以上成功
    expect(results.failed).toBeLessThan(5);
    
    // server1への初期リクエストと、停止後のserver2への移行を確認
    expect(results.servers.server1).toBeGreaterThan(40);
    expect(results.servers.server2).toBeGreaterThan(150);
    
    // HAProxy統計での確認
    const stats = await statsClient.getStats();
    const server1Stats = stats.servers.find(s => s.name === 'server1');
    
    expect(server1Stats.status).toBe('DOWN');
    expect(server1Stats.check_status).toBe('L4CON');
  });

  it('should maintain sticky sessions', async () => {
    // 10個のクライアントセッション
    const clients = Array(10).fill(0).map((_, i) => ({
      id: `client-${i}`,
      cookie: null,
      assignedServer: null,
      requests: []
    }));
    
    // 各クライアントが20リクエストを送信
    for (const client of clients) {
      for (let i = 0; i < 20; i++) {
        const response = await fetch('http://localhost/api/session', {
          headers: client.cookie ? { 'Cookie': client.cookie } : {}
        });
        
        // Set-Cookieヘッダーを保存
        const setCookie = response.headers.get('set-cookie');
        if (setCookie && !client.cookie) {
          client.cookie = setCookie.split(';')[0];
        }
        
        const data = await response.json();
        
        // 最初のサーバー割り当てを記録
        if (!client.assignedServer) {
          client.assignedServer = data.server;
        }
        
        client.requests.push({
          server: data.server,
          sessionId: data.sessionId
        });
      }
    }
    
    // 各クライアントが同じサーバーに固定されているか確認
    for (const client of clients) {
      const servers = unique(client.requests.map(r => r.server));
      expect(servers).toHaveLength(1);
      expect(servers[0]).toBe(client.assignedServer);
      
      // セッションIDも一貫しているか
      const sessionIds = unique(client.requests.map(r => r.sessionId));
      expect(sessionIds).toHaveLength(1);
    }
  });

  it('should handle connection draining', async () => {
    // 長時間実行されるリクエストを開始
    const longRequests = Array(10).fill(0).map(() => 
      fetch('http://localhost/api/long-operation', {
        method: 'POST',
        body: JSON.stringify({ duration: 10000 }) // 10秒
      })
    );
    
    // 1秒後にserver1をDRAIN状態に
    await sleep(1000);
    await statsClient.setServerState('webservers/server1', 'drain');
    
    // 新規リクエストがserver2に向かうことを確認
    const newRequests = await Promise.all(
      Array(20).fill(0).map(() => 
        fetch('http://localhost/api/whoami').then(r => r.json())
      )
    );
    
    const servers = newRequests.map(r => r.server);
    expect(servers.every(s => s === 'server2')).toBe(true);
    
    // 既存の長時間リクエストは完了することを確認
    const longResults = await Promise.all(longRequests);
    expect(longResults.every(r => r.ok)).toBe(true);
  });

  it('should enforce rate limiting', async () => {
    // レート制限の設定確認（10req/s per IP）
    const results = {
      accepted: 0,
      ratelimited: 0
    };
    
    // 2秒間で30リクエスト（15req/s）を送信
    const startTime = Date.now();
    
    while (Date.now() - startTime < 2000) {
      const response = await fetch('http://localhost/api/test');
      
      if (response.status === 429) {
        results.ratelimited++;
      } else if (response.ok) {
        results.accepted++;
      }
    }
    
    // 約20リクエストが受け入れられ、10がレート制限されるはず
    expect(results.accepted).toBeGreaterThan(18);
    expect(results.accepted).toBeLessThan(22);
    expect(results.ratelimited).toBeGreaterThan(8);
  });

  it('should provide detailed statistics', async () => {
    // 様々な種類のリクエストを生成
    const scenarios = [
      { path: '/api/fast', count: 100, expectedTime: 50 },
      { path: '/api/slow', count: 50, expectedTime: 500 },
      { path: '/api/error', count: 20, expectedStatus: 500 },
      { path: '/api/notfound', count: 10, expectedStatus: 404 }
    ];
    
    for (const scenario of scenarios) {
      await Promise.all(
        Array(scenario.count).fill(0).map(() => 
          fetch(`http://localhost${scenario.path}`)
        )
      );
    }
    
    // 統計情報を取得
    const stats = await statsClient.getDetailedStats();
    
    // フロントエンド統計
    const frontend = stats.frontends[0];
    expect(frontend.requests_total).toBe(180);
    expect(frontend.responses_2xx).toBeGreaterThan(140);
    expect(frontend.responses_4xx).toBe(10);
    expect(frontend.responses_5xx).toBe(20);
    
    // バックエンド統計
    const backend = stats.backends[0];
    expect(backend.avg_response_time).toBeGreaterThan(50);
    expect(backend.avg_response_time).toBeLessThan(200);
    
    // サーバー個別統計
    for (const server of backend.servers) {
      expect(server.status).toBe('UP');
      expect(server.health_checks.passed).toBeGreaterThan(0);
      expect(server.queue_current).toBe(0);
    }
  });
});

// 高度な設定のテスト
describe('HAProxy Advanced Features', () => {
  it('should handle SSL/TLS termination', async () => {
    const httpsResponse = await fetch('https://localhost:443/api/secure', {
      agent: new https.Agent({ rejectUnauthorized: false })
    });
    
    expect(httpsResponse.ok).toBe(true);
    
    const data = await httpsResponse.json();
    expect(data.protocol).toBe('https');
    expect(data.tls_version).toMatch(/TLSv1\.[23]/);
  });
  
  it('should apply custom routing rules', async () => {
    // パスベースルーティング
    const apiResponse = await fetch('http://localhost/api/v2/users');
    const apiData = await apiResponse.json();
    expect(apiData.server).toMatch(/^api-server/);
    
    // ホストベースルーティング
    const adminResponse = await fetch('http://admin.localhost/dashboard');
    const adminData = await adminResponse.json();
    expect(adminData.server).toBe('admin-server');
  });
});
```

### Green Phase (HAProxy設定と実装)
```
# haproxy.cfg
global
    log stdout local0
    maxconn 4096
    tune.ssl.default-dh-param 2048
    
    # 統計ソケット
    stats socket /var/run/haproxy.sock mode 600 level admin
    stats timeout 30s
    
    # マルチスレッド
    nbthread 4

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  http-server-close
    option  forwardfor except 127.0.0.0/8
    option  redispatch
    
    # タイムアウト設定
    timeout connect 5s
    timeout client  30s
    timeout server  30s
    timeout http-request 10s
    timeout queue   30s
    timeout http-keep-alive 5s
    
    # エラーページ
    errorfile 503 /etc/haproxy/errors/503.http

# 統計情報ダッシュボード
stats enable
stats uri /stats
stats realm HAProxy\ Statistics
stats auth admin:admin
stats refresh 5s

# フロントエンド定義
frontend web_frontend
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/server.pem
    
    # HTTPSリダイレクト
    redirect scheme https if !{ ssl_fc }
    
    # レート制限（10req/s per IP）
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    tcp-request connection track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 10 }
    
    # リクエストヘッダー追加
    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    http-request set-header X-Real-IP %[src]
    
    # ACLによるルーティング
    acl is_api path_beg /api/v2
    acl is_admin hdr(host) -i admin.localhost
    acl is_websocket hdr(Upgrade) -i WebSocket
    
    # バックエンド選択
    use_backend api_servers if is_api
    use_backend admin_server if is_admin
    use_backend websocket_servers if is_websocket
    default_backend webservers

# メインバックエンド
backend webservers
    balance roundrobin
    
    # スティッキーセッション
    cookie SERVERID insert indirect nocache
    
    # ヘルスチェック
    option httpchk GET /health HTTP/1.1\r\nHost:\ localhost
    http-check expect status 200
    
    # サーバー定義
    server server1 server1:3001 check inter 2s fall 3 rise 2 cookie server1 maxconn 100
    server server2 server2:3002 check inter 2s fall 3 rise 2 cookie server2 maxconn 100
    
    # バックアップサーバー
    server backup backup-server:3003 backup check

# APIサーバー用バックエンド
backend api_servers
    balance leastconn
    
    # リトライ設定
    retry-on conn-failure empty-response response-timeout
    retries 3
    
    server api1 api-server1:4001 check
    server api2 api-server2:4002 check

# 管理サーバー
backend admin_server
    # 単一サーバー
    server admin admin-server:5001 check

# WebSocketバックエンド
backend websocket_servers
    balance source  # IPハッシュ
    
    # WebSocket特有の設定
    timeout tunnel 1h
    
    server ws1 ws-server1:6001 check
    server ws2 ws-server2:6002 check

# カスタムエラーレスポンス
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 5s
    stats show-legends
    stats show-node
    stats admin if TRUE
```

```javascript
// haproxy-backend-app.js
const express = require('express');
const session = require('express-session');
const app = express();

const SERVER_NAME = process.env.SERVER_NAME || 'server1';
const PORT = process.env.PORT || 3001;

// セッション設定
app.use(session({
  secret: 'haproxy-test-secret',
  resave: false,
  saveUninitialized: true,
  cookie: { 
    secure: false,
    httpOnly: true,
    maxAge: 3600000 // 1時間
  }
}));

app.use(express.json());

// ロギングミドルウェア
app.use((req, res, next) => {
  console.log(`[${SERVER_NAME}] ${req.method} ${req.path} - Session: ${req.sessionID}`);
  next();
});

// ヘルスチェックエンドポイント
app.get('/health', (req, res) => {
  // HAProxyのヘルスチェックに応答
  res.status(200).send('OK');
});

// サーバー識別エンドポイント
app.get('/api/whoami', (req, res) => {
  res.json({
    server: SERVER_NAME,
    timestamp: new Date().toISOString(),
    headers: req.headers
  });
});

// セッションテスト
app.get('/api/session', (req, res) => {
  if (!req.session.visits) {
    req.session.visits = 0;
  }
  
  req.session.visits++;
  
  res.json({
    server: SERVER_NAME,
    sessionId: req.sessionID,
    visits: req.session.visits,
    created: req.session.cookie._expires
  });
});

// 長時間実行オペレーション
app.post('/api/long-operation', async (req, res) => {
  const duration = req.body.duration || 5000;
  
  console.log(`[${SERVER_NAME}] Starting long operation (${duration}ms)`);
  
  // グレースフルシャットダウンのテスト用
  await new Promise(resolve => setTimeout(resolve, duration));
  
  res.json({
    server: SERVER_NAME,
    duration,
    completed: true
  });
});

// パフォーマンステスト用エンドポイント
app.get('/api/fast', (req, res) => {
  res.json({ server: SERVER_NAME, type: 'fast' });
});

app.get('/api/slow', async (req, res) => {
  await new Promise(resolve => setTimeout(resolve, 400 + Math.random() * 200));
  res.json({ server: SERVER_NAME, type: 'slow' });
});

app.get('/api/error', (req, res) => {
  res.status(500).json({ error: 'Simulated error', server: SERVER_NAME });
});

// グレースフルシャットダウン
let isShuttingDown = false;

process.on('SIGTERM', () => {
  console.log(`[${SERVER_NAME}] SIGTERM received, starting graceful shutdown`);
  isShuttingDown = true;
  
  // 新規リクエストを拒否
  app.use((req, res, next) => {
    if (isShuttingDown) {
      res.status(503).send('Server is shutting down');
      return;
    }
    next();
  });
  
  // 30秒後に強制終了
  setTimeout(() => {
    console.log(`[${SERVER_NAME}] Forcing shutdown`);
    process.exit(0);
  }, 30000);
});

// サーバー起動
const server = app.listen(PORT, () => {
  console.log(`[${SERVER_NAME}] Server listening on port ${PORT}`);
});

// Keep-Alive設定
server.keepAliveTimeout = 65000;
server.headersTimeout = 66000;
```

### Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  haproxy:
    image: haproxy:2.8-alpine
    ports:
      - "80:80"
      - "443:443"
      - "8404:8404"  # Stats
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - ./certs:/etc/haproxy/certs:ro
      - ./errors:/etc/haproxy/errors:ro
    depends_on:
      - server1
      - server2
    sysctls:
      - net.ipv4.ip_unprivileged_port_start=0
    networks:
      - backend

  server1:
    build: .
    environment:
      SERVER_NAME: server1
      PORT: 3001
    expose:
      - "3001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - backend

  server2:
    build: .
    environment:
      SERVER_NAME: server2
      PORT: 3002
    expose:
      - "3002"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - backend

  # バックアップサーバー
  backup-server:
    build: .
    environment:
      SERVER_NAME: backup
      PORT: 3003
    expose:
      - "3003"
    networks:
      - backend

  # モニタリング
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - backend

networks:
  backend:
    driver: bridge
```

## 実行と監視

### 1. システム起動
```bash
# SSL証明書の生成
./scripts/generate-certs.sh

# 起動
docker-compose up -d

# ヘルスチェック
./scripts/wait-for-healthy.sh
```

### 2. HAProxy統計ダッシュボード
```bash
# ブラウザで開く
open http://localhost:8404/stats

# CLIでの確認
echo "show stat" | socat unix-connect:/var/run/haproxy.sock stdio
```

### 3. 負荷テストとモニタリング
```bash
# 負荷テスト実行
npm run loadtest:haproxy

# リアルタイムログ
docker-compose logs -f haproxy

# メトリクス確認
curl -s http://localhost:8404/stats?json | jq
```

## 成功基準

- [ ] 自動負荷分散の実現（誤差5%以内）
- [ ] 3秒以内の自動フェイルオーバー
- [ ] スティッキーセッションの100%維持
- [ ] 99.9%以上の可用性
- [ ] リアルタイム統計の提供

## 運用ガイド

### メンテナンスモード
```bash
# サーバーをDRAIN状態に
echo "set server webservers/server1 state drain" | \
  socat unix-connect:/var/run/haproxy.sock stdio

# メンテナンス完了後
echo "set server webservers/server1 state ready" | \
  socat unix-connect:/var/run/haproxy.sock stdio
```

### 動的な重み変更
```bash
# server2の重みを増やす
echo "set weight webservers/server2 200" | \
  socat unix-connect:/var/run/haproxy.sock stdio
```

### 設定のリロード
```bash
# 設定ファイルの検証
docker-compose exec haproxy haproxy -f /usr/local/etc/haproxy/haproxy.cfg -c

# ゼロダウンタイムリロード
docker-compose exec haproxy kill -USR2 1
```

## トラブルシューティング

### 問題: 503エラーが頻発
```bash
# バックエンドサーバーの状態確認
echo "show servers state" | socat unix-connect:/var/run/haproxy.sock stdio

# ヘルスチェックログ
docker-compose logs haproxy | grep "Health check"
```

### 問題: セッションが維持されない
```
# Cookieの確認
curl -v http://localhost/api/session | grep -i cookie

# スティッキーテーブルの確認
echo "show table" | socat unix-connect:/var/run/haproxy.sock stdio
```

## 次のステップ

HAProxyでの自動化を確立後、`13_triple_servers_consistent_hash`で3台以上のサーバーでConsistent Hashingを実装します。

## 学んだこと

- エンタープライズグレードの負荷分散
- 自動フェイルオーバーの威力
- 統計情報による可視化の重要性
- 設定の柔軟性と複雑性のバランス

## 参考資料

- [HAProxy Documentation](http://www.haproxy.org/#docs)
- [HAProxy Best Practices](https://www.haproxy.com/blog/haproxy-configuration-basics-load-balance-your-servers/)
- [Load Balancing Algorithms](https://www.haproxy.com/blog/load-balancing-algorithms/)
- [HAProxy Statistics](https://www.haproxy.com/blog/exploring-the-haproxy-stats-page/)