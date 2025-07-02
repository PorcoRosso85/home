# 20_production_best_practices

## 概要

これまでの19のPoCで学んだ知見を統合し、本番環境での並列・分散システム運用のベストプラクティスをまとめます。スケーラブルで信頼性の高いシステム構築の指針を提供します。

## 目的

- 学習した全パターンの統合
- 本番環境での実践的ガイドライン
- 運用の自動化と標準化
- 継続的な改善プロセス

## 全体アーキテクチャ

```
┌─────────────────────────────────────────────┐
│          Production Architecture            │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │  Edge   │  │  Multi  │  │  Cloud  │    │
│  │Computing│  │  Cloud  │  │ Native  │    │
│  └────┬────┘  └────┬────┘  └────┬────┘    │
│       │            │            │           │
│  ┌────▼────────────▼────────────▼────┐     │
│  │    Global Load Balancing          │     │
│  │    (Geo-distributed, HA)          │     │
│  └────────────────┬──────────────────┘     │
│                   │                         │
│  ┌────────────────▼──────────────────┐     │
│  │      Service Mesh (Istio)         │     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐     │     │
│  │  │mTLS  │ │Trace │ │Policy│     │     │
│  │  └──────┘ └──────┘ └──────┘     │     │
│  └────────────────┬──────────────────┘     │
│                   │                         │
│  ┌────────────────▼──────────────────┐     │
│  │    Container Orchestration        │     │
│  │         (Kubernetes)              │     │
│  │  ┌──────────┬──────────┐         │     │
│  │  │   HPA    │   VPA    │         │     │
│  │  └──────────┴──────────┘         │     │
│  └────────────────┬──────────────────┘     │
│                   │                         │
│  ┌────────────────▼──────────────────┐     │
│  │      Data Layer                   │     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐     │     │
│  │  │RDBMS │ │NoSQL │ │Cache │     │     │
│  │  └──────┘ └──────┘ └──────┘     │     │
│  └───────────────────────────────────┘     │
│                                             │
│  ┌─────────────────────────────────┐       │
│  │   Observability Platform        │       │
│  │  Metrics | Logs | Traces | Chaos│       │
│  └─────────────────────────────────┘       │
└─────────────────────────────────────────────┘
```

## ベストプラクティス集

### 1. スケーラビリティ設計

#### 水平スケーリング優先
```yaml
# ✅ Good: 水平スケーリング可能な設計
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stateless-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
      - name: app
        env:
        - name: INSTANCE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 自動スケーリング設定
```yaml
# HPA設定
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 3
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 10
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### 2. 高可用性パターン

#### マルチリージョン展開
```javascript
// multi-region-deployment.js
class MultiRegionDeployment {
  constructor() {
    this.regions = [
      { name: 'us-east-1', primary: true, weight: 40 },
      { name: 'eu-west-1', primary: false, weight: 30 },
      { name: 'ap-southeast-1', primary: false, weight: 30 }
    ];
  }
  
  async deploy(application) {
    // 全リージョンへの並列デプロイ
    const deployments = await Promise.all(
      this.regions.map(region => 
        this.deployToRegion(application, region)
      )
    );
    
    // クロスリージョンレプリケーション設定
    await this.setupReplication(deployments);
    
    // グローバルロードバランサー設定
    await this.configureGlobalLoadBalancer(deployments);
    
    return deployments;
  }
  
  async deployToRegion(application, region) {
    const deployment = {
      ...application,
      region: region.name,
      replicas: this.calculateReplicas(application.baseReplicas, region.weight),
      resources: this.adjustResourcesForRegion(application.resources, region)
    };
    
    // リージョン固有の設定
    if (region.primary) {
      deployment.role = 'primary';
      deployment.features = ['write-enabled', 'admin-api'];
    } else {
      deployment.role = 'replica';
      deployment.features = ['read-only', 'cache-heavy'];
    }
    
    return this.kubernetesClient.deploy(deployment, region);
  }
  
  calculateReplicas(base, weight) {
    return Math.ceil(base * weight / 100);
  }
}
```

