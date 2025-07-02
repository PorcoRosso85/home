# 06_quad_containers_with_lb

## 概要

4つのアプリケーションコンテナに拡張し、より高度な負荷分散戦略とサービスメッシュパターンを検証します。単一サーバーでのコンテナオーケストレーションの実践的な限界を探ります。

## 目的

- 4コンテナでのスケーリング効率の検証
- 高度な負荷分散アルゴリズムの比較
- リソース競合の影響測定
- サービスディスカバリーの必要性確認

## アーキテクチャ

```
┌─────────────────────────────────┐
│       Clients (1000+)           │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│    Advanced Load Balancer       │
│  ┌─────────────────────────┐    │
│  │ - Least Connections     │    │
│  │ - Weighted Round Robin  │    │
│  │ - Response Time Based   │    │
│  │ - Circuit Breaker       │    │
│  └─────────────────────────┘    │
└───┬─────┬─────┬─────┬───────────┘
    │     │     │     │
    ▼     ▼     ▼     ▼
┌──────┐┌──────┐┌──────┐┌──────┐
│App-1 ││App-2 ││App-3 ││App-4 │
│:3001 ││:3002 ││:3003 ││:3004 │
│      ││      ││      ││      │
│Weight││Weight││Weight││Weight│
│ 1.0  ││ 1.0  ││ 0.5  ││ 1.5  │
└──────┘└──────┘└──────┘└──────┘
    │       │       │       │
    └───────┴───────┴───────┘
              │
    ┌─────────▼─────────┐
    │ Shared Resources  │
    │ - CPU (4 cores)   │
    │ - Memory (4GB)    │
    │ - Network I/O     │
    └───────────────────┘
```

## 検証項目

### 1. スケーリング効率
- **4倍のスループット達成可能性**: 理論値との乖離
- **リソース競合の影響**: CPU/メモリの奪い合い
- **最適なコンテナ数**: 収穫逓減の法則
- **コンテナ間の干渉**: ノイジーネイバー問題

### 2. 高度な負荷分散
- **アルゴリズム比較**: RR vs LC vs Response Time
- **動的重み付け**: パフォーマンスベースの調整
- **サーキットブレーカー**: 障害の伝播防止
- **リトライとタイムアウト**: 最適な設定値

### 3. 運用の複雑性
- **ログ集約**: 4つのソースからの統合
- **デバッグの困難さ**: 問題の特定と切り分け
- **設定管理**: 環境変数とシークレット
- **協調的な起動/停止**: 依存関係の管理

## TDDアプローチ

