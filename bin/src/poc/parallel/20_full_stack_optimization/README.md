# 20_full_stack_optimization

## 概要

これまでの19のPoCで学んだ全ての最適化手法を統合し、エンドツーエンドでの最適化を実現します。単一サーバーから始まり、マルチサーバー、キャッシュ、読み書き分離まで、段階的な最適化の集大成です。

## 目的

- 全レイヤーでの最適化統合
- ボトルネック特定と解消
- 自動スケーリング戦略
- 総合的なパフォーマンス向上

## 統合アーキテクチャ

```
┌────────────────────────────────────────┐
│          CDN (CloudFlare)              │
│     静的コンテンツキャッシュ            │
└───────────────┬────────────────────────┘
                │
┌───────────────▼────────────────────────┐
│      Global Load Balancer              │
│  (GeoDNS + Health Checks)              │
└──┬─────────┬─────────┬─────────────────┘
   │         │         │
   ▼         ▼         ▼
┌──────┐ ┌──────┐ ┌──────┐
│Region│ │Region│ │Region│
│  US  │ │  EU  │ │ ASIA │
└──┬───┘ └──┬───┘ └──┬───┘
   │         │         │
   ▼         ▼         ▼
┌────────────────────────┐
│   Regional LB (HAProxy)│
└──┬──┬──┬──┬───────────┘
   │  │  │  │
   ▼  ▼  ▼  ▼
┌─────────────────────┐
│  App Servers (4+)   │
│  - Auto-scaling     │
│  - Service Mesh     │
│  - Circuit Breakers │
└──┬──────────────────┘
   │
   ├─────────┬─────────┐
   ▼         ▼         ▼
┌──────┐ ┌──────┐ ┌──────┐
│Local │ │Redis │ │ CDN  │
│Cache │ │Cache │ │Cache │
└──────┘ └──┬───┘ └──────┘
           │
   ┌───────┴───────┐
   ▼               ▼
┌──────┐      ┌────────┐
│Write │      │Read    │
│Master│      │Replicas│
│(1)   │      │(3+)    │
└──────┘      └────────┘
```

## 最適化レイヤー

### 1. フロントエンド最適化
```javascript
// cdn-config.js
module.exports = {
  // 静的アセットのCDN配信
  cdn: {
    provider: 'cloudflare',
    zones: ['us', 'eu', 'asia'],
    cache: {
      html: '1h',
      css: '1y',
      js: '1y',
      images: '1y',
      api: 'no-cache'
    }
  },
  
  // 画像最適化
  images: {
    formats: ['webp', 'avif', 'jpg'],
    sizes: [320, 640, 1280, 1920],
    lazyLoad: true,
    placeholder: 'blur'
  },
  
  // バンドル最適化
  webpack: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10
        },
        common: {
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true
        }
      }
    },
    compression: 'brotli',
    treeshaking: true
  }
};
```

### 2. アプリケーション層最適化
```javascript
// app-optimization.js
class OptimizedApp {
  constructor() {
    // コネクションプーリング
    this.dbPool = new Pool({
      max: 50,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000
    });
    
    // 多層キャッシュ
    this.l1Cache = new NodeCache({ stdTTL: 60 });
    this.l2Cache = new Redis.Cluster(redisNodes);
    
    // サーキットブレーカー
    this.circuitBreaker = new CircuitBreaker(this.handleRequest, {
      timeout: 3000,
      errorThresholdPercentage: 50,
      resetTimeout: 30000
    });
    
    // レート制限
    this.rateLimiter = new RateLimiter({
      windowMs: 60000,
      max: 100,
      skipSuccessfulRequests: true
    });
  }
  
  async handleRequest(req, res) {
    // 1. レート制限チェック
    if (!await this.rateLimiter.check(req)) {
      return res.status(429).send('Too Many Requests');
    }
    
    // 2. キャッシュ確認（L1 → L2）
    const cachedResponse = await this.getFromCache(req.path);
    if (cachedResponse) {
      return res.send(cachedResponse);
    }
    
    // 3. サーキットブレーカー経由でリクエスト処理
    try {
      const response = await this.circuitBreaker.fire(req);
      
      // 4. レスポンスをキャッシュ
      await this.cacheResponse(req.path, response);
      
      return res.send(response);
    } catch (error) {
      return this.handleError(error, res);
    }
  }
  
  async getFromCache(key) {
    // L1キャッシュ確認
    let value = this.l1Cache.get(key);
    if (value) return value;
    
    // L2キャッシュ確認
    value = await this.l2Cache.get(key);
    if (value) {
      // L1にも保存
      this.l1Cache.set(key, value);
      return JSON.parse(value);
    }
    
    return null;
  }
  
  async cacheResponse(key, value) {
    // 両レベルにキャッシュ
    this.l1Cache.set(key, value);
    await this.l2Cache.setex(key, 3600, JSON.stringify(value));
  }
}
```