#### サーキットブレーカー実装
```javascript
// circuit-breaker.js
class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.timeout = options.timeout || 5000;
    this.resetTimeout = options.resetTimeout || 30000;
    this.state = 'CLOSED';
    this.failures = 0;
    this.nextAttempt = Date.now();
  }
  
  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }
    
    try {
      const result = await this.performOperation(operation);
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  async performOperation(operation) {
    return new Promise(async (resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error('Operation timeout'));
      }, this.timeout);
      
      try {
        const result = await operation();
        clearTimeout(timer);
        resolve(result);
      } catch (error) {
        clearTimeout(timer);
        reject(error);
      }
    });
  }
  
  onSuccess() {
    this.failures = 0;
    if (this.state === 'HALF_OPEN') {
      this.state = 'CLOSED';
    }
  }
  
  onFailure() {
    this.failures++;
    if (this.failures >= this.failureThreshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.resetTimeout;
    }
  }
}
```

### 3. データ管理戦略

#### イベントソーシング
```javascript
// event-sourcing.js
class EventStore {
  constructor(database) {
    this.db = database;
  }
  
  async append(streamId, events) {
    const transaction = await this.db.transaction();
    
    try {
      for (const event of events) {
        await transaction.query(
          `INSERT INTO events (stream_id, event_type, event_data, event_version, created_at)
           VALUES ($1, $2, $3, $4, NOW())`,
          [streamId, event.type, JSON.stringify(event.data), event.version]
        );
      }
      
      await transaction.commit();
    } catch (error) {
      await transaction.rollback();
      throw error;
    }
  }
  
  async getEvents(streamId, fromVersion = 0) {
    const result = await this.db.query(
      `SELECT * FROM events 
       WHERE stream_id = $1 AND event_version > $2 
       ORDER BY event_version`,
      [streamId, fromVersion]
    );
    
    return result.rows.map(row => ({
      type: row.event_type,
      data: row.event_data,
      version: row.event_version,
      timestamp: row.created_at
    }));
  }
  
  async getSnapshot(streamId) {
    const result = await this.db.query(
      `SELECT * FROM snapshots 
       WHERE stream_id = $1 
       ORDER BY version DESC 
       LIMIT 1`,
      [streamId]
    );
    
    return result.rows[0] || null;
  }
  
  async saveSnapshot(streamId, snapshot) {
    await this.db.query(
      `INSERT INTO snapshots (stream_id, version, data, created_at)
       VALUES ($1, $2, $3, NOW())`,
      [streamId, snapshot.version, JSON.stringify(snapshot.data)]
    );
  }
}

// Aggregate実装例
class OrderAggregate {
  constructor(eventStore) {
    this.eventStore = eventStore;
    this.state = null;
    this.version = 0;
  }
  
  async load(orderId) {
    // スナップショットから開始
    const snapshot = await this.eventStore.getSnapshot(orderId);
    
    if (snapshot) {
      this.state = snapshot.data;
      this.version = snapshot.version;
    } else {
      this.state = { orderId, items: [], total: 0, status: 'pending' };
      this.version = 0;
    }
    
    // イベントを適用
    const events = await this.eventStore.getEvents(orderId, this.version);
    
    for (const event of events) {
      this.apply(event);
    }
  }
  
  apply(event) {
    switch (event.type) {
      case 'OrderCreated':
        this.state = { ...this.state, ...event.data };
        break;
      case 'ItemAdded':
        this.state.items.push(event.data.item);
        this.state.total += event.data.item.price * event.data.item.quantity;
        break;
      case 'OrderConfirmed':
        this.state.status = 'confirmed';
        break;
      // その他のイベント...
    }
    
    this.version = event.version;
  }
  
  async save(orderId, newEvents) {
    await this.eventStore.append(orderId, newEvents);
    
    // スナップショット作成（100イベントごと）
    if (this.version % 100 === 0) {
      await this.eventStore.saveSnapshot(orderId, {
        version: this.version,
        data: this.state
      });
    }
  }
}
```