### Red Phase (4コンテナシステムのテスト)
```javascript
// test/quad-container-advanced.test.js
describe('Quad Container Advanced Load Balancing', () => {
  let system;
  let chaos;
  
  beforeAll(async () => {
    system = new QuadContainerSystem({
      containers: ['app-1', 'app-2', 'app-3', 'app-4'],
      loadBalancer: 'nginx-advanced',
      monitoring: true
    });
    
    chaos = new ChaosEngineering(system);
    
    await system.waitForReady();
  });

  it('should achieve near-linear scaling with 4 containers', async () => {
    // ベースライン（前のPOCから）
    const baselines = {
      single: { throughput: 1000, latency: 50 },
      dual: { throughput: 1800, latency: 55 }
    };
    
    // 4コンテナでの性能測定
    const quadResults = await runBenchmark({
      duration: 60000,
      targetRPS: 4000,
      connections: 2000
    });
    
    // スケーリング分析
    const scalingAnalysis = {
      throughputEfficiency: quadResults.throughput / (baselines.single.throughput * 4),
      latencyDegradation: quadResults.p95Latency / baselines.single.latency,
      actualScalingFactor: quadResults.throughput / baselines.single.throughput
    };
    
    // 期待値
    expect(scalingAnalysis.throughputEfficiency).toBeGreaterThan(0.7); // 70%以上の効率
    expect(scalingAnalysis.latencyDegradation).toBeLessThan(1.5); // 50%以下の劣化
    expect(scalingAnalysis.actualScalingFactor).toBeGreaterThan(3.0); // 3倍以上
    
    // リソース使用効率
    const resourceMetrics = await system.getResourceMetrics();
    expect(resourceMetrics.cpuEfficiency).toBeGreaterThan(0.8); // CPU使用率80%以上
    expect(resourceMetrics.memoryWaste).toBeLessThan(0.2); // メモリ無駄20%以下
  });

  it('should handle complex failure scenarios', async () => {
    const scenarios = [
      {
        name: 'single_container_failure',
        action: () => chaos.killContainer('app-2'),
        expectedBehavior: {
          availability: 0.99,
          maxLatencyIncrease: 1.2
        }
      },
      {
        name: 'dual_container_failure',
        action: () => chaos.killContainers(['app-1', 'app-3']),
        expectedBehavior: {
          availability: 0.95,
          maxLatencyIncrease: 2.0
        }
      },
      {
        name: 'memory_pressure',
        action: () => chaos.induceMemoryPressure('app-4', 0.9),
        expectedBehavior: {
          affectedContainerSlowdown: 5.0,
          otherContainersImpact: 1.1
        }
      },
      {
        name: 'cascading_failure',
        action: () => chaos.induceCascadingFailure(),
        expectedBehavior: {
          recoveryTime: 30000,
          dataLoss: false
        }
      }
    ];
    
    for (const scenario of scenarios) {
      console.log(`Testing scenario: ${scenario.name}`);
      
      const baseline = await system.getCurrentMetrics();
      
      // カオスを注入
      await scenario.action();
      
      // 影響を測定
      const duringChaos = await monitorDuring(30000);
      
      // 復旧
      await system.recover();
      
      const analysis = analyzeScenario(baseline, duringChaos);
      
      // 期待される挙動の検証
      Object.entries(scenario.expectedBehavior).forEach(([metric, expected]) => {
        expect(analysis[metric]).toBeLessThanOrEqual(expected);
      });
    }
  });

  it('should optimize load distribution based on performance', async () => {
    // 異なるパフォーマンス特性を持つコンテナを設定
    await system.configureContainers({
      'app-1': { cpuLimit: '1.0', memoryLimit: '1G' },
      'app-2': { cpuLimit: '1.0', memoryLimit: '1G' },
      'app-3': { cpuLimit: '0.5', memoryLimit: '512M' }, // 低性能
      'app-4': { cpuLimit: '1.5', memoryLimit: '1.5G' }  // 高性能
    });
    
    // 動的重み付けを有効化
    await system.enableDynamicWeighting();
    
    // 負荷テスト実行
    const testDuration = 120000; // 2分
    const results = await runAdaptiveLoadTest({
      duration: testDuration,
      initialRPS: 2000,
      adaptiveScaling: true
    });
    
    // 時間経過による重み付けの変化を分析
    const weightEvolution = results.getWeightEvolution();
    
    // 低性能コンテナへの負荷が減少していることを確認
    expect(weightEvolution['app-3'].final).toBeLessThan(
      weightEvolution['app-3'].initial * 0.7
    );
    
    // 高性能コンテナへの負荷が増加していることを確認
    expect(weightEvolution['app-4'].final).toBeGreaterThan(
      weightEvolution['app-4'].initial * 1.2
    );
    
    // 全体的なパフォーマンス向上
    const performanceImprovement = 
      results.finalThroughput / results.initialThroughput;
    expect(performanceImprovement).toBeGreaterThan(1.15); // 15%以上の改善
  });

  it('should handle resource contention gracefully', async () => {
    // リソース競合シナリオ
    const contentionTests = [
      {
        name: 'cpu_contention',
        load: () => generateCPUIntensiveLoad(4000),
        metric: 'cpuThrottling'
      },
      {
        name: 'memory_contention',
        load: () => generateMemoryIntensiveLoad(3.5), // 3.5GB
        metric: 'memorySwapping'
      },
      {
        name: 'io_contention',
        load: () => generateIOIntensiveLoad(1000), // 1000 IOPS
        metric: 'ioWait'
      }
    ];
    
    for (const test of contentionTests) {
      console.log(`Testing ${test.name}`);
      
      // ベースライン測定
      const baseline = await measureContainerMetrics();
      
      // 競合を発生させる
      const loadHandle = await test.load();
      
      // 競合中のメトリクス
      const duringContention = await measureContainerMetrics();
      
      // クリーンアップ
      await loadHandle.stop();
      
      // 分析
      const impact = calculateContentionImpact(baseline, duringContention);
      
      // 過度な劣化がないことを確認
      expect(impact[test.metric]).toBeLessThan(2.0); // 2倍以下の劣化
      
      // 公平性の確認（特定のコンテナだけが影響を受けていない）
      const fairness = calculateFairnessIndex(impact.perContainer);
      expect(fairness).toBeGreaterThan(0.8); // Jain's fairness index
    }
  });
});

// 高度なロードバランシングアルゴリズムテスト
describe('Advanced Load Balancing Algorithms', () => {
  it('should compare different algorithms', async () => {
    const algorithms = [
      'round_robin',
      'least_conn',
      'least_response_time',
      'weighted_response_time',
      'adaptive'
    ];
    
    const results = {};
    
    for (const algorithm of algorithms) {
      console.log(`Testing algorithm: ${algorithm}`);
      
      // アルゴリズムを切り替え
      await reconfigureLoadBalancer({ algorithm });
      
      // パフォーマンステスト
      results[algorithm] = await runStandardBenchmark({
        duration: 60000,
        targetRPS: 3000
      });
      
      // クールダウン
      await sleep(10000);
    }
    
    // 結果の比較
    const comparison = compareAlgorithms(results);
    
    // least_response_timeが最も良いはず
    expect(comparison.bestAlgorithm).toBe('least_response_time');
    
    // adaptiveが最も安定しているはず
    expect(comparison.mostStable).toBe('adaptive');
    
    // round_robinが最もシンプルで予測可能
    expect(comparison.mostPredictable).toBe('round_robin');
  });
});

// ヘルパー関数
function calculateFairnessIndex(values) {
  // Jain's fairness index
  const sum = values.reduce((a, b) => a + b, 0);
  const sumSquares = values.reduce((a, b) => a + b * b, 0);
  const n = values.length;
  
  return (sum * sum) / (n * sumSquares);
}

async function monitorDuring(duration) {
  const metrics = [];
  const interval = 100; // 100ms
  const iterations = duration / interval;
  
  for (let i = 0; i < iterations; i++) {
    metrics.push(await system.getCurrentMetrics());
    await sleep(interval);
  }
  
  return {
    metrics,
    summary: summarizeMetrics(metrics)
  };
}
```

