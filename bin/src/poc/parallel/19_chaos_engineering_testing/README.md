# 19_chaos_engineering_testing

## 概要

カオスエンジニアリングの原則を適用し、本番環境での予期しない障害に対するシステムの回復力を検証します。制御された障害注入により、弱点を発見し、信頼性を向上させます。

## 目的

- 制御された障害実験の実施
- システムの回復力の測定
- 未知の脆弱性の発見
- 運用チームの対応能力向上

## アーキテクチャ

```
┌─────────────────────────────────────┐
│      Chaos Control Center           │
│  ┌─────────┬──────────┬─────────┐  │
│  │ Chaos   │Experiment │ Report  │  │
│  │ Mesh    │Scheduler  │ Engine  │  │
│  └─────────┴──────────┴─────────┘  │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
┌───▼───┐  ┌──▼───┐  ┌──▼───┐  ┌──▼───┐
│Network│  │ Pod  │  │ Node │  │ I/O  │
│ Chaos │  │Chaos │  │Chaos │  │Chaos │
│       │  │      │  │      │  │      │
│Latency│  │Kill  │  │Drain │  │Delay │
│Packet │  │CPU   │  │Reboot│  │Error │
│Loss   │  │Memory│  │Disk  │  │      │
└───────┘  └──────┘  └──────┘  └──────┘
    │          │          │          │
    └──────────┼──────────┼──────────┘
               │          │
         [Target System]
```

## 検証項目

### 1. インフラストラクチャカオス
- **ノード障害**: 突然のシャットダウン、再起動
- **ネットワーク分断**: パーティション、遅延、パケットロス
- **リソース枯渇**: CPU、メモリ、ディスク
- **時刻のずれ**: NTPドリフト、クロックスキュー

### 2. アプリケーションカオス
- **Pod削除**: ランダムなPod終了
- **依存関係障害**: サービス間通信の妨害
- **データ破損**: 一時的なデータ不整合
- **設定変更**: 環境変数、設定ファイル

### 3. データレイヤーカオス
- **データベース障害**: プライマリ失敗、レプリカ遅延
- **キャッシュ無効化**: Redis/Memcached障害
- **メッセージキュー**: Kafka/RabbitMQ障害
- **ストレージ障害**: ディスク満杯、I/Oエラー

### 4. セキュリティカオス
- **証明書期限切れ**: TLS証明書の無効化
- **認証障害**: IDプロバイダーの停止
- **権限昇格**: RBAC設定の変更
- **DDoS攻撃**: トラフィックフラッド

## TDDアプローチ

