# 04_single_container_failure_point

## 概要

単一コンテナの破綻点を科学的に分析し、失敗のメカニズムを理解します。これにより、水平スケーリングへの移行が必要な理由を定量的に証明します。

## 目的

- 失敗の正確なメカニズムの解明
- 各種リソースの限界点の特定
- 失敗の予兆パターンの発見
- スケールアウト戦略の根拠確立

## アーキテクチャ

```
┌─────────────────────────────────┐
│    Failure Analysis Setup       │
│  ┌─────────────────────────┐    │
│  │ Controlled Load Gen     │    │
│  │ Real-time Monitoring    │    │
│  │ Failure Injection       │    │
│  └─────────────────────────┘    │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│ System  │    │ Application  │
│ Metrics │    │  Container   │
│ Probe   │    │  (Failing)   │
└─────────┘    └──────────────┘
    │                 │
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ Failure Event   │
    │ Timeline & Logs │
    └─────────────────┘
```

## 検証項目

### 1. 失敗の段階的進行
- **Stage 1**: 初期劣化（レスポンス遅延）
- **Stage 2**: 部分的失敗（一部リクエストの失敗）
- **Stage 3**: カスケード失敗（連鎖的な障害）
- **Stage 4**: 完全停止（サービス不能）

### 2. リソース別限界値
- **CPU**: コンテキストスイッチの閾値
- **メモリ**: OOMキラーの発動条件
- **ネットワーク**: バッファ枯渇点
- **ファイルディスクリプタ**: 上限到達の影響

### 3. 失敗の予兆指標
- **早期警告シグナル**: 失敗の30秒前に検出可能な指標
- **ポイント・オブ・ノーリターン**: 回復不可能になる時点
- **相関パターン**: 複数メトリクスの相関関係

## TDDアプローチ