### Green Phase (4コンテナシステムの実装)
```nginx
# nginx-advanced.conf
# 高度な負荷分散設定

# アップストリームゾーンの定義（共有メモリ）
upstream backend {
    zone backend_zone 64k;
    
    # 最少接続数アルゴリズム
    least_conn;
    
    # サーバー定義（重み付きの動的調整可能）
    server app-1:3001 weight=10 max_fails=3 fail_timeout=30s;
    server app-2:3002 weight=10 max_fails=3 fail_timeout=30s;
    server app-3:3003 weight=5  max_fails=3 fail_timeout=30s; # 低性能
    server app-4:3004 weight=15 max_fails=3 fail_timeout=30s; # 高性能
    
    # 接続プーリング
    keepalive 128;
    keepalive_requests 1000;
    keepalive_timeout 65s;
}

# レスポンスタイムベースの負荷分散（Plus版機能の代替）
map $upstream_response_time $response_time_zone {
    default medium;
    ~^0\.0[0-4] fast;
    ~^0\.[5-9] slow;
    ~^[1-9] very_slow;
}

# サーキットブレーカーの実装
map $upstream_addr $circuit_status {
    default open;
    ~app-1:3001$ $circuit_app1;
    ~app-2:3002$ $circuit_app2;
    ~app-3:3003$ $circuit_app3;
    ~app-4:3004$ $circuit_app4;
}

server {
    listen 80;
    
    # アクセスログの詳細化
    log_format detailed '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       'rt=$request_time uct="$upstream_connect_time" '
                       'uht="$upstream_header_time" urt="$upstream_response_time" '
                       'us="$upstream_status" ua="$upstream_addr"';
    
    access_log /var/log/nginx/access.log detailed;
    
    # プロキシ設定
    location / {
        proxy_pass http://backend;
        
        # タイムアウトとリトライ
        proxy_connect_timeout 2s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
        
        # 高度なフェイルオーバー
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_next_upstream_tries 4;
        proxy_next_upstream_timeout 5s;
        
        # ヘッダー
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Response-Time-Zone $response_time_zone;
        
        # バッファリング最適化
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 16 8k;
        proxy_busy_buffers_size 24k;
    }
    
    # 動的な重み調整エンドポイント
    location /admin/adjust-weight {
        # 認証が必要
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        content_by_lua_block {
            local server = ngx.var.arg_server
            local weight = ngx.var.arg_weight
            
            -- 実際の実装では動的モジュールを使用
            ngx.say("Weight adjustment would be applied here")
        }
    }
    
    # ヘルスチェックの高度化
    location /health-check {
        access_log off;
        
        content_by_lua_block {
            local backends = {
                {name = "app-1", url = "http://app-1:3001/health"},
                {name = "app-2", url = "http://app-2:3002/health"},
                {name = "app-3", url = "http://app-3:3003/health"},
                {name = "app-4", url = "http://app-4:3004/health"}
            }
            
            local results = {}
            
            for _, backend in ipairs(backends) do
                local res = ngx.location.capture("/proxy/" .. backend.name)
                results[backend.name] = {
                    status = res.status,
                    time = res.header["X-Response-Time"] or "unknown"
                }
            end
            
            ngx.header.content_type = "application/json"
            ngx.say(cjson.encode(results))
        }
    }
}
```

