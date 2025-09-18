# 09_container_service_mesh

## 概要

サービスメッシュパターンを導入し、コンテナ間の高度な通信制御、観測性、セキュリティを実現します。Envoy/Linkerdの軽量版を単一サーバー内で実装します。

## 目的

- サイドカープロキシパターンの実装
- サービス間通信の可視化
- 自動リトライとサーキットブレーカー
- 分散トレーシングの基礎

## アーキテクチャ

```
┌─────────────────────────────────┐
│         Clients (N)             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│      Ingress Gateway            │
│        (Envoy/Nginx)            │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┬────────┬────────┐
    │                 │        │        │
┌───▼───┐       ┌────▼──┐ ┌──▼───┐ ┌──▼───┐
│ App-1 │       │ App-2 │ │App-3 │ │App-4 │
│       │       │       │ │      │ │      │
│Sidecar│       │Sidecar│ │Side- │ │Side- │
│ Proxy │       │ Proxy │ │ car  │ │ car  │
└───┬───┘       └───┬───┘ └──┬───┘ └──┬───┘
    │               │         │        │
    └───────┬───────┴─────────┴────────┘
            │
    ┌───────▼────────┐
    │  Control Plane │
    │                │
    │ - Discovery   │
    │ - Config      │
    │ - Telemetry   │
    └────────────────┘
```

## 検証項目

### 1. サービスディスカバリー
- **動的エンドポイント登録**: サービスの自動登録/削除
- **ヘルスチェック統合**: 不健全なインスタンスの除外
- **負荷分散の高度化**: レイテンシベースルーティング
- **A/Bテストサポート**: トラフィック分割

### 2. 回復力パターン
- **自動リトライ**: 一時的エラーの透過的処理
- **サーキットブレーカー**: カスケード障害の防止
- **タイムアウト管理**: 階層的タイムアウト
- **バルクヘッド**: リソース隔離

### 3. 観測性
- **分散トレーシング**: リクエストの経路追跡
- **メトリクス収集**: RED（Rate/Error/Duration）
- **ログ相関**: トレースIDによる統合
- **サービスマップ**: 依存関係の可視化

## TDDアプローチ