### 4. 監視とアラート

#### 包括的なメトリクス収集
```yaml
# prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: application-alerts
spec:
  groups:
  - name: availability
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
        /
        sum(rate(http_requests_total[5m])) by (service)
        > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate on {{ $labels.service }}"
        description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.service }}"
    
    - alert: ServiceDown
      expr: up{job="kubernetes-pods"} == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Service {{ $labels.pod }} is down"
    
    - alert: HighLatency
      expr: |
        histogram_quantile(0.99,
          sum(rate(http_request_duration_seconds_bucket[5m])) by (service, le)
        ) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High latency on {{ $labels.service }}"
        description: "P99 latency is {{ $value }}s"
  
  - name: resource-usage
    interval: 30s
    rules:
    - alert: HighCPUUsage
      expr: |
        100 * (
          1 - avg by(instance)(
            rate(node_cpu_seconds_total{mode="idle"}[5m])
          )
        ) > 80
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage on {{ $labels.instance }}"
    
    - alert: HighMemoryUsage
      expr: |
        (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
        / node_memory_MemTotal_bytes * 100 > 85
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage on {{ $labels.instance }}"
```

#### 分散トレーシング
```javascript
// distributed-tracing.js
const opentelemetry = require('@opentelemetry/api');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');

class DistributedTracing {
  constructor() {
    this.tracer = opentelemetry.trace.getTracer('application', '1.0.0');
  }
  
  instrumentExpress(app) {
    app.use((req, res, next) => {
      const span = this.tracer.startSpan(`${req.method} ${req.path}`, {
        kind: opentelemetry.SpanKind.SERVER,
        attributes: {
          'http.method': req.method,
          'http.url': req.url,
          'http.target': req.path,
          'http.host': req.hostname,
          'http.scheme': req.protocol,
          'http.user_agent': req.get('user-agent')
        }
      });
      
      // コンテキスト伝播
      const ctx = opentelemetry.trace.setSpan(
        opentelemetry.context.active(),
        span
      );
      
      // レスポンス処理
      const originalSend = res.send;
      res.send = function(data) {
        span.setAttributes({
          'http.status_code': res.statusCode,
          'http.status_text': res.statusMessage
        });
        
        if (res.statusCode >= 400) {
          span.setStatus({
            code: opentelemetry.SpanStatusCode.ERROR,
            message: res.statusMessage
          });
        }
        
        span.end();
        originalSend.call(this, data);
      };
      
      opentelemetry.context.with(ctx, () => next());
    });
  }
  
  async instrumentDatabase(client) {
    const originalQuery = client.query.bind(client);
    
    client.query = async (text, params) => {
      const span = this.tracer.startSpan('db.query', {
        kind: opentelemetry.SpanKind.CLIENT,
        attributes: {
          'db.system': 'postgresql',
          'db.statement': text.substring(0, 100),
          'db.operation': text.split(' ')[0].toUpperCase()
        }
      });
      
      try {
        const result = await originalQuery(text, params);
        span.setStatus({ code: opentelemetry.SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.setStatus({
          code: opentelemetry.SpanStatusCode.ERROR,
          message: error.message
        });
        span.recordException(error);
        throw error;
      } finally {
        span.end();
      }
    };
  }
}
```

### 5. セキュリティベストプラクティス

#### ゼロトラストネットワーク
```yaml
# network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: zero-trust-policy
spec:
  podSelector: {}  # 全Podに適用
  policyTypes:
  - Ingress
  - Egress
  ingress: []  # デフォルトで全て拒否
  egress:
  - to:  # DNSのみ許可
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
---
# 特定の通信のみ許可
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-to-backend
spec:
  podSelector:
    matchLabels:
      tier: backend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - protocol: TCP
      port: 8080
```

