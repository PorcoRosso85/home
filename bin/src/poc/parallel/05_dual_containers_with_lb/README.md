# 05_dual_containers_with_lb

## 概要

2つのアプリケーションコンテナとロードバランサーを導入し、単一サーバー内での水平スケーリングを実現します。Phase 1で特定した限界を、ソフトウェアレベルのスケールアウトで克服します。

## 目的

- 単一サーバー内での負荷分散の実装
- ロードバランサーの効果測定
- フェイルオーバー機能の検証
- セッション管理戦略の確立

## アーキテクチャ

```
┌─────────────────────────────────┐
│         Clients (N)             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│     Nginx Load Balancer         │
│  ┌─────────────────────────┐    │
│  │ - Round Robin           │    │
│  │ - Health Checks         │    │
│  │ - Sticky Sessions       │    │
│  │ - Connection Pooling    │    │
│  └─────────────────────────┘    │
└─────────┬─────────────┬─────────┘
          │             │
          ▼             ▼
┌─────────────┐   ┌─────────────┐
│   App-1     │   │   App-2     │
│  Port:3001  │   │  Port:3002  │
│             │   │             │
│ [Isolated]  │   │ [Isolated]  │
└─────────────┘   └─────────────┘
        │                 │
        └────────┬────────┘
                 ▼
         [Shared Resources]
         - File System
         - Network Stack
         - CPU/Memory Pool
```

## 検証項目

### 1. 負荷分散の効率性
- **分散の均等性**: 50/50の理想的な分散
- **レスポンス改善**: 単一コンテナ比で2倍のスループット
- **リソース利用率**: 各コンテナのバランスの取れた使用
- **スケール効果**: 線形に近いスケーリング

### 2. 高可用性の実現
- **自動フェイルオーバー**: 1コンテナ停止時の無停止切替
- **ヘルスチェック**: 異常検出から除外までの時間
- **復旧の自動化**: 回復したコンテナの自動組み込み
- **グレースフルシャットダウン**: 既存接続の適切な処理

### 3. 運用上の課題
- **セッション管理**: スティッキーセッションの実装
- **ログの統合**: 複数コンテナからのログ集約
- **メトリクスの集計**: 分散したメトリクスの統合
- **デプロイ戦略**: ローリングアップデートの実現

## TDDアプローチ