```javascript
// container-orchestrator.js
// 4コンテナの協調制御

const EventEmitter = require('events');

class ContainerOrchestrator extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.containers = new Map();
    this.loadBalancer = options.loadBalancer;
    this.metricsInterval = options.metricsInterval || 1000;
    
    // サーキットブレーカーの状態
    this.circuitBreakers = new Map();
    
    // 動的重み付け
    this.weights = new Map();
    this.dynamicWeighting = options.dynamicWeighting || false;
  }
  
  async initialize() {
    // コンテナの初期化
    const containerConfigs = [
      { id: 'app-1', port: 3001, weight: 10 },
      { id: 'app-2', port: 3002, weight: 10 },
      { id: 'app-3', port: 3003, weight: 5 },
      { id: 'app-4', port: 3004, weight: 15 }
    ];
    
    for (const config of containerConfigs) {
      await this.addContainer(config);
    }
    
    // メトリクス収集開始
    this.startMetricsCollection();
    
    // 動的重み付けが有効な場合
    if (this.dynamicWeighting) {
      this.startDynamicWeighting();
    }
  }
  
  async addContainer(config) {
    const container = {
      id: config.id,
      port: config.port,
      weight: config.weight,
      status: 'initializing',
      metrics: {
        requests: 0,
        errors: 0,
        responseTime: [],
        cpu: 0,
        memory: 0
      }
    };
    
    this.containers.set(config.id, container);
    this.weights.set(config.id, config.weight);
    
    // サーキットブレーカーの初期化
    this.circuitBreakers.set(config.id, {
      state: 'closed',
      failures: 0,
      lastFailure: null,
      timeout: 30000 // 30秒
    });
    
    // コンテナの起動を待つ
    await this.waitForHealthy(config.id);
    
    container.status = 'running';
    this.emit('container-added', config.id);
  }
  
  async removeContainer(containerId) {
    const container = this.containers.get(containerId);
    if (!container) return;
    
    // グレースフルシャットダウン
    container.status = 'draining';
    this.emit('container-draining', containerId);
    
    // 既存の接続が完了するまで待つ
    await this.drainConnections(containerId);
    
    // ロードバランサーから除外
    await this.updateLoadBalancer();
    
    this.containers.delete(containerId);
    this.weights.delete(containerId);
    this.circuitBreakers.delete(containerId);
    
    this.emit('container-removed', containerId);
  }
  
  startMetricsCollection() {
    this.metricsTimer = setInterval(async () => {
      for (const [id, container] of this.containers) {
        if (container.status !== 'running') continue;
        
        try {
          const metrics = await this.collectMetrics(id);
          this.updateContainerMetrics(id, metrics);
          
          // サーキットブレーカーの更新
          this.updateCircuitBreaker(id, metrics);
          
        } catch (error) {
          console.error(`Failed to collect metrics for ${id}:`, error);
          this.handleMetricsFailure(id);
        }
      }
      
      this.emit('metrics-updated', this.getAggregatedMetrics());
    }, this.metricsInterval);
  }
  
  startDynamicWeighting() {
    this.weightingTimer = setInterval(async () => {
      const performanceScores = this.calculatePerformanceScores();
      
      for (const [id, score] of performanceScores) {
        const currentWeight = this.weights.get(id);
        const newWeight = this.calculateNewWeight(currentWeight, score);
        
        if (Math.abs(newWeight - currentWeight) > 1) {
          this.weights.set(id, newWeight);
          await this.updateLoadBalancerWeight(id, newWeight);
          
          this.emit('weight-adjusted', {
            container: id,
            oldWeight: currentWeight,
            newWeight: newWeight,
            reason: score
          });
        }
      }
    }, 10000); // 10秒ごと
  }
  
  calculatePerformanceScores() {
    const scores = new Map();
    
    for (const [id, container] of this.containers) {
      if (container.status !== 'running') continue;
      
      const metrics = container.metrics;
      
      // パフォーマンススコアの計算（0-100）
      let score = 100;
      
      // レスポンスタイム（重み: 40%）
      const avgResponseTime = this.average(metrics.responseTime);
      score -= Math.min(40, (avgResponseTime / 100) * 40);
      
      // エラー率（重み: 30%）
      const errorRate = metrics.errors / (metrics.requests || 1);
      score -= errorRate * 30;
      
      // CPU使用率（重み: 20%）
      score -= Math.min(20, (metrics.cpu / 100) * 20);
      
      // メモリ使用率（重み: 10%）
      score -= Math.min(10, (metrics.memory / 100) * 10);
      
      scores.set(id, Math.max(0, score));
    }
    
    return scores;
  }
  
  calculateNewWeight(currentWeight, performanceScore) {
    // パフォーマンススコアに基づいて重みを調整
    const targetWeight = Math.round((performanceScore / 100) * 20);
    
    // 急激な変化を避けるため、段階的に調整
    const adjustment = Math.sign(targetWeight - currentWeight) * 2;
    
    return Math.max(1, Math.min(20, currentWeight + adjustment));
  }
  
  updateCircuitBreaker(containerId, metrics) {
    const breaker = this.circuitBreakers.get(containerId);
    if (!breaker) return;
    
    const errorRate = metrics.errors / (metrics.requests || 1);
    
    if (errorRate > 0.5) {
      // エラー率が50%を超えた場合
      breaker.failures++;
      breaker.lastFailure = Date.now();
      
      if (breaker.failures >= 5 && breaker.state === 'closed') {
        // サーキットを開く
        breaker.state = 'open';
        this.emit('circuit-opened', containerId);
        
        // タイムアウト後に半開状態にする
        setTimeout(() => {
          breaker.state = 'half-open';
          breaker.failures = 0;
          this.emit('circuit-half-open', containerId);
        }, breaker.timeout);
      }
    } else if (breaker.state === 'half-open') {
      // 成功したので閉じる
      breaker.state = 'closed';
      breaker.failures = 0;
      this.emit('circuit-closed', containerId);
    }
  }
  
  async collectMetrics(containerId) {
    const container = this.containers.get(containerId);
    const url = `http://${containerId}:${container.port}/metrics`;
    
    const response = await fetch(url, { timeout: 1000 });
    return await response.json();
  }
  
  updateContainerMetrics(containerId, newMetrics) {
    const container = this.containers.get(containerId);
    if (!container) return;
    
    // メトリクスの更新（移動平均）
    container.metrics.requests = newMetrics.requests;
    container.metrics.errors = newMetrics.errors;
    container.metrics.cpu = newMetrics.cpu;
    container.metrics.memory = newMetrics.memory;
    
    // レスポンスタイムの移動平均
    container.metrics.responseTime.push(newMetrics.avgResponseTime);
    if (container.metrics.responseTime.length > 60) {
      container.metrics.responseTime.shift();
    }
  }
  
  getAggregatedMetrics() {
    const aggregated = {
      totalRequests: 0,
      totalErrors: 0,
      avgResponseTime: 0,
      avgCpu: 0,
      avgMemory: 0,
      containerMetrics: {}
    };
    
    let responseTimeSum = 0;
    let responseTimeCount = 0;
    
    for (const [id, container] of this.containers) {
      if (container.status !== 'running') continue;
      
      aggregated.totalRequests += container.metrics.requests;
      aggregated.totalErrors += container.metrics.errors;
      aggregated.avgCpu += container.metrics.cpu;
      aggregated.avgMemory += container.metrics.memory;
      
      const avgRT = this.average(container.metrics.responseTime);
      responseTimeSum += avgRT;
      responseTimeCount++;
      
      aggregated.containerMetrics[id] = {
        ...container.metrics,
        avgResponseTime: avgRT,
        weight: this.weights.get(id),
        circuitState: this.circuitBreakers.get(id).state
      };
    }
    
    aggregated.avgResponseTime = responseTimeCount > 0 
      ? responseTimeSum / responseTimeCount 
      : 0;
    aggregated.avgCpu /= this.containers.size;
    aggregated.avgMemory /= this.containers.size;
    
    return aggregated;
  }
  
  average(arr) {
    if (arr.length === 0) return 0;
    return arr.reduce((a, b) => a + b) / arr.length;
  }
}