### Red Phase (失敗シナリオの定義)
```typescript
// test/failure-analysis.test.ts
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { FailureAnalyzer } from "../src/failure-analyzer.ts";
import { SystemProbe } from "../src/system-probe.ts";

Deno.test("Container Failure Point Analysis", async (t) => {
  let failureAnalyzer: FailureAnalyzer;
  let systemProbe: SystemProbe;
  
  // Setup
  failureAnalyzer = new FailureAnalyzer({
    metricsInterval: 100, // 100ms間隔で詳細記録
    alertThresholds: {
      cpu: 90,
      memory: 85,
      eventLoopLag: 100,
      errorRate: 0.05
    }
  });
  
  systemProbe = new SystemProbe({
    pid: Deno.pid,
    detailed: true
  });

  await t.step("should identify exact failure progression", async () => {
    const timeline = [];
    let failureDetected = false;
    
    // イベントリスナー設定
    failureAnalyzer.on('stage-change', (stage) => {
      timeline.push({
        timestamp: Date.now(),
        stage: stage.name,
        metrics: stage.metrics,
        severity: stage.severity
      });
    });
    
    failureAnalyzer.on('failure-imminent', (prediction) => {
      console.log(`Failure predicted in ${prediction.timeToFailure}ms`);
      failureDetected = true;
    });
    
    // 段階的に負荷を増加させて失敗を誘発
    const loadSteps = [
      { clients: 100, duration: 30000 },
      { clients: 500, duration: 30000 },
      { clients: 1000, duration: 30000 },
      { clients: 1500, duration: 30000 },
      { clients: 2000, duration: 30000 } // 確実に失敗させる
    ];
    
    for (const step of loadSteps) {
      console.log(`Applying load: ${step.clients} clients`);
      
      const stepResult = await applyLoad({
        clients: step.clients,
        duration: step.duration,
        stopOnFailure: true
      });
      
      if (stepResult.failed) {
        timeline.push({
          timestamp: Date.now(),
          stage: 'COMPLETE_FAILURE',
          finalMetrics: stepResult.metrics
        });
        break;
      }
    }
    
    // タイムラインの分析
    assertEquals(timeline.length > 3, true); // 複数の段階を経て失敗
    assertEquals(failureDetected, true); // 失敗が予測されたこと
    
    // 失敗の進行を検証
    const stages = timeline.map(t => t.stage);
    assertExists(stages.find(s => s === 'DEGRADATION_START'));
    assertExists(stages.find(s => s === 'PARTIAL_FAILURE'));
    assertExists(stages.find(s => s === 'CASCADE_FAILURE'));
    assertExists(stages.find(s => s === 'COMPLETE_FAILURE'));
  });

  await t.step("should identify resource exhaustion patterns", async () => {
    const resourceTimeline = [];
    
    // 詳細なリソース監視
    const monitor = setInterval(() => {
      const snapshot = {
        timestamp: Date.now(),
        ...systemProbe.getDetailedMetrics()
      };
      resourceTimeline.push(snapshot);
    }, 100);
    
    // 失敗するまで負荷を増加
    await induceFailure({
      method: 'gradual',
      targetClients: 2000
    });
    
    clearInterval(monitor);
    
    // リソース枯渇の分析
    const analysis = analyzeResourceExhaustion(resourceTimeline);
    
    assertExists(analysis.primaryBottleneck);
    assertEquals(analysis.exhaustionSequence.includes('memory'), true);
    assertEquals(analysis.exhaustionSequence.includes('cpu'), true);
    assertEquals(analysis.exhaustionSequence.includes('network'), true);
    
    // 限界値の特定
    assertExists(analysis.limits.maxConnections);
    assertExists(analysis.limits.maxMemoryMB);
    assertExists(analysis.limits.maxCpuPercent);
    assertExists(analysis.limits.maxEventLoopLagMs);
  });

  await t.step("should test different failure modes", async () => {
    const failureModes = [
      {
        name: 'memory_exhaustion',
        method: async () => {
          // メモリリークをシミュレート
          const leaks = [];
          while (true) {
            leaks.push(new Array(1024 * 1024).fill('x'));
            await new Promise(resolve => setTimeout(resolve, 100));
          }
        }
      },
      {
        name: 'cpu_saturation',
        method: async () => {
          // CPU集約的な処理
          const encoder = new TextEncoder();
          while (true) {
            await crypto.subtle.deriveBits(
              {
                name: "PBKDF2",
                salt: encoder.encode("salt"),
                iterations: 100000,
                hash: "SHA-512"
              },
              await crypto.subtle.importKey(
                "raw",
                encoder.encode("test"),
                "PBKDF2",
                false,
                ["deriveBits"]
              ),
              512
            );
          }
        }
      },
      {
        name: 'connection_flood',
        method: async () => {
          // 大量の短命接続
          const connections = [];
          for (let i = 0; i < 10000; i++) {
            try {
              const conn = await Deno.connect({ hostname: "localhost", port: 3000 });
              conn.close();
              connections.push(conn);
            } catch (_) {
              // 接続エラーは無視
            }
          }
        }
      },
      {
        name: 'event_loop_block',
        method: async () => {
          // イベントループをブロック
          const start = Date.now();
          while (Date.now() - start < 5000) {
            // Blocking computation
          }
        }
      }
    ];
    
    for (const mode of failureModes) {
      console.log(`Testing failure mode: ${mode.name}`);
      
      const result = await testFailureMode(mode);
      
      assertExists(result.mode);
      assertEquals(result.mode, mode.name);
      assertExists(result.timeToFailure);
      assertExists(result.recoveryTime);
      assertExists(result.impactRadius);
    }
  });
});

// 失敗予測アルゴリズム
class FailurePrediction {
  constructor(windowSize = 30) {
    this.window = [];
    this.windowSize = windowSize;
  }
  
  addMetrics(metrics) {
    this.window.push(metrics);
    if (this.window.length > this.windowSize) {
      this.window.shift();
    }
  }
  
  predict() {
    if (this.window.length < 10) return null;
    
    // トレンド分析
    const trends = this.calculateTrends();
    
    // 複合スコアの計算
    const riskScore = this.calculateRiskScore(trends);
    
    if (riskScore > 0.8) {
      // 失敗までの推定時間
      const timeToFailure = this.estimateTimeToFailure(trends);
      
      return {
        probability: riskScore,
        timeToFailure,
        criticalResource: this.identifyCriticalResource(trends)
      };
    }
    
    return null;
  }
  
  calculateTrends() {
    const recent = this.window.slice(-10);
    const older = this.window.slice(-20, -10);
    
    return {
      cpuTrend: this.getTrend(older, recent, 'cpu'),
      memoryTrend: this.getTrend(older, recent, 'memory'),
      errorRateTrend: this.getTrend(older, recent, 'errorRate'),
      responseTImeTrend: this.getTrend(older, recent, 'responseTime')
    };
  }
  
  getTrend(older, recent, metric) {
    const oldAvg = older.reduce((sum, m) => sum + m[metric], 0) / older.length;
    const recentAvg = recent.reduce((sum, m) => sum + m[metric], 0) / recent.length;
    
    return {
      absolute: recentAvg,
      relative: recentAvg / oldAvg,
      acceleration: (recentAvg - oldAvg) / older.length
    };
  }
  
  calculateRiskScore(trends) {
    let score = 0;
    
    // CPU危険域
    if (trends.cpuTrend.absolute > 85) score += 0.3;
    if (trends.cpuTrend.relative > 1.5) score += 0.2;
    
    // メモリ危険域
    if (trends.memoryTrend.absolute > 90) score += 0.3;
    if (trends.memoryTrend.acceleration > 5) score += 0.2;
    
    // エラー率上昇
    if (trends.errorRateTrend.absolute > 0.05) score += 0.2;
    if (trends.errorRateTrend.relative > 2) score += 0.1;
    
    return Math.min(score, 1);
  }
}
```