### Red Phase (サービスメッシュ機能のテスト)
```javascript
// test/service-mesh.test.js
describe('Service Mesh Functionality', () => {
  let mesh;
  let services;
  
  beforeAll(async () => {
    mesh = new ServiceMeshController({
      controlPlane: 'http://localhost:15000',
      dataPlane: 'http://localhost:15001'
    });
    
    services = {
      frontend: new ServiceProxy('frontend', 3001),
      backend: new ServiceProxy('backend', 3002),
      database: new ServiceProxy('database', 3003),
      cache: new ServiceProxy('cache', 3004)
    };
    
    await mesh.waitForReady();
  });

  it('should automatically discover and register services', async () => {
    // サービスの自動登録確認
    const registry = await mesh.getServiceRegistry();
    
    expect(registry.services).toHaveLength(4);
    expect(registry.services.map(s => s.name)).toEqual(
      expect.arrayContaining(['frontend', 'backend', 'database', 'cache'])
    );
    
    // 各サービスのエンドポイント確認
    for (const service of registry.services) {
      expect(service.endpoints).toHaveLength(1);
      expect(service.endpoints[0].status).toBe('healthy');
    }
    
    // 新サービス追加時の自動検出
    const newService = new ServiceProxy('analytics', 3005);
    await newService.start();
    
    // 検出を待つ
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const updatedRegistry = await mesh.getServiceRegistry();
    expect(updatedRegistry.services).toHaveLength(5);
  });

  it('should implement circuit breaker pattern', async () => {
    // バックエンドサービスを不安定にする
    await services.backend.simulateErrors({
      errorRate: 0.8, // 80%エラー
      duration: 10000
    });
    
    const results = [];
    
    // 50リクエストを送信
    for (let i = 0; i < 50; i++) {
      const start = Date.now();
      try {
        const response = await fetch('http://localhost/frontend/api/data');
        results.push({
          status: response.status,
          latency: Date.now() - start,
          circuitOpen: response.headers.get('X-Circuit-Status') === 'open'
        });
      } catch (error) {
        results.push({
          status: 'error',
          latency: Date.now() - start,
          error: error.message
        });
      }
      
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // サーキットブレーカーの動作確認
    const circuitOpenIndex = results.findIndex(r => r.circuitOpen);
    expect(circuitOpenIndex).toBeGreaterThan(5); // 数回失敗後に開く
    expect(circuitOpenIndex).toBeLessThan(15); // 早期に開く
    
    // サーキット開放後は高速失敗
    const afterOpen = results.slice(circuitOpenIndex);
    const fastFailures = afterOpen.filter(r => r.latency < 10);
    expect(fastFailures.length / afterOpen.length).toBeGreaterThan(0.8);
  });

  it('should provide distributed tracing', async () => {
    // トレース対応リクエスト
    const traceId = generateTraceId();
    
    const response = await fetch('http://localhost/frontend/api/complex', {
      headers: {
        'X-Trace-Id': traceId,
        'X-Span-Id': generateSpanId()
      }
    });
    
    expect(response.ok).toBe(true);
    
    // トレース情報の取得
    await new Promise(resolve => setTimeout(resolve, 1000)); // 収集待ち
    
    const trace = await mesh.getTrace(traceId);
    
    expect(trace.spans).toHaveLength(4); // frontend -> backend -> database & cache
    
    // スパンの階層構造確認
    const rootSpan = trace.spans.find(s => !s.parentId);
    expect(rootSpan.service).toBe('frontend');
    
    const backendSpan = trace.spans.find(s => s.service === 'backend');
    expect(backendSpan.parentId).toBe(rootSpan.id);
    
    // レイテンシ分析
    const totalLatency = rootSpan.duration;
    const backendLatency = backendSpan.duration;
    const networkOverhead = totalLatency - backendLatency;
    
    expect(networkOverhead).toBeLessThan(totalLatency * 0.2); // 20%以下
  });

  it('should implement intelligent load balancing', async () => {
    // 異なるレイテンシを持つバックエンドインスタンス
    const backends = [
      new ServiceProxy('backend-1', 4001, { latency: 10 }),
      new ServiceProxy('backend-2', 4002, { latency: 50 }),
      new ServiceProxy('backend-3', 4003, { latency: 100 })
    ];
    
    await Promise.all(backends.map(b => b.start()));
    
    // P2C（Power of Two Choices）アルゴリズムを有効化
    await mesh.setLoadBalancingPolicy('backend', 'p2c');
    
    // 1000リクエストの分散を測定
    const distribution = { 'backend-1': 0, 'backend-2': 0, 'backend-3': 0 };
    
    for (let i = 0; i < 1000; i++) {
      const response = await fetch('http://localhost/api/backend/health');
      const instance = response.headers.get('X-Instance-Id');
      distribution[instance]++;
    }
    
    // 低レイテンシインスタンスにより多くのトラフィック
    expect(distribution['backend-1']).toBeGreaterThan(500);
    expect(distribution['backend-2']).toBeLessThan(300);
    expect(distribution['backend-3']).toBeLessThan(200);
  });

  it('should support canary deployments', async () => {
    // カナリアデプロイメント設定
    await mesh.configureCanary('backend', {
      stable: { version: 'v1', weight: 90 },
      canary: { version: 'v2', weight: 10 }
    });
    
    const versions = { v1: 0, v2: 0 };
    
    // 1000リクエストでバージョン分布を確認
    for (let i = 0; i < 1000; i++) {
      const response = await fetch('http://localhost/api/backend/version');
      const version = await response.text();
      versions[version]++;
    }
    
    // 設定通りの分布（±5%の誤差許容）
    expect(versions.v1).toBeGreaterThan(850);
    expect(versions.v1).toBeLessThan(950);
    expect(versions.v2).toBeGreaterThan(50);
    expect(versions.v2).toBeLessThan(150);
  });
});

// メトリクス収集テスト
describe('Service Mesh Observability', () => {
  it('should collect RED metrics', async () => {
    // 様々なパターンのリクエスト生成
    const scenarios = [
      { count: 100, path: '/api/fast', expectedLatency: 10 },
      { count: 50, path: '/api/slow', expectedLatency: 500 },
      { count: 20, path: '/api/error', expectedStatus: 500 }
    ];
    
    for (const scenario of scenarios) {
      const promises = Array(scenario.count).fill(0).map(() =>
        fetch(`http://localhost${scenario.path}`)
      );
      await Promise.all(promises);
    }
    
    // メトリクス取得
    const metrics = await mesh.getMetrics('frontend', {
      window: '1m',
      granularity: '10s'
    });
    
    // Rate（スループット）
    expect(metrics.rate).toBeGreaterThan(2); // req/s
    
    // Errors（エラー率）
    const expectedErrorRate = 20 / 170; // 20 errors out of 170 total
    expect(metrics.errorRate).toBeCloseTo(expectedErrorRate, 2);
    
    // Duration（レイテンシ）
    expect(metrics.p50Latency).toBeLessThan(50);
    expect(metrics.p99Latency).toBeGreaterThan(400);
  });
});
```

### Green Phase (サービスメッシュの実装)
```javascript
// sidecar-proxy.js
const express = require('express');
const httpProxy = require('http-proxy-middleware');
const CircuitBreaker = require('opossum');