module.exports = ContainerOrchestrator;
```

### Docker Compose - 4コンテナ構成
```yaml
# docker-compose.yml
version: '3.8'

services:
  nginx:
    build:
      context: .
      dockerfile: Dockerfile.nginx
    ports:
      - "80:80"
      - "8080:8080" # 管理UI
    volumes:
      - ./nginx-advanced.conf:/etc/nginx/nginx.conf:ro
      - ./lua-scripts:/etc/nginx/lua:ro
    depends_on:
      app-1:
        condition: service_healthy
      app-2:
        condition: service_healthy
      app-3:
        condition: service_healthy
      app-4:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

  app-1:
    build: .
    environment:
      CONTAINER_ID: app-1
      PORT: 3001
      NODE_ENV: production
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "node", "healthcheck.js"]
      interval: 5s
      timeout: 3s
      retries: 5

  app-2:
    build: .
    environment:
      CONTAINER_ID: app-2
      PORT: 3002
      NODE_ENV: production
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "node", "healthcheck.js"]
      interval: 5s
      timeout: 3s
      retries: 5

  app-3:
    build: .
    environment:
      CONTAINER_ID: app-3
      PORT: 3003
      NODE_ENV: production
      PERFORMANCE_MODE: low # シミュレート用
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "node", "healthcheck.js"]
      interval: 5s
      timeout: 3s
      retries: 5

  app-4:
    build: .
    environment:
      CONTAINER_ID: app-4
      PORT: 3004
      NODE_ENV: production
      PERFORMANCE_MODE: high # シミュレート用
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1536M
    healthcheck:
      test: ["CMD", "node", "healthcheck.js"]
      interval: 5s
      timeout: 3s
      retries: 5

  # オーケストレーター
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.orchestrator
    environment:
      DYNAMIC_WEIGHTING: "true"
      METRICS_INTERVAL: 1000
    depends_on:
      - nginx
      - app-1
      - app-2
      - app-3
      - app-4
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

  # メトリクス可視化
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana-datasources:/etc/grafana/provisioning/datasources
```

## 実行と検証

### 1. システム起動
```bash
# 環境準備
docker-compose build