### Red Phase (分散システムのテスト)
```typescript
// test/dual-container-lb.test.ts
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { LoadBalancerTester, ContainerController } from "../src/test-utils.ts";

Deno.test("Dual Containers with Load Balancer", async (t) => {
  let loadBalancer: LoadBalancerTester;
  let containers: { app1: ContainerController; app2: ContainerController };
  
  // Setup
  // コンテナとLBの起動を待つ
  await waitForHealthy(['http://localhost:3001', 'http://localhost:3002']);
  
  loadBalancer = new LoadBalancerTester({
    url: 'http://localhost',
    expectedBackends: ['app-1:3001', 'app-2:3002']
  });
  
  containers = {
    app1: new ContainerController('app-1'),
    app2: new ContainerController('app-2')
  };

  await t.step("should distribute load evenly between containers", async () => {
    const requests = 1000;
    const results = {
      'app-1': 0,
      'app-2': 0
    };
    
    // 並列でリクエストを送信
    const promises = Array(requests).fill(0).map(async () => {
      const response = await fetch('http://localhost/api/whoami');
      const data = await response.json();
      results[data.container]++;
      return data;
    });
    
    await Promise.all(promises);
    
    // 分散の均等性を検証（±5%の誤差を許容）
    const distribution = {
      app1: results['app-1'] / requests,
      app2: results['app-2'] / requests
    };
    
    assertEquals(Math.abs(distribution.app1 - 0.5) < 0.1, true);
    assertEquals(Math.abs(distribution.app2 - 0.5) < 0.1, true);
    
    // カイ二乗検定で分散の均等性を統計的に検証
    const chiSquare = calculateChiSquare(results, requests / 2);
    assertEquals(chiSquare < 3.841, true); // 95%信頼度
  });

  await t.step("should handle container failure gracefully", async () => {
    const testDuration = 30000; // 30秒
    const metricsCollector = new MetricsCollector();
    
    // バックグラウンドで継続的にリクエストを送信
    const loadGenerator = startContinuousLoad({
      rps: 100,
      duration: testDuration,
      onResponse: (res) => metricsCollector.record(res)
    });
    
    // 10秒後に1つのコンテナを停止
    setTimeout(async () => {
      console.log('Stopping app-1 container...');
      await containers.app1.stop();
    }, 10000);
    
    // 20秒後にコンテナを再起動
    setTimeout(async () => {
      console.log('Restarting app-1 container...');
      await containers.app1.start();
    }, 20000);
    
    // テスト完了を待つ
    await loadGenerator.wait();
    
    const analysis = metricsCollector.analyze();
    
    // フェイルオーバー中もエラー率が低いこと
    assertEquals(analysis.errorRate < 0.01, true); // 1%未満
    
    // 停止期間中もスループットが維持されること
    assertEquals(analysis.minThroughput > 80, true); // 80 rps以上
    
    // 復旧後に負荷が再分散されること
    const postRecoveryDistribution = analysis.getDistributionAfter(25000);
    assertEquals(postRecoveryDistribution['app-1'] > 0.3, true);
    assertEquals(postRecoveryDistribution['app-2'] < 0.7, true);
  });

  await t.step("should maintain session affinity", async () => {
    const sessions = {};
    const numClients = 50;
    const requestsPerClient = 20;
    
    // 各クライアントが複数のリクエストを送信
    const clientPromises = Array(numClients).fill(0).map(async (_, clientId) => {
      const cookieJar = new CookieJar();
      sessions[clientId] = {
        servers: new Set(),
        requests: []
      };
      
      for (let i = 0; i < requestsPerClient; i++) {
        const response = await fetchWithCookies('http://localhost/api/session', {
          cookieJar,
          method: 'POST',
          body: JSON.stringify({ clientId, requestNum: i })
        });
        
        const data = await response.json();
        sessions[clientId].servers.add(data.container);
        sessions[clientId].requests.push(data);
      }
    });
    
    await Promise.all(clientPromises);
    
    // 各クライアントが同じサーバーに固定されていることを確認
    const stickySuccess = Object.values(sessions).filter(
      session => session.servers.size === 1
    ).length;
    
    assertEquals(stickySuccess / numClients > 0.95, true); // 95%以上が成功
  });

  await t.step("should scale performance linearly", async () => {
    // 単一コンテナのベースライン（Phase 1の結果を使用）
    const singleContainerBaseline = {
      throughput: 1000, // req/s
      p95Latency: 200,  // ms
      maxClients: 800
    };
    
    // 2コンテナでの性能測定
    const dualContainerResults = await runPerformanceTest({
      duration: 60000,
      targetRPS: 2000,
      maxClients: 1600
    });
    
    // スケーリング効率の計算
    const scalingEfficiency = {
      throughput: dualContainerResults.throughput / (singleContainerBaseline.throughput * 2),
      clients: dualContainerResults.maxClients / (singleContainerBaseline.maxClients * 2),
      latency: singleContainerBaseline.p95Latency / dualContainerResults.p95Latency
    };
    
    // 80%以上の効率を期待
    assertEquals(scalingEfficiency.throughput > 0.8, true);
    assertEquals(scalingEfficiency.clients > 0.8, true);
    assertEquals(scalingEfficiency.latency > 0.8, true);
  });
});

// ヘルパー関数
function calculateChiSquare(observed, expected) {
  let sum = 0;
  Object.values(observed).forEach(count => {
    sum += Math.pow(count - expected, 2) / expected;
  });
  return sum;
}

class MetricsCollector {
  constructor() {
    this.metrics = [];
  }
  
  record(response) {
    this.metrics.push({
      timestamp: Date.now(),
      status: response.status,
      container: response.headers.get('X-Container-Id'),
      latency: response.latency,
      error: response.status >= 500
    });
  }
  
  analyze() {
    const windows = this.getTimeWindows();
    
    return {
      errorRate: this.calculateErrorRate(),
      minThroughput: Math.min(...windows.map(w => w.throughput)),
      getDistributionAfter: (time) => this.getDistribution(time)
    };
  }
  
  getDistribution(afterTime) {
    const relevantMetrics = this.metrics.filter(m => m.timestamp > afterTime);
    const counts = {};
    
    relevantMetrics.forEach(m => {
      counts[m.container] = (counts[m.container] || 0) + 1;
    });
    
    const total = relevantMetrics.length;
    const distribution = {};
    
    Object.entries(counts).forEach(([container, count]) => {
      distribution[container] = count / total;
    });
    
    return distribution;
  }
}
```