### Red Phase (カオス実験のテスト)
```javascript
// test/chaos-engineering.test.js
const { ChaosOrchestrator, SteadyStateValidator } = require('../src/chaos');
const k8s = require('@kubernetes/client-node');

describe('Chaos Engineering Experiments', () => {
  let chaosOrchestrator;
  let steadyState;
  let targetSystem;
  
  beforeAll(async () => {
    // カオスオーケストレーターの初期化
    chaosOrchestrator = new ChaosOrchestrator({
      kubeconfig: process.env.KUBECONFIG,
      namespace: 'production',
      experiments: {
        blast_radius: 'controlled', // controlled, limited, wide
        duration: '5m',
        dry_run: false
      }
    });
    
    // 定常状態の定義
    steadyState = new SteadyStateValidator({
      metrics: {
        availability: { min: 0.999 },
        latency_p99: { max: 100 }, // ms
        error_rate: { max: 0.001 },
        throughput: { min: 1000 } // req/s
      }
    });
    
    // ターゲットシステムの特定
    targetSystem = {
      deployment: 'web-app',
      namespace: 'production',
      replicas: 5
    };
  });

  it('should survive random pod failures', async () => {
    // 実験の定義
    const experiment = {
      name: 'pod-chaos-test',
      type: 'pod-failure',
      target: {
        selector: {
          app: 'web-app',
          tier: 'frontend'
        },
        mode: 'fixed-percent',
        value: 40 // 40%のPodを削除
      },
      duration: '5m',
      interval: '30s'
    };
    
    // 定常状態の確認
    const initialState = await steadyState.validate();
    expect(initialState.healthy).toBe(true);
    
    // カオス実験の実行
    const chaosJob = await chaosOrchestrator.runExperiment(experiment);
    
    // 実験中の監視
    const monitoringResults = [];
    const monitor = setInterval(async () => {
      const state = await steadyState.getCurrentState();
      monitoringResults.push({
        timestamp: Date.now(),
        ...state
      });
      
      // SLO違反のチェック
      if (state.availability < 0.995) {
        console.warn('SLO violation detected:', state);
      }
    }, 5000); // 5秒ごと
    
    // 実験完了を待つ
    await chaosJob.waitForCompletion();
    clearInterval(monitor);
    
    // 結果の分析
    const analysis = analyzeResults(monitoringResults);
    
    // システムが回復したか
    const finalState = await steadyState.validate();
    expect(finalState.healthy).toBe(true);
    
    // 可用性が閾値を下回らなかったか
    expect(analysis.minAvailability).toBeGreaterThan(0.995);
    
    // エラー率が許容範囲内か
    expect(analysis.maxErrorRate).toBeLessThan(0.01);
    
    // 自動回復時間
    expect(analysis.recoveryTime).toBeLessThan(60000); // 1分以内
  });

  it('should handle network partitions', async () => {
    // ネットワーク分断実験
    const experiment = {
      name: 'network-partition',
      type: 'network-chaos',
      target: {
        source: {
          selector: { app: 'web-app' }
        },
        destination: {
          selector: { app: 'database' }
        }
      },
      action: 'partition',
      duration: '3m',
      direction: 'both'
    };
    
    // トラフィックジェネレーターの起動
    const trafficGen = new TrafficGenerator({
      target: 'http://web-app-service',
      rps: 100,
      duration: '10m'
    });
    
    await trafficGen.start();
    
    // ベースライン測定（30秒）
    await new Promise(resolve => setTimeout(resolve, 30000));
    const baseline = await trafficGen.getStats();
    
    // カオス注入
    const chaosJob = await chaosOrchestrator.runExperiment(experiment);
    
    // リアルタイムメトリクス収集
    const chaosMetrics = [];
    const metricsCollector = setInterval(async () => {
      const metrics = await collectMetrics();
      chaosMetrics.push(metrics);
      
      // 分断の影響を確認
      if (metrics.databaseConnections === 0) {
        console.log('Database partition detected');
      }
    }, 1000);
    
    await chaosJob.waitForCompletion();
    clearInterval(metricsCollector);
    
    // 回復の確認
    await new Promise(resolve => setTimeout(resolve, 30000));
    const recovered = await trafficGen.getStats();
    
    // 分析
    const impact = analyzeNetworkPartitionImpact(baseline, chaosMetrics, recovered);
    
    // グレースフルデグラデーション
    expect(impact.completeFailures).toBe(0);
    expect(impact.degradedResponses).toBeGreaterThan(0);
    
    // キャッシュの有効性
    expect(impact.cacheHitRate).toBeGreaterThan(0.8);
    
    // 自動フェイルオーバー
    expect(impact.failoverTime).toBeLessThan(10000); // 10秒以内
    
    await trafficGen.stop();
  });

  it('should survive cascading failures', async () => {
    // カスケード障害シナリオ
    const scenario = {
      name: 'cascading-failure',
      stages: [
        {
          name: 'initial-trigger',
          experiment: {
            type: 'resource-chaos',
            target: { selector: { app: 'api-gateway' } },
            action: 'cpu-stress',
            stress: { cores: 2, load: 90 }
          },
          duration: '1m'
        },
        {
          name: 'secondary-failure',
          experiment: {
            type: 'latency-injection',
            target: { 
              source: { selector: { app: 'api-gateway' } },
              destination: { selector: { app: 'backend-service' } }
            },
            latency: '500ms',
            jitter: '100ms'
          },
          duration: '2m',
          delay: '30s' // 最初の実験から30秒後
        },
        {
          name: 'tertiary-failure',
          experiment: {
            type: 'pod-failure',
            target: { selector: { app: 'cache-service' } },
            mode: 'all'
          },
          duration: '1m',
          delay: '1m'
        }
      ]
    };
    
    // サーキットブレーカーの状態を監視
    const circuitBreakerMonitor = new CircuitBreakerMonitor({
      services: ['api-gateway', 'backend-service', 'cache-service']
    });
    
    await circuitBreakerMonitor.start();
    
    // シナリオの実行
    const scenarioRunner = await chaosOrchestrator.runScenario(scenario);
    
    // 各ステージでの影響を記録
    const stageImpacts = [];
    
    scenarioRunner.on('stage-start', (stage) => {
      console.log(`Starting stage: ${stage.name}`);
    });
    
    scenarioRunner.on('stage-complete', async (stage) => {
      const impact = await assessImpact();
      stageImpacts.push({
        stage: stage.name,
        impact
      });
    });
    
    await scenarioRunner.waitForCompletion();
    
    // サーキットブレーカーの動作確認
    const cbStats = await circuitBreakerMonitor.getStats();
    
    // 適切なタイミングでサーキットが開いたか
    expect(cbStats['api-gateway'].openCount).toBeGreaterThan(0);
    expect(cbStats['backend-service'].openCount).toBeGreaterThan(0);
    
    // カスケード障害が防げたか
    const totalFailures = stageImpacts.reduce((sum, s) => 
      sum + s.impact.failedRequests, 0
    );
    
    const totalRequests = stageImpacts.reduce((sum, s) => 
      sum + s.impact.totalRequests, 0
    );
    
    const failureRate = totalFailures / totalRequests;
    expect(failureRate).toBeLessThan(0.1); // 10%以下
    
    // 自己回復
    const finalHealth = await steadyState.validate();
    expect(finalHealth.healthy).toBe(true);
  });

  it('should test disaster recovery procedures', async () => {
    // 災害復旧シナリオ
    const disaster = {
      name: 'datacenter-failure',
      type: 'zone-failure',
      target: {
        zone: 'us-east-1a',
        resources: ['compute', 'storage', 'network']
      },
      duration: '10m'
    };
    
    // RPO/RTOの測定準備
    const drMetrics = new DisasterRecoveryMetrics({
      rpo_target: 60, // 60秒
      rto_target: 300 // 5分
    });
    
    // データ整合性チェッカー
    const dataIntegrity = new DataIntegrityChecker({
      databases: ['primary-db', 'replica-db'],
      criticalTables: ['users', 'transactions', 'orders']
    });
    
    // 災害前のチェックポイント
    const checkpoint = await dataIntegrity.createCheckpoint();
    
    // 災害シミュレーション開始
    const disasterStart = Date.now();
    const disasterJob = await chaosOrchestrator.runExperiment(disaster);
    
    // 自動フェイルオーバーの監視
    const failoverMonitor = setInterval(async () => {
      const topology = await getClusterTopology();
      
      if (topology.primaryZone !== 'us-east-1a') {
        const failoverTime = Date.now() - disasterStart;
        console.log(`Failover completed in ${failoverTime}ms`);
        drMetrics.recordFailover(failoverTime);
      }
    }, 1000);
    
    // RPOの測定（最後に同期されたデータ）
    const lastSyncedData = await getLastSyncedTimestamp();
    const dataLoss = disasterStart - lastSyncedData;
    drMetrics.recordRPO(dataLoss / 1000); // 秒単位
    
    await disasterJob.waitForCompletion();
    clearInterval(failoverMonitor);
    
    // 復旧後のデータ整合性チェック
    const integrityCheck = await dataIntegrity.compareWithCheckpoint(checkpoint);
    
    // メトリクスの検証
    const drReport = drMetrics.generateReport();
    
    // RPO達成
    expect(drReport.actualRPO).toBeLessThan(60);
    
    // RTO達成  
    expect(drReport.actualRTO).toBeLessThan(300);
    
    // データ整合性
    expect(integrityCheck.discrepancies).toEqual([]);
    expect(integrityCheck.dataLoss).toBe(0);
    
    // サービス可用性
    expect(drReport.availabilityDuringDisaster).toBeGreaterThan(0.99);
  });

  it('should validate security chaos scenarios', async () => {
    // セキュリティカオス実験
    const securityChaos = {
      name: 'security-chaos',
      experiments: [
        {
          type: 'certificate-expiry',
          target: { service: 'api-gateway' },
          action: 'expire-cert'
        },
        {
          type: 'auth-service-failure',
          target: { service: 'oauth-provider' },
          action: 'shutdown'
        },
        {
          type: 'rbac-mutation',
          target: { 
            serviceAccount: 'app-service-account',
            namespace: 'production'
          },
          action: 'remove-permissions'
        }
      ]
    };
    
    // セキュリティ監視
    const securityMonitor = new SecurityMonitor({
      alertThresholds: {
        authFailures: 100,
        unauthorizedAccess: 10,
        certificateErrors: 50
      }
    });
    
    await securityMonitor.start();
    
    // 各セキュリティ実験の実行
    for (const experiment of securityChaos.experiments) {
      console.log(`Running security experiment: ${experiment.type}`);
      
      const job = await chaosOrchestrator.runExperiment(experiment);
      
      // セキュリティイベントの監視
      const events = [];
      const eventCollector = setInterval(async () => {
        const newEvents = await securityMonitor.getEvents();
        events.push(...newEvents);
      }, 1000);
      
      await job.waitForCompletion();
      clearInterval(eventCollector);
      
      // 適切なエラーハンドリング
      const analysis = analyzeSecurityEvents(events);
      
      switch (experiment.type) {
        case 'certificate-expiry':
          // 証明書の自動更新または適切なエラーメッセージ
          expect(analysis.certRenewalAttempts).toBeGreaterThan(0);
          expect(analysis.tlsErrors).toBeGreaterThan(0);
          expect(analysis.serviceDowntime).toBe(0); // ダウンタイムなし
          break;
          
        case 'auth-service-failure':
          // キャッシュされた認証トークンの使用
          expect(analysis.cachedAuthUsage).toBeGreaterThan(0);
          expect(analysis.completeAuthFailures).toBeLessThan(10);
          break;
          
        case 'rbac-mutation':
          // 権限エラーの適切な処理
          expect(analysis.forbiddenResponses).toBeGreaterThan(0);
          expect(analysis.privilegeEscalations).toBe(0);
          break;
      }
    }
    
    // セキュリティアラートの確認
    const alerts = await securityMonitor.getAlerts();
    expect(alerts.critical).toEqual([]);
  });

  it('should perform game day exercises', async () => {
    // ゲームデイ演習 - 複数チームでの対応訓練
    const gameDay = new GameDayExercise({
      scenario: 'black-friday-load',
      teams: ['sre', 'development', 'support'],
      duration: '2h',
      objectives: [
        'Maintain 99.9% availability',
        'Keep p99 latency under 200ms',
        'Scale to 10x normal load',
        'Coordinate incident response'
      ]
    });
    
    // シナリオ: ブラックフライデーの負荷 + 障害
    const scenario = {
      phases: [
        {
          name: 'normal-load',
          duration: '10m',
          load: { rps: 1000 }
        },
        {
          name: 'gradual-increase',
          duration: '20m',
          load: { 
            rps: { start: 1000, end: 5000 },
            pattern: 'linear'
          }
        },
        {
          name: 'peak-load-with-failures',
          duration: '30m',
          load: { rps: 10000 },
          chaos: [
            {
              time: '+5m',
              experiment: {
                type: 'pod-failure',
                target: { selector: { app: 'web-app' } },
                mode: 'fixed',
                value: 2
              }
            },
            {
              time: '+15m',
              experiment: {
                type: 'database-slowdown',
                latency: '200ms'
              }
            }
          ]
        },
        {
          name: 'recovery',
          duration: '20m',
          load: { rps: 5000 }
        }
      ]
    };
    
    // 演習の開始
    await gameDay.start(scenario);
    
    // チームアクションの記録
    gameDay.on('team-action', (action) => {
      console.log(`[${action.team}] ${action.description}`);
    });
    
    // インシデント対応の追跡
    const incidentTracker = new IncidentTracker();
    
    gameDay.on('incident-detected', async (incident) => {
      const response = await incidentTracker.createIncident(incident);
      console.log(`Incident created: ${response.id}`);
    });
    
    // メトリクスの継続的な監視
    const performanceTracker = setInterval(async () => {
      const metrics = await collectSystemMetrics();
      gameDay.recordMetrics(metrics);
      
      // SLO違反の確認
      if (metrics.availability < 0.999) {
        gameDay.recordSLOViolation('availability', metrics.availability);
      }
      
      if (metrics.p99_latency > 200) {
        gameDay.recordSLOViolation('latency', metrics.p99_latency);
      }
    }, 5000);
    
    // 演習完了
    await gameDay.waitForCompletion();
    clearInterval(performanceTracker);
    
    // 結果の分析
    const report = await gameDay.generateReport();
    
    // 目標達成の確認
    expect(report.objectives.achieved).toContain('Scale to 10x normal load');
    
    // チームパフォーマンス
    expect(report.teamMetrics.sre.mttr).toBeLessThan(300000); // MTTR < 5分
    expect(report.teamMetrics.development.fixes_deployed).toBeGreaterThan(0);
    
    // インシデント対応
    expect(report.incidents.total).toBeGreaterThan(0);
    expect(report.incidents.resolved).toBe(report.incidents.total);
    
    // 学習項目
    expect(report.lessons_learned).toHaveLength(greaterThan(3));
    
    // 改善提案
    expect(report.improvements).toContain(
      expect.objectContaining({
        category: 'automation'
      })
    );
  });
});

// ヘルパー関数
function analyzeResults(monitoringResults) {
  return {
    minAvailability: Math.min(...monitoringResults.map(r => r.availability)),
    maxErrorRate: Math.max(...monitoringResults.map(r => r.errorRate)),
    recoveryTime: findRecoveryTime(monitoringResults)
  };
}

function findRecoveryTime(results) {
  const failureStart = results.findIndex(r => r.availability < 0.999);
  if (failureStart === -1) return 0;
  
  const recoveryPoint = results.slice(failureStart).findIndex(r => 
    r.availability >= 0.999
  );
  
  if (recoveryPoint === -1) return Infinity;
  
  return (recoveryPoint * 5000); // 5秒間隔
}
```