#### シークレット管理
```javascript
// secret-management.js
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');
const crypto = require('crypto');

class SecretManager {
  constructor() {
    this.client = new SecretManagerServiceClient();
    this.cache = new Map();
    this.rotationHandlers = new Map();
  }
  
  async getSecret(name, version = 'latest') {
    const cacheKey = `${name}:${version}`;
    
    // キャッシュチェック
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (cached.expiry > Date.now()) {
        return cached.value;
      }
    }
    
    // シークレット取得
    const [response] = await this.client.accessSecretVersion({
      name: `projects/${process.env.PROJECT_ID}/secrets/${name}/versions/${version}`
    });
    
    const secret = response.payload.data.toString();
    
    // キャッシュ保存（5分）
    this.cache.set(cacheKey, {
      value: secret,
      expiry: Date.now() + 300000
    });
    
    return secret;
  }
  
  async rotateSecret(name) {
    // 新しいシークレット生成
    const newSecret = this.generateSecret();
    
    // シークレット更新
    await this.client.addSecretVersion({
      parent: `projects/${process.env.PROJECT_ID}/secrets/${name}`,
      payload: {
        data: Buffer.from(newSecret)
      }
    });
    
    // ローテーションハンドラー実行
    const handler = this.rotationHandlers.get(name);
    if (handler) {
      await handler(newSecret);
    }
    
    // キャッシュクリア
    for (const [key] of this.cache) {
      if (key.startsWith(`${name}:`)) {
        this.cache.delete(key);
      }
    }
    
    return newSecret;
  }
  
  onRotation(secretName, handler) {
    this.rotationHandlers.set(secretName, handler);
  }
  
  generateSecret(length = 32) {
    return crypto.randomBytes(length).toString('base64');
  }
}
```

### 6. CI/CDパイプライン

#### GitOpsワークフロー
```yaml
# .github/workflows/gitops.yaml
name: GitOps Deployment

on:
  push:
    branches: [main]
    paths:
    - 'k8s/**'
    - 'apps/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Validate Kubernetes manifests
      run: |
        kubectl apply --dry-run=client -f k8s/
    
    - name: Security scanning
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'config'
        scan-ref: 'k8s/'
    
    - name: Policy validation
      run: |
        opa test policies/
        conftest verify --policy policies/ k8s/

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Kustomize
      uses: imranismail/setup-kustomize@v1
    
    - name: Update image tags
      run: |
        cd k8s/overlays/production
        kustomize edit set image app=${{ github.sha }}
    
    - name: Commit changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git commit -am "Update image to ${{ github.sha }}"
        git push
    
    - name: Sync ArgoCD
      run: |
        argocd app sync production --force
        argocd app wait production --health
```

### 7. 災害復旧計画

#### バックアップと復元
```bash
#!/bin/bash
# backup-restore.sh

# データベースバックアップ
backup_databases() {
    echo "Starting database backups..."
    
    # PostgreSQL
    kubectl exec -n production postgres-primary-0 -- \
        pg_dumpall -U postgres | \
        gzip > backup-$(date +%Y%m%d-%H%M%S).sql.gz
    
    # MongoDB
    kubectl exec -n production mongodb-0 -- \
        mongodump --archive --gzip | \
        aws s3 cp - s3://backups/mongodb-$(date +%Y%m%d-%H%M%S).gz
    
    # Redis
    kubectl exec -n production redis-master-0 -- \
        redis-cli BGSAVE
    
    # Persistent Volumes
    velero backup create pv-backup-$(date +%Y%m%d) \
        --include-namespaces production \
        --ttl 720h
}

# 復元手順
restore_from_backup() {
    local backup_date=$1
    
    echo "Restoring from backup: ${backup_date}"
    
    # Velero復元
    velero restore create --from-backup pv-backup-${backup_date}
    
    # データベース復元
    kubectl exec -i -n production postgres-primary-0 -- \
        psql -U postgres < <(gunzip -c backup-${backup_date}.sql.gz)
}

# 災害復旧テスト
dr_test() {
    echo "Starting DR test..."
    
    # 別リージョンでの復元
    kubectl config use-context dr-cluster
    
    # バックアップからの復元
    restore_from_backup $(date +%Y%m%d)
    
    # 検証
    run_validation_tests
}
```