### Green Phase (ロードバランサーと2コンテナの実装)
```nginx
// nginx.conf
upstream backend {
    # IPハッシュによるセッション維持
    ip_hash;
    
    # バックエンドサーバー
    server app-1:3001 max_fails=3 fail_timeout=30s;
    server app-2:3002 max_fails=3 fail_timeout=30s;
    
    # 接続プーリング
    keepalive 32;
}

server {
    listen 80;
    
    # ヘルスチェックエンドポイント
    location /health {
        access_log off;
        return 200 "healthy\n";
    }
    
    # アプリケーションへのプロキシ
    location / {
        proxy_pass http://backend;
        
        # ヘッダー設定
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Container-Id $upstream_addr;
        
        # タイムアウト設定
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # バッファリング設定
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # Keep-Alive設定
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        # エラー時の次のサーバーへのフェイルオーバー
        proxy_next_upstream error timeout http_500 http_502 http_503;
        proxy_next_upstream_tries 2;
        proxy_next_upstream_timeout 10s;
    }
    
    # メトリクスエンドポイント
    location /nginx-metrics {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
```

```typescript
// app.ts - 改良されたアプリケーション
import { Application, Router } from "https://deno.land/x/oak@v12.6.1/mod.ts";

const app = new Application();
const router = new Router();
const CONTAINER_ID = Deno.env.get("CONTAINER_ID") || 'unknown';
const PORT = parseInt(Deno.env.get("PORT") || '3001');

// グレースフルシャットダウンのサポート
let isShuttingDown = false;

// セッション管理（簡易実装）
const sessions = new Map();

// ミドルウェア
app.use(async (ctx, next) => {
  if (isShuttingDown) {
    ctx.response.headers.set('Connection', 'close');
    ctx.response.status = 503;
    ctx.response.body = 'Server is shutting down';
    return;
  }
  await next();
});

// ヘルスチェックエンドポイント
router.get('/health', (ctx) => {
  if (isShuttingDown) {
    ctx.response.status = 503;
    ctx.response.body = { status: 'shutting_down' };
    return;
  }
  
  ctx.response.body = {
    status: 'healthy',
    container: CONTAINER_ID,
    uptime: performance.now() / 1000,
    memory: Deno.memoryUsage()
  };
});

// コンテナ識別エンドポイント
router.get('/api/whoami', (ctx) => {
  ctx.response.body = {
    container: CONTAINER_ID,
    pid: Deno.pid,
    hostname: Deno.hostname(),
    timestamp: Date.now()
  };
});

// セッション管理エンドポイント
router.post('/api/session', async (ctx) => {
  const sessionId = ctx.request.headers.get('x-session-id') || generateSessionId();
  const body = await ctx.request.body({ type: 'json' }).value;
  const { clientId, requestNum } = body;
  
  // セッションデータの保存/更新
  if (!sessions.has(sessionId)) {
    sessions.set(sessionId, {
      clientId,
      container: CONTAINER_ID,
      created: Date.now(),
      requests: []
    });
  }
  
  const session = sessions.get(sessionId);
  session.requests.push({
    requestNum,
    timestamp: Date.now()
  });
  
  ctx.response.headers.set('X-Session-Id', sessionId);
  ctx.response.body = {
    sessionId,
    container: CONTAINER_ID,
    requestCount: session.requests.length
  };
});

// パフォーマンステスト用エンドポイント
router.get('/api/load-test', (ctx) => {
  // CPUバウンドな処理をシミュレート
  const iterations = parseInt(ctx.request.url.searchParams.get('iterations') || '1000');
  let result = 0;
  
  for (let i = 0; i < iterations; i++) {
    result += Math.sqrt(i);
  }
  
  ctx.response.body = {
    container: CONTAINER_ID,
    result,
    processingTime: iterations
  };
});

// グレースフルシャットダウン
const abortController = new AbortController();

Deno.addSignalListener("SIGTERM", () => {
  console.log('SIGTERM received, starting graceful shutdown...');
  isShuttingDown = true;
  
  // 新規接続の受付を停止
  abortController.abort();
  
  // アクティブな接続の完了を待つ
  setTimeout(() => {
    console.log('Forcing shutdown...');
    Deno.exit(0);
  }, 30000); // 最大30秒待つ
});

app.use(router.routes());
app.use(router.allowedMethods());

console.log(`Container ${CONTAINER_ID} listening on port ${PORT}`);
await app.listen({ port: PORT, signal: abortController.signal });

function generateSessionId() {
  return `${CONTAINER_ID}-${Date.now()}-${crypto.randomUUID().substring(0, 8)}`;
}
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
RUN deno cache app.ts

EXPOSE 3000

CMD ["deno", "run", "--allow-net", "--allow-env", "--allow-hrtime", "app.ts"]
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
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  app-1:
    build: .
    environment:
      CONTAINER_ID: app-1
      PORT: 3001
      NODE_ENV: production
    expose:
      - "3001"
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  app-2:
    build: .
    environment:
      CONTAINER_ID: app-2
      PORT: 3002
      NODE_ENV: production
    expose:
      - "3002"
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  # メトリクス収集
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

## 実行手順

### 1. 環境準備
```bash
# Nginxコンフィグの検証
nginx -t -c nginx.conf