# 起動（ヘルスチェック付き）
docker-compose up -d

# 全コンテナの健全性確認
./scripts/verify-health.sh
```

### 2. パフォーマンステスト
```bash
# 基本的な負荷テスト
npm run test:performance -- --containers=4

# アルゴリズム比較
npm run test:algorithms

# リソース競合テスト
npm run test:resource-contention
```

### 3. カオスエンジニアリング
```bash
# 単一コンテナ障害
npm run chaos:kill-container app-2

# 複数コンテナ障害
npm run chaos:kill-multiple app-1,app-3

# リソース枯渇
npm run chaos:memory-pressure app-4
```

## 監視とデバッグ

### メトリクスダッシュボード
```bash
# Grafanaダッシュボードにアクセス
open http://localhost:3000

# リアルタイムメトリクス
watch -n 1 'curl -s http://localhost:8080/metrics | jq'
```

### ログ集約
```bash
# 全コンテナのログを統合表示
docker-compose logs -f --tail=100

# 特定パターンの検索
docker-compose logs | grep -E "(ERROR|WARN|circuit)"
```

## 成功基準

- [ ] 4コンテナで3000+ RPSの処理
- [ ] 単一/複数障害時の99.9%可用性
- [ ] 動的重み付けによる15%以上の性能向上
- [ ] リソース競合時の公平な劣化（Fairness > 0.8）
- [ ] 各種アルゴリズムの特性理解

## トラブルシューティング

### 問題: 特定コンテナへの偏り
```javascript
// 重み付けのリセット
orchestrator.resetWeights();

// 手動での重み調整
orchestrator.setWeight('app-3', 2);
```

### 問題: カスケード障害
```nginx
# より保守的な設定に変更
proxy_next_upstream_tries 2;
proxy_next_upstream_timeout 2s;
```

### 問題: メモリ不足
```yaml
# スワップの有効化（開発環境のみ）
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

## 次のステップ

4コンテナでの限界を確認後、`07_container_shared_filedb`で共有リソースの問題に取り組みます。

## 学んだこと

- 4コンテナでも効果的なスケーリングが可能
- 動的な負荷分散の重要性
- リソース競合の影響は無視できない
- 複雑性の増大とその管理方法

## 参考資料

- [NGINX Dynamic Upstreams](https://www.nginx.com/blog/dynamic-upstreams/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Container Resource Management](https://docs.docker.com/config/containers/resource_constraints/)
- [Chaos Engineering Principles](https://principlesofchaos.org/)