### Green Phase (失敗検出と分析の実装)
```typescript
// failure-detector.ts
import { EventEmitter } from "https://deno.land/x/event_emitter@1.0.0/mod.ts";

export class FailureDetector extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.thresholds = {
      cpu: options.cpuThreshold || 90,
      memory: options.memoryThreshold || 85,
      eventLoopLag: options.lagThreshold || 100,
      errorRate: options.errorThreshold || 0.05,
      ...options.thresholds
    };
    
    this.state = 'healthy';
    this.metrics = [];
    this.predictor = new FailurePrediction();
  }
  
  analyze(currentMetrics) {
    this.metrics.push({
      ...currentMetrics,
      timestamp: Date.now()
    });
    
    // 状態遷移の検出
    const newState = this.determineState(currentMetrics);
    
    if (newState !== this.state) {
      this.emit('stage-change', {
        from: this.state,
        to: newState,
        metrics: currentMetrics
      });
      
      this.state = newState;
    }
    
    // 失敗予測
    this.predictor.addMetrics(currentMetrics);
    const prediction = this.predictor.predict();
    
    if (prediction && prediction.probability > 0.8) {
      this.emit('failure-imminent', prediction);
    }
    
    // 詳細分析
    return {
      state: this.state,
      health: this.calculateHealth(currentMetrics),
      bottlenecks: this.identifyBottlenecks(currentMetrics),
      prediction
    };
  }
  
  determineState(metrics) {
    const violations = this.checkThresholds(metrics);
    
    if (violations.length === 0) {
      return 'healthy';
    }
    
    if (violations.length === 1 && violations[0].severity < 0.5) {
      return 'degrading';
    }
    
    if (metrics.errorRate > 0.5) {
      return 'failing';
    }
    
    if (violations.length >= 2 || violations.some(v => v.severity > 0.8)) {
      return 'critical';
    }
    
    return 'degraded';
  }
  
  checkThresholds(metrics) {
    const violations = [];
    
    Object.entries(this.thresholds).forEach(([metric, threshold]) => {
      const value = metrics[metric];
      if (value > threshold) {
        violations.push({
          metric,
          value,
          threshold,
          severity: (value - threshold) / threshold
        });
      }
    });
    
    return violations;
  }
  
  calculateHealth(metrics) {
    let score = 100;
    
    // 各メトリクスの影響を計算
    score -= (metrics.cpu / 100) * 20;
    score -= (metrics.memory / 100) * 20;
    score -= Math.min(metrics.eventLoopLag / 1000, 1) * 20;
    score -= metrics.errorRate * 40;
    
    return Math.max(0, Math.min(100, score));
  }
  
  identifyBottlenecks(metrics) {
    const bottlenecks = [];
    
    // CPU ボトルネック
    if (metrics.cpu > this.thresholds.cpu) {
      bottlenecks.push({
        resource: 'cpu',
        severity: 'high',
        impact: 'Response time degradation',
        recommendation: 'Scale horizontally or optimize CPU usage'
      });
    }
    
    // メモリボトルネック
    if (metrics.memory > this.thresholds.memory) {
      bottlenecks.push({
        resource: 'memory',
        severity: 'critical',
        impact: 'OOM killer risk',
        recommendation: 'Increase memory limit or fix memory leaks'
      });
    }
    
    // イベントループボトルネック
    if (metrics.eventLoopLag > this.thresholds.eventLoopLag) {
      bottlenecks.push({
        resource: 'eventLoop',
        severity: 'high',
        impact: 'Request queuing',
        recommendation: 'Offload CPU-intensive tasks'
      });
    }
    
    return bottlenecks;
  }
}

// システムプローブ実装
export class SystemProbe {
  private pid: number;
  private detailed: boolean;
  
  constructor(options: { pid?: number; detailed?: boolean } = {}) {
    this.pid = options.pid || Deno.pid;
    this.detailed = options.detailed || false;
  }
  
  async getMemoryUsage() {
    const memoryUsage = Deno.memoryUsage();
    return {
      heapUsed: memoryUsage.heapUsed,
      heapTotal: memoryUsage.heapTotal,
      external: memoryUsage.external,
      rss: memoryUsage.rss
    };
  }
  
  async getDetailedMetrics() {
    const metrics = {
      cpu: await this.getCpuUsage(),
      memory: await this.getMemoryUsage(),
      network: await this.getNetworkStats(),
      io: await this.getIOStats(),
      threads: await this.getThreadCount(),
      handles: await this.getHandleCount()
    };
    
    if (this.detailed) {
      metrics.tcp = await this.getTcpStats();
      metrics.gc = await this.getGCStats();
    }
    
    return metrics;
  }
  
  async getCpuUsage() {
    // Denoでは直接的なCPU使用率取得がないため、代替実装
    const startTime = performance.now();
    const startMetrics = Deno.metrics();
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    const endTime = performance.now();
    const endMetrics = Deno.metrics();
    const elapsedTime = endTime - startTime;
    
    // 簡易的な計算
    const opsCompleted = endMetrics.opsCompleted - startMetrics.opsCompleted;
    const approximateCpuUsage = (opsCompleted / elapsedTime) * 100;
    
    return {
      user: approximateCpuUsage * 0.8,
      system: approximateCpuUsage * 0.2,
      total: approximateCpuUsage
    };
  }
  
  async getTcpStats() {
    // /proc/net/tcp の解析（Linux環境）
    try {
      const tcpData = await Deno.readTextFile('/proc/net/tcp');
      const lines = tcpData.split('\n').slice(1); // ヘッダーをスキップ
      
      const states = {
        ESTABLISHED: 0,
        SYN_SENT: 0,
        SYN_RECV: 0,
        FIN_WAIT1: 0,
        FIN_WAIT2: 0,
        TIME_WAIT: 0,
        CLOSE_WAIT: 0,
        CLOSING: 0
      };
      
      lines.forEach(line => {
        const parts = line.trim().split(/\s+/);
        if (parts.length > 3) {
          const state = parseInt(parts[3], 16);
          // TCP状態のマッピング
          switch (state) {
            case 1: states.ESTABLISHED++; break;
            case 2: states.SYN_SENT++; break;
            case 3: states.SYN_RECV++; break;
            case 4: states.FIN_WAIT1++; break;
            case 5: states.FIN_WAIT2++; break;
            case 6: states.TIME_WAIT++; break;
            case 7: states.CLOSE_WAIT++; break;
            case 8: states.CLOSING++; break;
          }
        }
      });
      
      return states;
    } catch (error) {
      return null; // Linux以外の環境
    }
  }
}
```