### Green Phase (カオスエンジニアリング実装)
```javascript
// chaos-orchestrator.ts
import { ChaosExperiment } from "./experiments.ts";

class ChaosOrchestrator {
  constructor(config) {
    this.config = config;
    this.kc = new k8s.KubeConfig();
    this.kc.loadFromDefault();
    
    this.k8sApi = this.kc.makeApiClient(k8s.CoreV1Api);
    this.customApi = this.kc.makeApiClient(k8s.CustomObjectsApi);
    
    this.experiments = new Map();
    this.scenarios = new Map();
  }
  
  async runExperiment(experimentConfig) {
    // 実験の検証
    this.validateExperiment(experimentConfig);
    
    // Blast Radius の確認
    const blastRadius = await this.calculateBlastRadius(experimentConfig);
    console.log(`Blast radius: ${blastRadius.affectedPods} pods, ${blastRadius.affectedServices} services`);
    
    if (blastRadius.risk === 'high' && this.config.experiments.blast_radius !== 'wide') {
      throw new Error('Experiment blast radius exceeds configured limits');
    }
    
    // Chaos Mesh CRD の作成
    const experiment = await this.createChaosExperiment(experimentConfig);
    
    // 実験の追跡
    this.experiments.set(experiment.id, experiment);
    
    // 監視の開始
    experiment.startMonitoring();
    
    return experiment;
  }
  
  async createChaosExperiment(config) {
    const manifest = this.generateChaosManifest(config);
    
    if (this.config.experiments.dry_run) {
      console.log('Dry run - would create:', JSON.stringify(manifest, null, 2));
      return new ChaosExperiment({ ...config, dryRun: true });
    }
    
    // Chaos Mesh リソースの作成
    const created = await this.customApi.createNamespacedCustomObject(
      'chaos-mesh.org',
      'v1alpha1',
      this.config.namespace,
      this.getChaosKind(config.type),
      manifest
    );
    
    return new ChaosExperiment({
      ...config,
      uid: created.body.metadata.uid,
      orchestrator: this
    });
  }
  
  generateChaosManifest(config) {
    switch (config.type) {
      case 'pod-failure':
        return this.generatePodChaos(config);
      case 'network-chaos':
        return this.generateNetworkChaos(config);
      case 'resource-chaos':
        return this.generateStressChaos(config);
      case 'time-chaos':
        return this.generateTimeChaos(config);
      default:
        throw new Error(`Unknown chaos type: ${config.type}`);
    }
  }
  
  generatePodChaos(config) {
    return {
      apiVersion: 'chaos-mesh.org/v1alpha1',
      kind: 'PodChaos',
      metadata: {
        name: config.name,
        namespace: this.config.namespace
      },
      spec: {
        action: config.action || 'pod-kill',
        mode: config.target.mode,
        value: config.target.value?.toString(),
        duration: config.duration,
        selector: {
          namespaces: [this.config.namespace],
          labelSelectors: config.target.selector
        },
        scheduler: {
          cron: config.schedule || `@every ${config.interval || '30s'}`
        }
      }
    };
  }
  
  generateNetworkChaos(config) {
    return {
      apiVersion: 'chaos-mesh.org/v1alpha1',
      kind: 'NetworkChaos',
      metadata: {
        name: config.name,
        namespace: this.config.namespace
      },
      spec: {
        action: config.action,
        mode: 'all',
        selector: {
          namespaces: [this.config.namespace],
          labelSelectors: config.target.source.selector
        },
        target: {
          mode: 'all',
          selector: {
            namespaces: [this.config.namespace],
            labelSelectors: config.target.destination.selector
          }
        },
        duration: config.duration,
        direction: config.direction || 'both',
        ...(config.action === 'delay' && {
          delay: {
            latency: config.latency,
            jitter: config.jitter,
            correlation: config.correlation || '0'
          }
        }),
        ...(config.action === 'loss' && {
          loss: {
            loss: config.loss,
            correlation: config.correlation || '0'
          }
        }),
        ...(config.action === 'partition' && {
          partition: {
            direction: config.direction
          }
        })
      }
    };
  }
  
  generateStressChaos(config) {
    return {
      apiVersion: 'chaos-mesh.org/v1alpha1',
      kind: 'StressChaos',
      metadata: {
        name: config.name,
        namespace: this.config.namespace
      },
      spec: {
        mode: 'all',
        selector: {
          namespaces: [this.config.namespace],
          labelSelectors: config.target.selector
        },
        stressors: {
          ...(config.action === 'cpu-stress' && {
            cpu: {
              workers: config.stress.cores,
              load: config.stress.load
            }
          }),
          ...(config.action === 'memory-stress' && {
            memory: {
              workers: config.stress.workers || 1,
              size: config.stress.size
            }
          }),
          ...(config.action === 'io-stress' && {
            io: {
              workers: config.stress.workers || 1,
              size: config.stress.size || '1M',
              path: config.stress.path || '/tmp'
            }
          })
        },
        duration: config.duration
      }
    };
  }
  
  async calculateBlastRadius(experiment) {
    // 影響を受けるリソースの特定
    const selector = experiment.target.selector;
    
    const pods = await this.k8sApi.listNamespacedPod(
      this.config.namespace,
      undefined,
      undefined,
      undefined,
      undefined,
      this.labelSelectorToString(selector)
    );
    
    const affectedPods = pods.body.items;
    const affectedServices = await this.findAffectedServices(affectedPods);
    const dependencies = await this.traceDependencies(affectedServices);
    
    const risk = this.assessRisk(affectedPods.length, dependencies.critical);
    
    return {
      affectedPods: affectedPods.length,
      affectedServices: affectedServices.length,
      criticalDependencies: dependencies.critical,
      risk
    };
  }
  
  assessRisk(podCount, criticalDeps) {
    if (criticalDeps > 0 || podCount > 10) return 'high';
    if (podCount > 5) return 'medium';
    return 'low';
  }
  
  async runScenario(scenarioConfig) {
    const scenario = new ChaosScenario(scenarioConfig, this);
    this.scenarios.set(scenario.id, scenario);
    
    await scenario.execute();
    
    return scenario;
  }
  
  getChaosKind(type) {
    const kindMap = {
      'pod-failure': 'podchaos',
      'network-chaos': 'networkchaos',
      'resource-chaos': 'stresschaos',
      'time-chaos': 'timechaos',
      'io-chaos': 'iochaos',
      'kernel-chaos': 'kernelchaos',
      'dns-chaos': 'dnschaos',
      'http-chaos': 'httpchaos'
    };
    
    return kindMap[type] || 'chaos';
  }
  
  labelSelectorToString(selector) {
    return Object.entries(selector)
      .map(([key, value]) => `${key}=${value}`)
      .join(',');
  }
}

// 定常状態検証
class SteadyStateValidator {
  constructor(config) {
    this.metrics = config.metrics;
    this.prometheus = new PrometheusClient({
      url: process.env.PROMETHEUS_URL || 'http://prometheus:9090'
    });
  }
  
  async validate() {
    const currentState = await this.getCurrentState();
    const violations = [];
    
    for (const [metric, constraints] of Object.entries(this.metrics)) {
      const value = currentState[metric];
      
      if (constraints.min !== undefined && value < constraints.min) {
        violations.push({
          metric,
          constraint: 'min',
          expected: constraints.min,
          actual: value
        });
      }
      
      if (constraints.max !== undefined && value > constraints.max) {
        violations.push({
          metric,
          constraint: 'max',
          expected: constraints.max,
          actual: value
        });
      }
    }
    
    return {
      healthy: violations.length === 0,
      violations,
      state: currentState
    };
  }
  
  async getCurrentState() {
    const queries = {
      availability: 'avg(up{job="kubernetes-pods"})',
      latency_p99: 'histogram_quantile(0.99, http_request_duration_seconds_bucket)',
      error_rate: 'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))',
      throughput: 'sum(rate(http_requests_total[5m]))'
    };
    
    const state = {};
    
    for (const [metric, query] of Object.entries(queries)) {
      const result = await this.prometheus.query(query);
      state[metric] = this.extractValue(result);
    }
    
    return state;
  }
  
  extractValue(prometheusResult) {
    if (prometheusResult.data.result.length > 0) {
      return parseFloat(prometheusResult.data.result[0].value[1]);
    }
    return 0;
  }
}

// カオス実験クラス
class ChaosExperiment {
  constructor(config) {
    this.config = config;
    this.id = config.uid || `experiment-${Date.now()}`;
    this.status = 'pending';
    this.startTime = null;
    this.endTime = null;
    this.metrics = [];
  }
  
  startMonitoring() {
    this.monitoringInterval = setInterval(async () => {
      const metrics = await this.collectMetrics();
      this.metrics.push({
        timestamp: Date.now(),
        ...metrics
      });
    }, 5000);
  }
  
  async waitForCompletion() {
    if (this.config.dryRun) {
      await this.simulateDryRun();
      return;
    }
    
    this.startTime = Date.now();
    
    // 実験の期間を待つ
    const duration = this.parseDuration(this.config.duration);
    await new Promise(resolve => setTimeout(resolve, duration));
    
    this.endTime = Date.now();
    this.status = 'completed';
    
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }
  }
  
  parseDuration(duration) {
    const match = duration.match(/(\d+)([smh])/);
    if (!match) return 60000; // デフォルト1分
    
    const value = parseInt(match[1]);
    const unit = match[2];
    
    switch (unit) {
      case 's': return value * 1000;
      case 'm': return value * 60 * 1000;
      case 'h': return value * 60 * 60 * 1000;
      default: return 60000;
    }
  }
  
  async simulateDryRun() {
    console.log(`Dry run simulation for ${this.config.duration}`);
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
  
  async collectMetrics() {
    // 実験中のメトリクス収集
    return {
      podFailures: await this.countPodFailures(),
      errorRate: await this.getErrorRate(),
      latency: await this.getLatency()
    };
  }
}

// カオスシナリオ
class ChaosScenario extends EventEmitter {
  constructor(config, orchestrator) {
    super();
    this.config = config;
    this.orchestrator = orchestrator;
    this.id = `scenario-${Date.now()}`;
    this.stages = config.stages;
    this.currentStage = -1;
  }
  
  async execute() {
    for (let i = 0; i < this.stages.length; i++) {
      const stage = this.stages[i];
      this.currentStage = i;
      
      this.emit('stage-start', stage);
      
      // 遅延がある場合は待機
      if (stage.delay) {
        await this.wait(stage.delay);
      }
      
      // 実験の実行
      const experiment = await this.orchestrator.runExperiment(stage.experiment);
      await experiment.waitForCompletion();
      
      this.emit('stage-complete', stage);
    }
    
    this.emit('scenario-complete');
  }
  
  async wait(delay) {
    const ms = this.parseDuration(delay);
    await new Promise(resolve => setTimeout(resolve, ms));
  }
  
  parseDuration(duration) {
    // ChaosExperiment.parseDuration と同じ
    const match = duration.match(/(\d+)([smh])/);
    if (!match) return 0;
    
    const value = parseInt(match[1]);
    const unit = match[2];
    
    switch (unit) {
      case 's': return value * 1000;
      case 'm': return value * 60 * 1000;
      case 'h': return value * 60 * 60 * 1000;
      default: return 0;
    }
  }
}

// ゲームデイ演習
class GameDayExercise extends EventEmitter {
  constructor(config) {
    super();
    this.config = config;
    this.scenario = null;
    this.metrics = [];
    this.teamActions = [];
    this.sloViolations = [];
    this.startTime = null;
    this.endTime = null;
  }
  
  async start(scenario) {
    this.scenario = scenario;
    this.startTime = Date.now();
    
    this.emit('exercise-start', {
      scenario: this.config.scenario,
      teams: this.config.teams,
      objectives: this.config.objectives
    });
    
    // シナリオの実行
    for (const phase of scenario.phases) {
      await this.executePhase(phase);
    }
    
    this.endTime = Date.now();
    this.emit('exercise-complete');
  }
  
  async executePhase(phase) {
    console.log(`Starting phase: ${phase.name}`);
    
    // 負荷生成
    const loadGen = new LoadGenerator(phase.load);
    await loadGen.start();
    
    // カオス注入
    if (phase.chaos) {
      for (const chaos of phase.chaos) {
        setTimeout(async () => {
          const experiment = await this.runChaosExperiment(chaos.experiment);
          this.emit('chaos-injected', {
            phase: phase.name,
            experiment: chaos.experiment
          });
        }, this.parseTime(chaos.time));
      }
    }
    
    // フェーズ期間の待機
    await new Promise(resolve => 
      setTimeout(resolve, this.parseDuration(phase.duration))
    );
    
    await loadGen.stop();
  }
  
  recordMetrics(metrics) {
    this.metrics.push({
      timestamp: Date.now(),
      ...metrics
    });
  }
  
  recordSLOViolation(metric, value) {
    this.sloViolations.push({
      timestamp: Date.now(),
      metric,
      value
    });
  }
  
  recordTeamAction(team, action) {
    const actionRecord = {
      timestamp: Date.now(),
      team,
      ...action
    };
    
    this.teamActions.push(actionRecord);
    this.emit('team-action', actionRecord);
  }
  
  async generateReport() {
    return {
      duration: this.endTime - this.startTime,
      objectives: this.evaluateObjectives(),
      teamMetrics: this.calculateTeamMetrics(),
      incidents: this.summarizeIncidents(),
      sloViolations: this.sloViolations,
      lessons_learned: this.extractLessons(),
      improvements: this.suggestImprovements()
    };
  }
  
  evaluateObjectives() {
    const achieved = [];
    const failed = [];
    
    for (const objective of this.config.objectives) {
      if (this.isObjectiveAchieved(objective)) {
        achieved.push(objective);
      } else {
        failed.push(objective);
      }
    }
    
    return { achieved, failed };
  }
  
  isObjectiveAchieved(objective) {
    // 目標達成の判定ロジック
    if (objective.includes('99.9% availability')) {
      const availability = this.calculateAvailability();
      return availability >= 0.999;
    }
    
    if (objective.includes('p99 latency under 200ms')) {
      const p99 = this.calculateP99Latency();
      return p99 < 200;
    }
    
    // 他の目標...
    
    return true;
  }
  
  calculateAvailability() {
    const totalTime = this.endTime - this.startTime;
    const downtime = this.sloViolations
      .filter(v => v.metric === 'availability')
      .reduce((sum, v) => sum + 5000, 0); // 各違反を5秒として計算
    
    return 1 - (downtime / totalTime);
  }
  
  parseTime(time) {
    if (time.startsWith('+')) {
      return this.parseDuration(time.substring(1));
    }
    return 0;
  }
  
  parseDuration(duration) {
    const match = duration.match(/(\d+)([smh])/);
    if (!match) return 0;
    
    const value = parseInt(match[1]);
    const unit = match[2];
    
    switch (unit) {
      case 's': return value * 1000;
      case 'm': return value * 60 * 1000;
      case 'h': return value * 60 * 60 * 1000;
      default: return 0;
    }
  }
}

module.exports = {
  ChaosOrchestrator,
  SteadyStateValidator,
  ChaosExperiment,
  ChaosScenario,
  GameDayExercise
};
```