# コンテナのビルドと起動
docker-compose build
docker-compose up -d

# ヘルスチェック
./scripts/wait-for-healthy.sh
```

### 2. テスト実行
```bash
# 単体テスト
deno test --allow-all test/

# 負荷分散テスト
deno run --allow-all scripts/test-load-distribution.ts

# フェイルオーバーテスト
deno run --allow-all scripts/test-failover.ts

# 性能テスト
deno run --allow-all scripts/test-performance.ts
```

### 3. モニタリング
```bash
# リアルタイムログ
docker-compose logs -f

# Nginxステータス
watch -n 1 'curl -s http://localhost/nginx-metrics'

# アプリケーションメトリクス
curl http://localhost/api/metrics | jq
```

## 運用シナリオ

### ローリングアップデート
```bash
#!/bin/bash
# rolling-update.sh

echo "Starting rolling update..."

# App-1を更新
docker-compose stop app-1
docker-compose build app-1
docker-compose up -d app-1

# ヘルスチェックを待つ
./wait-for-healthy.sh app-1

# App-2を更新
docker-compose stop app-2
docker-compose build app-2
docker-compose up -d app-2

echo "Rolling update completed"
```

### 障害シミュレーション
```bash
# 1つのコンテナを強制停止
docker-compose kill app-1

# ログで挙動を確認
docker-compose logs -f nginx

# 復旧
docker-compose up -d app-1
```

## 成功基準

- [ ] 2つのコンテナへの均等な負荷分散（誤差5%以内）
- [ ] 1コンテナ障害時のゼロダウンタイム
- [ ] 単一コンテナ比で1.8倍以上のスループット
- [ ] セッションアフィニティの95%以上の成功率
- [ ] 5秒以内のフェイルオーバー完了

## トラブルシューティング

### 問題: 負荷が偏る
```nginx
# least_connに変更
upstream backend {
    least_conn;
    server app-1:3001;
    server app-2:3002;
}
```

### 問題: セッションが維持されない
```typescript
// Redisベースのセッション共有を実装
import { connect } from "https://deno.land/x/redis@v0.29.0/mod.ts";

const redis = await connect({
  hostname: "redis",
  port: 6379,
});
```

### 問題: ヘルスチェックが頻繁に失敗
```nginx
# タイムアウトを調整
upstream backend {
    server app-1:3001 max_fails=5 fail_timeout=60s;
}
```

## 次のステップ

2コンテナでの成功を確認後、`06_quad_containers_with_lb`で4コンテナに拡張し、より高度な負荷分散戦略を検証します。

## 学んだこと

- ロードバランサーによる透過的な負荷分散
- ヘルスチェックとフェイルオーバーの重要性
- セッション管理の複雑さ
- 水平スケーリングの効果と限界

## 参考資料

- [NGINX Load Balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- [Deno Deploy](https://deno.com/deploy)
- [High Availability Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/)