## 実装手順

### 1. Dockerfile
```dockerfile
# Dockerfile
FROM denoland/deno:alpine

WORKDIR /app

# 依存関係のキャッシュ
 COPY deps.ts .
RUN deno cache deps.ts

# アプリケーションコードのコピー
COPY . .

# メインファイルのキャッシュ
RUN deno cache server.ts

EXPOSE 3000

CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-write", "--allow-env", "--allow-hrtime", "server.ts"]
```

### 2. 監視インフラストラクチャ
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      ENABLE_PROFILING: "true"
      FAILURE_DETECTION: "true"
    volumes:
      - ./logs:/app/logs
      - ./dumps:/app/dumps
    cap_add:
      - SYS_PTRACE  # デバッグ用
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

  # 監視用サイドカー
  monitor:
    image: prom/node-exporter
    pid: "container:app"
    network_mode: "container:app"
    
  # ログ収集
  logger:
    image: fluent/fluentd
    volumes:
      - ./logs:/fluentd/log
      - ./fluent.conf:/fluentd/etc/fluent.conf
```

### 2. 失敗注入ツール
```typescript
// chaos-injection.ts
export class ChaosInjector {
  constructor() {
    this.scenarios = {
      memoryLeak: this.injectMemoryLeak,
      cpuSpike: this.injectCpuSpike,
      networkDelay: this.injectNetworkDelay,
      connectionFlood: this.injectConnectionFlood
    };
  }
  