### Chaos Mesh設定
```yaml
# chaos-mesh/install.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: chaos-testing
---
# Chaos Mesh のインストール
# helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-testing --set dashboard.create=true
```

```yaml
# chaos-experiments/pod-failure.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure-example
  namespace: production
spec:
  action: pod-kill
  mode: fixed-percent
  value: "30"
  duration: "5m"
  selector:
    namespaces:
      - production
    labelSelectors:
      app: web-app
      tier: frontend
  scheduler:
    cron: "@every 2m"
```

```yaml
# chaos-experiments/network-partition.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-partition-example
  namespace: production
spec:
  action: partition
  mode: all
  selector:
    namespaces:
      - production
    labelSelectors:
      app: web-app
  target:
    mode: all
    selector:
      namespaces:
        - production
      labelSelectors:
        app: database
  duration: "3m"
  direction: both
```

```yaml
# chaos-experiments/stress-test.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: cpu-stress-example
  namespace: production
spec:
  mode: all
  selector:
    namespaces:
      - production
    labelSelectors:
      app: api-gateway
  stressors:
    cpu:
      workers: 2
      load: 80
  duration: "10m"
```

### 実行スクリプト
```bash
#!/bin/bash
# run-chaos-experiments.sh

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting Chaos Engineering Experiments${NC}"

# 環境の確認
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Kubernetes接続確認
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    
    # Chaos Mesh確認
    if ! kubectl get ns chaos-testing &> /dev/null; then
        echo -e "${YELLOW}Chaos Mesh not installed. Installing...${NC}"
        install_chaos_mesh
    fi
    
    # Prometheus確認
    if ! kubectl get svc prometheus -n monitoring &> /dev/null; then
        echo -e "${RED}Warning: Prometheus not found in monitoring namespace${NC}"
    fi
}

install_chaos_mesh() {
    helm repo add chaos-mesh https://charts.chaos-mesh.org
    helm repo update
    helm install chaos-mesh chaos-mesh/chaos-mesh \
        -n chaos-testing --create-namespace \
        --set dashboard.create=true \
        --set dashboard.securityMode=false
    
    echo "Waiting for Chaos Mesh to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=chaos-mesh -n chaos-testing --timeout=300s
}

# 定常状態の確認
verify_steady_state() {
    echo -e "\n${GREEN}Verifying steady state...${NC}"
    
    # メトリクスの収集
    local availability=$(kubectl exec -n monitoring prometheus-0 -- \
        promtool query instant 'avg(up{job="kubernetes-pods"})')
    
    local error_rate=$(kubectl exec -n monitoring prometheus-0 -- \
        promtool query instant 'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))')
    
    echo "Current metrics:"
    echo "  Availability: ${availability}"
    echo "  Error rate: ${error_rate}"
    
    # 閾値チェック
    if [[ $(echo "${availability} < 0.99" | bc) -eq 1 ]]; then
        echo -e "${RED}System not in steady state. Availability below threshold.${NC}"
        exit 1
    fi
}

# 実験の実行
run_experiment() {
    local experiment_file=$1
    local experiment_name=$(basename $experiment_file .yaml)
    
    echo -e "\n${YELLOW}Running experiment: ${experiment_name}${NC}"
    
    # 実験の適用
    kubectl apply -f $experiment_file
    
    # 実験の監視
    monitor_experiment $experiment_name
    
    # 実験の削除
    kubectl delete -f $experiment_file
}

monitor_experiment() {
    local experiment_name=$1
    local duration=300  # 5分
    local interval=10
    
    echo "Monitoring experiment for ${duration} seconds..."
    
    for ((i=0; i<$duration; i+=$interval)); do
        # メトリクスの収集
        local timestamp=$(date +%s)
        local pods_running=$(kubectl get pods -n production -l app=web-app --field-selector=status.phase=Running -o json | jq '.items | length')
        local pods_total=$(kubectl get pods -n production -l app=web-app -o json | jq '.items | length')
        
        echo "[${timestamp}] Running pods: ${pods_running}/${pods_total}"
        
        # アラート確認
        check_alerts
        
        sleep $interval
    done
}

check_alerts() {
    local alerts=$(kubectl exec -n monitoring prometheus-0 -- \
        promtool query instant 'ALERTS{alertstate="firing"}' 2>/dev/null | grep -v "no data")
    
    if [ -n "$alerts" ]; then
        echo -e "${RED}Active alerts detected:${NC}"
        echo "$alerts"
    fi
}

# レポート生成
generate_report() {
    local report_file="chaos-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > $report_file << EOF
# Chaos Engineering Report

Date: $(date)

## Experiments Conducted

$(ls chaos-experiments/*.yaml | while read exp; do
    echo "- $(basename $exp .yaml)"
done)

## Results Summary

### System Resilience
- Availability during experiments: ${AVAILABILITY:-N/A}
- Maximum error rate: ${MAX_ERROR_RATE:-N/A}
- Recovery time: ${RECOVERY_TIME:-N/A}

### Discovered Issues
${ISSUES:-No critical issues discovered}

### Recommendations
${RECOMMENDATIONS:-No specific recommendations}

## Detailed Metrics

\`\`\`
${DETAILED_METRICS:-No detailed metrics available}
\`\`\`

EOF
    
    echo -e "\n${GREEN}Report generated: ${report_file}${NC}"
}

# メイン実行
main() {
    check_prerequisites
    verify_steady_state
    
    # 実験の実行
    for experiment in chaos-experiments/*.yaml; do
        if [ -f "$experiment" ]; then
            run_experiment $experiment
            
            # 実験間の回復時間
            echo "Waiting for system recovery..."
            sleep 60
            
            verify_steady_state
        fi
    done
    
    generate_report
}

# 実行
main
```