### 8. パフォーマンス最適化

#### キャッシング戦略
```javascript
// caching-strategy.js
class CacheManager {
  constructor(redis, options = {}) {
    this.redis = redis;
    this.ttl = options.ttl || 3600;
    this.prefix = options.prefix || 'cache:';
  }
  
  async get(key, fetcher) {
    const cacheKey = this.prefix + key;
    
    // キャッシュ確認
    let cached = await this.redis.get(cacheKey);
    
    if (cached) {
      // キャッシュヒット
      this.updateMetrics('hit', key);
      return JSON.parse(cached);
    }
    
    // キャッシュミス - データ取得
    this.updateMetrics('miss', key);
    
    // Dogpile効果防止
    const lockKey = `lock:${cacheKey}`;
    const lock = await this.redis.set(lockKey, '1', 'NX', 'EX', 30);
    
    if (!lock) {
      // 他のプロセスが取得中 - 待機
      await this.waitForCache(cacheKey);
      cached = await this.redis.get(cacheKey);
      return cached ? JSON.parse(cached) : null;
    }
    
    try {
      const data = await fetcher();
      
      // キャッシュ保存
      await this.redis.setex(
        cacheKey,
        this.ttl,
        JSON.stringify(data)
      );
      
      // ウォームアップ用の予備キャッシュ
      await this.redis.setex(
        `${cacheKey}:warm`,
        this.ttl + 300,
        JSON.stringify(data)
      );
      
      return data;
    } finally {
      await this.redis.del(lockKey);
    }
  }
  
  async invalidate(pattern) {
    const keys = await this.redis.keys(this.prefix + pattern);
    
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
  
  async warmup(keys, fetcher) {
    const promises = keys.map(key => 
      this.get(key, () => fetcher(key))
    );
    
    await Promise.all(promises);
  }
  
  async waitForCache(key, timeout = 5000) {
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
      const value = await this.redis.get(key);
      if (value) return;
      
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
}
```

## チェックリスト

### デプロイメント前
- [ ] 負荷テストの実施
- [ ] カオスエンジニアリングテスト
- [ ] セキュリティスキャン
- [ ] 依存関係の更新
- [ ] ドキュメントの更新

### 本番環境監視
- [ ] SLI/SLOの定義
- [ ] アラートルールの設定
- [ ] ダッシュボードの作成
- [ ] ランブックの準備
- [ ] インシデント対応手順

### 定期メンテナンス
- [ ] バックアップの検証
- [ ] 証明書の更新
- [ ] 依存関係の脆弱性スキャン
- [ ] キャパシティプランニング
- [ ] コスト最適化レビュー

## まとめ

### 重要な学び

1. **段階的なスケーリング**: 単一コンテナから始まり、マルチクラウドまで段階的に拡張
2. **障害を前提とした設計**: カオスエンジニアリングによる継続的な検証
3. **自動化の重要性**: 手動運用から完全自動化への移行
4. **観測可能性**: メトリクス、ログ、トレースの統合

### 次のステップ

1. **AIオプス**: 機械学習による異常検知と自動修復
2. **サーバーレス統合**: イベントドリブンアーキテクチャ
3. **量子耐性暗号**: 将来のセキュリティ対策
4. **グリーンコンピューティング**: 環境に配慮した最適化

## 参考資料

### 書籍
- "Site Reliability Engineering" - Google
- "Building Microservices" - Sam Newman
- "Designing Data-Intensive Applications" - Martin Kleppmann
- "Cloud Native Patterns" - Cornelia Davis

### オンラインリソース
- [CNCF Cloud Native Trail Map](https://github.com/cncf/trailmap)
- [The Twelve-Factor App](https://12factor.net/)
- [Google Cloud Architecture Framework](https://cloud.google.com/architecture/framework)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

### コミュニティ
- [CNCF](https://www.cncf.io/)
- [Kubernetes Community](https://kubernetes.io/community/)
- [DevOps Community](https://devops.com/)
- [SRE Community](https://sre.google/)