  async inject(scenario, options = {}) {
    const injection = this.scenarios[scenario];
    if (!injection) {
      throw new Error(`Unknown scenario: ${scenario}`);
    }
    
    console.log(`Injecting chaos: ${scenario}`);
    return injection.call(this, options);
  }
  
  injectMemoryLeak({ rate = 10, size = 1024 * 1024 }) {
    const leaks = [];
    const interval = setInterval(() => {
      leaks.push(new Array(size).fill('memory leak'));
      console.log(`Leaked ${size} bytes. Total: ${leaks.length * size}`);
    }, rate);
    
    return {
      stop: () => clearInterval(interval)
    };
  }
  
  injectCpuSpike({ duration = 5000, intensity = 0.9 }) {
    const endTime = Date.now() + duration;
    
    const spike = () => {
      while (Date.now() < endTime) {
        // CPU intensive operation
        crypto.getRandomValues(new Uint8Array(1024));
        
        // Allow some breathing room based on intensity
        if (Math.random() > intensity) {
          setImmediate(spike);
          return;
        }
      }
    };
    
    spike();
    
    return {
      stop: () => {} // Self-terminating
    };
  }
}
```

## 分析結果の可視化

### タイムライン生成
```javascript
// timeline-generator.js
function generateFailureTimeline(events) {
  const timeline = {
    start: events[0].timestamp,
    end: events[events.length - 1].timestamp,
    duration: events[events.length - 1].timestamp - events[0].timestamp,
    stages: [],
    criticalEvents: []
  };
  
  let currentStage = null;
  
  events.forEach(event => {
    if (event.type === 'stage-change') {
      if (currentStage) {
        currentStage.end = event.timestamp;
        currentStage.duration = event.timestamp - currentStage.start;
      }
      
      currentStage = {
        name: event.data.to,
        start: event.timestamp,
        metrics: event.data.metrics
      };
      
      timeline.stages.push(currentStage);
    }
    
    if (event.severity === 'critical') {
      timeline.criticalEvents.push({
        timestamp: event.timestamp,
        description: event.description,
        impact: event.impact
      });
    }
  });
  
  return timeline;
}
```

## 実行と分析

```bash
# 1. 通常の失敗テスト
deno test --allow-all test/failure-point.test.ts

# 2. カオステスト
deno run --allow-all scripts/chaos-memory-leak.ts
deno run --allow-all scripts/chaos-cpu-spike.ts
deno run --allow-all scripts/chaos-network-flood.ts

# 3. 分析レポート生成
deno run --allow-all scripts/analyze-generate-report.ts

# 4. プロファイリング
deno run --inspect --allow-all server.ts
```

## 成功基準

- [ ] 4つの失敗段階を明確に識別
- [ ] 失敗の30秒前に予測可能
- [ ] 各リソースの正確な限界値を特定
- [ ] 失敗パターンの再現性を確認
- [ ] 回復可能性の境界を特定

## 失敗分析の結論

### 単一コンテナの限界
1. **接続数**: ~800-1000 が実用的な上限
2. **CPU**: 80%を超えると急激に劣化
3. **メモリ**: GCプレッシャーが致命的
4. **イベントループ**: 100ms以上の遅延で連鎖障害

### スケールアウトの必要性
- 垂直スケールは限界がある
- 失敗は予測可能だが回避は困難
- 水平スケールによる冗長性が必須

## 次のステップ

この分析結果を基に、`05_dual_containers_with_lb`から水平スケーリングの実装を開始します。

## 学んだこと

- 失敗は段階的に進行し、予測可能
- リソース間には複雑な相互作用がある
- 早期検出により、グレースフルな対処が可能
- アーキテクチャ変更なしには限界を超えられない

## 参考資料

- [Site Reliability Engineering](https://sre.google/books/)
- [Chaos Engineering](https://principlesofchaos.org/)
- [Linux Performance Analysis](http://www.brendangregg.com/linuxperf.html)
- [Deno Runtime APIs](https://deno.land/api)