## 実行と検証

### 1. Chaos Meshのインストール
```bash
# Helmでのインストール
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-testing --create-namespace

# ダッシュボードへのアクセス
kubectl port-forward -n chaos-testing svc/chaos-dashboard 2333:2333
```

### 2. 実験の実行
```bash
# 基本的な実験
./run-chaos-experiments.sh

# 特定の実験のみ
kubectl apply -f chaos-experiments/pod-failure.yaml

# 実験の監視
watch kubectl get podchaos -A
```

### 3. ゲームデイの実施
```bash
# ゲームデイシナリオの実行
npm run gameday -- --scenario black-friday --duration 2h
```

## 成功基準

- [ ] 99.9%の可用性を維持
- [ ] 障害からの自動回復（5分以内）
- [ ] データ損失ゼロ
- [ ] SLO違反の最小化
- [ ] インシデント対応時間の短縮

## 運用ガイド

### 実験の計画
1. 仮説の設定
2. 影響範囲の評価
3. 成功/失敗基準の定義
4. ロールバック計画

### 安全な実行
```bash
# Dry runモード
export CHAOS_DRY_RUN=true

# 限定的な影響範囲
export CHAOS_BLAST_RADIUS=controlled

# 緊急停止
kubectl delete podchaos,networkchaos,stresschaos --all -n production
```

## トラブルシューティング

### 問題: 実験が停止しない
```bash
# 強制削除
kubectl patch podchaos <name> -n production -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl delete podchaos <name> -n production --force
```

### 問題: システムが回復しない
```bash
# Podの再起動
kubectl rollout restart deployment/web-app -n production

# ノードの確認
kubectl get nodes
kubectl describe node <node-name>
```

## 次のステップ

カオスエンジニアリングによる検証を完了後、`20_production_best_practices`で本番環境のベストプラクティスをまとめます。

## 学んだこと

- 障害は避けられない前提での設計
- 定期的な障害訓練の重要性
- 観測可能性の必要性
- チーム間協力の価値

## 参考資料

- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Chaos Mesh Documentation](https://chaos-mesh.org/docs/)
- [Netflix Chaos Engineering](https://netflixtechblog.com/tagged/chaos-engineering)
- [Google SRE Book - Testing for Reliability](https://sre.google/sre-book/testing-reliability/)