### 3. データベース層最適化
```javascript
// db-optimization.js
class OptimizedDatabase {
  constructor() {
    // 読み書き分離
    this.master = new Pool(masterConfig);
    this.slaves = slaveConfigs.map(config => new Pool(config));
    
    // クエリキャッシュ
    this.queryCache = new Map();
    
    // プリペアドステートメント
    this.preparedStatements = new Map();
  }
  
  async query(sql, params, options = {}) {
    // 1. クエリ最適化
    const optimizedSql = this.optimizeQuery(sql);
    
    // 2. キャッシュ可能か判定
    if (this.isCacheable(optimizedSql)) {
      const cacheKey = this.getCacheKey(optimizedSql, params);
      const cached = this.queryCache.get(cacheKey);
      if (cached && cached.expires > Date.now()) {
        return cached.result;
      }
    }
    
    // 3. 適切なDBを選択
    const db = this.selectDatabase(optimizedSql, options);
    
    // 4. プリペアドステートメント使用
    const statement = await this.getPreparedStatement(db, optimizedSql);
    const result = await statement.execute(params);
    
    // 5. 結果をキャッシュ
    if (this.isCacheable(optimizedSql)) {
      this.queryCache.set(this.getCacheKey(optimizedSql, params), {
        result,
        expires: Date.now() + 60000
      });
    }
    
    return result;
  }
  
  optimizeQuery(sql) {
    // インデックスヒントの追加
    if (sql.includes('WHERE user_id')) {
      sql = sql.replace('FROM users', 'FROM users USE INDEX (idx_user_id)');
    }
    
    // 不要なカラムの除外
    if (sql.includes('SELECT *')) {
      console.warn('SELECT * detected, consider specifying columns');
    }
    
    return sql;
  }
  
  async getPreparedStatement(db, sql) {
    const key = `${db.id}:${sql}`;
    
    if (!this.preparedStatements.has(key)) {
      const statement = await db.prepare(sql);
      this.preparedStatements.set(key, statement);
    }
    
    return this.preparedStatements.get(key);
  }
}
```

### 4. 自動スケーリング
```javascript
// auto-scaling.js
class AutoScaler {
  constructor() {
    this.metrics = new MetricsCollector();
    this.kubernetes = new K8sClient();
    this.predictor = new LoadPredictor();
  }
  
  async checkAndScale() {
    const metrics = await this.metrics.collect();
    
    // 1. 現在の負荷を分析
    const analysis = {
      cpu: metrics.cpu.average,
      memory: metrics.memory.average,
      requestRate: metrics.requests.rate,
      responseTime: metrics.latency.p99,
      errorRate: metrics.errors.rate
    };
    
    // 2. 将来の負荷を予測
    const prediction = await this.predictor.predict(analysis);
    
    // 3. スケーリング決定
    const decision = this.makeScalingDecision(analysis, prediction);
    
    // 4. スケーリング実行
    if (decision.action !== 'none') {
      await this.executeScaling(decision);
    }
  }
  
  makeScalingDecision(current, predicted) {
    // CPUベース
    if (current.cpu > 80 || predicted.cpu > 80) {
      return { action: 'scale-up', replicas: 2 };
    }
    
    // レスポンスタイムベース
    if (current.responseTime > 500) {
      return { action: 'scale-up', replicas: 1 };
    }
    
    // エラー率ベース
    if (current.errorRate > 0.05) {
      return { action: 'circuit-break', services: ['problematic-service'] };
    }
    
    // スケールダウン条件
    if (current.cpu < 20 && current.requestRate < 100) {
      return { action: 'scale-down', replicas: 1 };
    }
    
    return { action: 'none' };
  }
  
  async executeScaling(decision) {
    switch (decision.action) {
      case 'scale-up':
        await this.kubernetes.scale('app', {
          replicas: '+' + decision.replicas
        });
        break;
        
      case 'scale-down':
        await this.kubernetes.scale('app', {
          replicas: '-' + decision.replicas,
          minReplicas: 2
        });
        break;
        
      case 'circuit-break':
        for (const service of decision.services) {
          await this.circuitBreaker.open(service);
        }
        break;
    }
  }
}
```