class SidecarProxy {
  constructor(serviceName, servicePort, meshConfig) {
    this.serviceName = serviceName;
    this.servicePort = servicePort;
    this.meshConfig = meshConfig;
    this.app = express();
    this.proxy = null;
    this.circuits = new Map();
    this.metrics = {
      requests: 0,
      errors: 0,
      latencies: []
    };
  }
  
  initialize() {
    // Prometheus形式のメトリクス
    this.app.get('/metrics', (req, res) => {
      res.set('Content-Type', 'text/plain');
      res.send(this.generateMetrics());
    });
    
    // ヘルスチェック
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        service: this.serviceName,
        uptime: process.uptime()
      });
    });
    
    // トレーシングミドルウェア
    this.app.use(this.tracingMiddleware.bind(this));
    
    // サーキットブレーカー付きプロキシ
    this.setupProxy();
    
    // メトリクス収集
    this.app.use(this.metricsMiddleware.bind(this));
  }
  
  tracingMiddleware(req, res, next) {
    // トレースコンテキストの伝播
    const traceId = req.headers['x-trace-id'] || this.generateTraceId();
    const parentSpanId = req.headers['x-span-id'];
    const spanId = this.generateSpanId();
    
    req.traceContext = {
      traceId,
      parentSpanId,
      spanId,
      startTime: Date.now()
    };
    
    // ヘッダーに追加
    req.headers['x-trace-id'] = traceId;
    req.headers['x-span-id'] = spanId;
    
    // レスポンス時にスパン情報を送信
    res.on('finish', () => {
      this.sendSpan({
        traceId,
        spanId,
        parentSpanId,
        service: this.serviceName,
        operation: `${req.method} ${req.path}`,
        startTime: req.traceContext.startTime,
        duration: Date.now() - req.traceContext.startTime,
        statusCode: res.statusCode,
        error: res.statusCode >= 400
      });
    });
    
    next();
  }
  
  metricsMiddleware(req, res, next) {
    const start = Date.now();
    
    res.on('finish', () => {
      const duration = Date.now() - start;
      this.metrics.requests++;
      
      if (res.statusCode >= 500) {
        this.metrics.errors++;
      }
      
      this.metrics.latencies.push(duration);
      
      // 最新1000件のみ保持
      if (this.metrics.latencies.length > 1000) {
        this.metrics.latencies.shift();
      }
    });
    
    next();
  }
  
  setupProxy() {
    // アップストリーム設定
    const upstreams = this.meshConfig.getUpstreams(this.serviceName);
    
    for (const upstream of upstreams) {
      // 各アップストリームにサーキットブレーカーを設定
      const circuit = new CircuitBreaker(
        this.createProxyFunction(upstream),
        {
          timeout: 3000,
          errorThresholdPercentage: 50,
          resetTimeout: 30000,
          rollingCountTimeout: 10000
        }
      );
      
      circuit.on('open', () => {
        console.log(`Circuit opened for ${upstream.name}`);
      });
      
      circuit.on('halfOpen', () => {
        console.log(`Circuit half-open for ${upstream.name}`);
      });
      
      this.circuits.set(upstream.name, circuit);
    }
    
    // インテリジェントルーティング
    this.app.use('/', async (req, res) => {
      const upstream = this.selectUpstream(req);
      const circuit = this.circuits.get(upstream.name);
      
      try {
        await circuit.fire(req, res);
      } catch (error) {
        if (error.code === 'EOPENBREAKER') {
          res.status(503).json({
            error: 'Service unavailable',
            circuit: 'open'
          });
        } else {
          res.status(500).json({
            error: error.message
          });
        }
      }
    });
  }
  
  createProxyFunction(upstream) {
    return (req, res) => {
      return new Promise((resolve, reject) => {
        const proxy = httpProxy.createProxyMiddleware({
          target: upstream.url,
          changeOrigin: true,
          onProxyReq: (proxyReq, req) => {
            // トレースヘッダーの伝播
            if (req.traceContext) {
              proxyReq.setHeader('X-Trace-Id', req.traceContext.traceId);
              proxyReq.setHeader('X-Parent-Span-Id', req.traceContext.spanId);
            }
          },
          onProxyRes: (proxyRes, req, res) => {
            // インスタンスIDをヘッダーに追加
            res.setHeader('X-Instance-Id', upstream.id);
            resolve();
          },
          onError: (err, req, res) => {
            reject(err);
          }
        });
        
        proxy(req, res);
      });
    };
  }
  
  selectUpstream(req) {
    // P2C (Power of Two Choices) ロードバランシング
    const upstreams = this.meshConfig.getHealthyUpstreams();
    
    if (upstreams.length === 0) {
      throw new Error('No healthy upstreams');
    }
    
    if (upstreams.length === 1) {
      return upstreams[0];
    }
    
    // ランダムに2つ選択
    const idx1 = Math.floor(Math.random() * upstreams.length);
    let idx2 = Math.floor(Math.random() * upstreams.length);
    while (idx2 === idx1) {
      idx2 = Math.floor(Math.random() * upstreams.length);
    }
    
    const upstream1 = upstreams[idx1];
    const upstream2 = upstreams[idx2];
    
    // より負荷の低い方を選択
    const load1 = this.getUpstreamLoad(upstream1);
    const load2 = this.getUpstreamLoad(upstream2);
    
    return load1 <= load2 ? upstream1 : upstream2;
  }
  
  getUpstreamLoad(upstream) {
    // 簡易的な負荷計算（実際はもっと複雑）
    const circuit = this.circuits.get(upstream.name);
    const stats = circuit.stats;
    
    return stats.failures / (stats.successes + stats.failures + 1);
  }
  
  generateMetrics() {
    const p50 = this.percentile(this.metrics.latencies, 0.5);
    const p95 = this.percentile(this.metrics.latencies, 0.95);
    const p99 = this.percentile(this.metrics.latencies, 0.99);
    
    return `
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{service="${this.serviceName}"} ${this.metrics.requests}

# HELP http_errors_total Total HTTP errors
# TYPE http_errors_total counter
http_errors_total{service="${this.serviceName}"} ${this.metrics.errors}

# HELP http_request_duration_ms HTTP request duration percentiles
# TYPE http_request_duration_ms summary
http_request_duration_ms{service="${this.serviceName}",quantile="0.5"} ${p50}
http_request_duration_ms{service="${this.serviceName}",quantile="0.95"} ${p95}
http_request_duration_ms{service="${this.serviceName}",quantile="0.99"} ${p99}
    `.trim();
  }
  
  percentile(arr, p) {
    if (arr.length === 0) return 0;
    const sorted = [...arr].sort((a, b) => a - b);
    const index = Math.ceil(sorted.length * p) - 1;
    return sorted[index];
  }
  
  generateTraceId() {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
  }
  
  generateSpanId() {
    return Math.random().toString(36).substring(2);
  }
  
  sendSpan(span) {
    // コントロールプレーンにスパン情報を送信
    fetch(`${this.meshConfig.controlPlane}/api/spans`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(span)
    }).catch(err => {
      console.error('Failed to send span:', err);
    });
  }
  
  start() {
    const proxyPort = this.servicePort + 1000; // サイドカーポート
    
    this.app.listen(proxyPort, () => {
      console.log(`Sidecar proxy for ${this.serviceName} listening on port ${proxyPort}`);
      
      // サービスレジストリに登録
      this.registerService();
    });
  }
  
  async registerService() {
    const registration = {
      name: this.serviceName,
      port: this.servicePort,
      sidecarPort: this.servicePort + 1000,
      metadata: {
        version: process.env.SERVICE_VERSION || 'v1',
        region: process.env.REGION || 'default'
      }
    };
    
    await fetch(`${this.meshConfig.controlPlane}/api/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(registration)
    });
  }
}

// コントロールプレーン
class ServiceMeshControlPlane {
  constructor() {
    this.services = new Map();
    this.traces = new Map();
    this.config = new Map();
    this.app = express();
    
    this.setupEndpoints();
  }
  
  setupEndpoints() {
    this.app.use(express.json());
    
    // サービス登録
    this.app.post('/api/register', (req, res) => {
      const service = req.body;
      this.services.set(service.name, {
        ...service,
        registeredAt: Date.now(),
        status: 'healthy'
      });
      
      res.json({ success: true });
    });
    
    // サービスディスカバリー
    this.app.get('/api/services', (req, res) => {
      const services = Array.from(this.services.values());
      res.json({ services });
    });
    
    // スパン収集
    this.app.post('/api/spans', (req, res) => {
      const span = req.body;
      
      if (!this.traces.has(span.traceId)) {
        this.traces.set(span.traceId, []);
      }
      
      this.traces.get(span.traceId).push(span);
      res.json({ success: true });
    });
    
    // トレース取得
    this.app.get('/api/traces/:traceId', (req, res) => {
      const trace = this.traces.get(req.params.traceId);
      
      if (!trace) {
        res.status(404).json({ error: 'Trace not found' });
        return;
      }
      
      res.json({
        traceId: req.params.traceId,
        spans: trace
      });
    });
    
    // 設定管理
    this.app.put('/api/config/:service', (req, res) => {
      this.config.set(req.params.service, req.body);
      res.json({ success: true });
    });
  }
  
  start() {
    this.app.listen(15000, () => {
      console.log('Service Mesh Control Plane listening on port 15000');
    });
  }
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
RUN deno cache sidecar-proxy.ts control-plane.ts

EXPOSE 3000

CMD ["deno", "run", "--allow-net", "--allow-env", "--allow-hrtime", "sidecar-proxy.ts"]
```

### Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  # コントロールプレーン
  control-plane:
    build:
      context: .
      dockerfile: Dockerfile.control-plane
    ports:
      - "15000:15000"
    environment:
      NODE_ENV: production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:15000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # フロントエンドサービス + サイドカー
  frontend:
    build: .
    environment:
      SERVICE_NAME: frontend
      SERVICE_PORT: 3001
      MESH_ENABLED: "true"
      CONTROL_PLANE: http://control-plane:15000
    depends_on:
      control-plane:
        condition: service_healthy
    
  frontend-sidecar:
    build:
      context: .
      dockerfile: Dockerfile.sidecar
    environment:
      SERVICE_NAME: frontend
      SERVICE_PORT: 3001
      PROXY_PORT: 4001
      CONTROL_PLANE: http://control-plane:15000
    network_mode: "service:frontend"
    depends_on:
      - frontend

  # バックエンドサービス + サイドカー
  backend:
    build: .
    environment:
      SERVICE_NAME: backend
      SERVICE_PORT: 3002
      MESH_ENABLED: "true"
      
  backend-sidecar:
    build:
      context: .
      dockerfile: Dockerfile.sidecar
    environment:
      SERVICE_NAME: backend
      SERVICE_PORT: 3002
      PROXY_PORT: 4002
      CONTROL_PLANE: http://control-plane:15000
    network_mode: "service:backend"
    depends_on:
      - backend

  # Ingressゲートウェイ
  ingress:
    image: envoyproxy/envoy:v1.24-latest
    ports:
      - "80:80"
      - "9901:9901" # Admin
    volumes:
      - ./envoy.yaml:/etc/envoy/envoy.yaml:ro
    depends_on:
      - control-plane
      - frontend-sidecar
      - backend-sidecar

  # 観測性スタック
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
      
  jaeger:
    image: jaegertracing/all-in-one
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686" # UI
      - "14250:14250"
      - "14268:14268"
      - "14269:14269"
      - "9411:9411"
```

## 実行と検証

### 1. システム起動
```bash
docker-compose up -d

# サービス登録の確認
curl http://localhost:15000/api/services | jq
```

### 2. サービスメッシュ機能テスト
```bash
# サーキットブレーカーテスト
npm run test:circuit-breaker

# 分散トレーシング確認
open http://localhost:16686  # Jaeger UI

# メトリクス確認
open http://localhost:3000   # Grafana
```

### 3. カオステスト
```bash
# サービス障害シミュレーション
./scripts/chaos-mesh.sh inject-failure backend

# レイテンシ注入
./scripts/chaos-mesh.sh inject-latency frontend 500ms
```

## 成功基準

- [ ] 全サービスの自動登録と発見
- [ ] サーキットブレーカーによる障害隔離
- [ ] 分散トレースの完全な可視化
- [ ] P2Cアルゴリズムによる効率的な負荷分散
- [ ] カナリアデプロイメントの成功

## 観測性ダッシュボード

### Grafanaダッシュボード例
```json
{
  "dashboard": {
    "title": "Service Mesh Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[1m])"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_errors_total[1m]) / rate(http_requests_total[1m])"
        }]
      },
      {
        "title": "Latency P99",
        "targets": [{
          "expr": "http_request_duration_ms{quantile=\"0.99\"}"
        }]
      }
    ]
  }
}
```

## 次のステップ

サービスメッシュの基礎を確立後、`10_container_resource_limits`でリソース制限と競合の管理を学びます。

## 学んだこと

- サイドカーパターンの威力
- 分散システムの観測性の重要性
- 自動回復メカニズムの実装
- マイクロサービス間の複雑な相互作用

## 参考資料

- [Service Mesh Patterns](https://www.oreilly.com/library/view/the-enterprise-path/9781492041795/)
- [Envoy Proxy Documentation](https://www.envoyproxy.io/docs/envoy/latest/)
- [Distributed Tracing](https://opentracing.io/docs/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)