## パフォーマンステスト

### 統合負荷テスト
```javascript
// load-test.js
async function runComprehensiveLoadTest() {
  const scenarios = [
    {
      name: 'Normal Load',
      users: 100,
      duration: '5m',
      rampUp: '30s'
    },
    {
      name: 'Peak Load',
      users: 1000,
      duration: '10m',
      rampUp: '2m'
    },
    {
      name: 'Spike Test',
      users: 5000,
      duration: '1m',
      rampUp: '5s'
    },
    {
      name: 'Endurance Test',
      users: 500,
      duration: '1h',
      rampUp: '5m'
    }
  ];
  
  const results = [];
  
  for (const scenario of scenarios) {
    console.log(`Running ${scenario.name}...`);
    
    const result = await k6.run({
      vus: scenario.users,
      duration: scenario.duration,
      stages: [
        { duration: scenario.rampUp, target: scenario.users },
        { duration: scenario.duration, target: scenario.users }
      ],
      thresholds: {
        http_req_duration: ['p(99)<500'],
        http_req_failed: ['rate<0.01']
      }
    });
    
    results.push({
      scenario: scenario.name,
      metrics: {
        requests: result.metrics.http_reqs,
        duration: result.metrics.http_req_duration,
        dataReceived: result.metrics.data_received,
        errorRate: result.metrics.http_req_failed
      }
    });
  }
  
  return results;
}
```

### ボトルネック分析
```javascript
// bottleneck-analysis.js
class BottleneckAnalyzer {
  async analyze() {
    const metrics = await this.collectMetrics();
    const bottlenecks = [];
    
    // CPU分析
    if (metrics.cpu.max > 90) {
      bottlenecks.push({
        type: 'CPU',
        severity: 'high',
        location: metrics.cpu.highestNode,
        recommendation: 'Vertical scaling or code optimization needed'
      });
    }
    
    // メモリ分析
    if (metrics.memory.usage > 85) {
      bottlenecks.push({
        type: 'Memory',
        severity: 'high',
        location: metrics.memory.highestNode,
        recommendation: 'Memory leak investigation or scaling needed'
      });
    }
    
    // データベース分析
    if (metrics.db.slowQueries > 10) {
      bottlenecks.push({
        type: 'Database',
        severity: 'medium',
        queries: metrics.db.slowestQueries,
        recommendation: 'Query optimization or indexing needed'
      });
    }
    
    // ネットワーク分析
    if (metrics.network.latency > 100) {
      bottlenecks.push({
        type: 'Network',
        severity: 'medium',
        route: metrics.network.slowestRoute,
        recommendation: 'CDN or edge deployment needed'
      });
    }
    
    return bottlenecks;
  }
}
```

## 最適化結果

### ベースラインとの比較
| メトリクス | ベースライン | 最適化後 | 改善率 |
|-----------|------------|---------|--------|
| スループット | 100 req/s | 10,000 req/s | 100x |
| レイテンシ(P50) | 200ms | 10ms | 95% |
| レイテンシ(P99) | 1000ms | 50ms | 95% |
| エラー率 | 5% | 0.01% | 99.8% |
| 可用性 | 99% | 99.99% | 1.01x |
| コスト効率 | $1000/月 | $800/月 | 20% |

### 段階別改善
```
1. 単一サーバー: 100 req/s
2. +ロードバランサー: 400 req/s
3. +キャッシュ: 2,000 req/s
4. +読み書き分離: 5,000 req/s
5. +自動スケーリング: 10,000 req/s
6. +CDN: 50,000 req/s (静的コンテンツ含む)
```

## モニタリングダッシュボード

```javascript
// monitoring-dashboard.js
class Dashboard {
  constructor() {
    this.panels = [
      {
        name: 'Request Rate',
        query: 'rate(http_requests_total[5m])',
        visualization: 'line'
      },
      {
        name: 'Error Rate',
        query: 'rate(http_requests_failed[5m]) / rate(http_requests_total[5m])',
        visualization: 'line',
        alert: { threshold: 0.01, severity: 'critical' }
      },
      {
        name: 'Response Time',
        query: 'histogram_quantile(0.99, http_request_duration_seconds)',
        visualization: 'heatmap',
        alert: { threshold: 0.5, severity: 'warning' }
      },
      {
        name: 'Cache Hit Rate',
        query: 'rate(cache_hits[5m]) / (rate(cache_hits[5m]) + rate(cache_misses[5m]))',
        visualization: 'gauge',
        target: 0.9
      },
      {
        name: 'Database Connections',
        query: 'pg_stat_activity_count',
        visualization: 'line',
        alert: { threshold: 80, severity: 'warning' }
      },
      {
        name: 'Pod Scaling',
        query: 'kube_deployment_status_replicas',
        visualization: 'line'
      }
    ];
  }
}
```

## デプロイメント戦略

### Blue-Green デプロイメント
```yaml
# blue-green-deployment.yaml
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
    version: green  # 切り替え可能
  ports:
    - port: 80
      targetPort: 3000

---
# Blue環境
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
spec:
  replicas: 4
  selector:
    matchLabels:
      app: myapp
      version: blue
  template:
    metadata:
      labels:
        app: myapp
        version: blue
    spec:
      containers:
      - name: app
        image: myapp:v1.0
        
---
# Green環境
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
spec:
  replicas: 4
  selector:
    matchLabels:
      app: myapp
      version: green
  template:
    metadata:
      labels:
        app: myapp
        version: green
    spec:
      containers:
      - name: app
        image: myapp:v2.0
```

## チェックリスト

### パフォーマンス最適化
- [x] CDN導入
- [x] 画像最適化
- [x] バンドル最適化
- [x] 多層キャッシュ
- [x] データベース最適化
- [x] 読み書き分離
- [x] 自動スケーリング
- [x] サーキットブレーカー

### 可用性
- [x] ヘルスチェック
- [x] 自動フェイルオーバー
- [x] 分散ロック
- [x] レート制限
- [x] DDoS対策

### 運用性
- [x] 監視ダッシュボード
- [x] アラート設定
- [x] ログ集約
- [x] トレーシング
- [x] A/Bテスト基盤

## まとめ

### 学んだこと
1. **段階的な最適化**: 一度に全てを最適化せず、ボトルネックを特定して対処
2. **測定の重要性**: 推測ではなくデータに基づいた意思決定
3. **トレードオフ**: パフォーマンス、コスト、複雑性のバランス
4. **自動化**: 手動運用からの脱却

### ベストプラクティス
1. **早期最適化を避ける**: まず動くものを作り、測定してから最適化
2. **キャッシュは慎重に**: 不整合とのトレードオフを理解
3. **障害を前提に**: サーキットブレーカー、フォールバック
4. **継続的な改善**: 定期的な見直しと最適化

## 参考資料

- [High Performance Browser Networking](https://hpbn.co/)
- [Designing Data-Intensive Applications](https://dataintensive.net/)
- [Site Reliability Engineering](https://sre.google/books/)
- [The Art of Scalability](http://theartofscalability.com/)
- [Systems Performance](http://www.brendangregg.com/systems-performance-2nd-edition-book.html)