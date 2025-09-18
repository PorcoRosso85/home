# 18_edge_computing_iot

## 概要

エッジコンピューティングとIoTデバイスの統合を実装し、低レイテンシ処理、オフライン動作、大規模デバイス管理、リアルタイムデータストリーミングを実現します。

## 目的

- エッジノードでの分散処理
- IoTデバイスの大規模管理
- リアルタイムデータ処理パイプライン
- エッジ-クラウド間の効率的な同期

## アーキテクチャ

```
┌──────────────────────────────────────┐
│          Cloud Backend               │
│  ┌─────────┬────────┬──────────┐    │
│  │   K8s   │ Time   │ Analytics│    │
│  │ Cluster │ Series │ Platform │    │
│  └─────────┴────────┴──────────┘    │
└────────────────┬─────────────────────┘
                 │
         [MQTT/HTTP/gRPC]
                 │
┌────────────────┼─────────────────────┐
│          Edge Layer                  │
│  ┌──────────┐  │  ┌──────────┐      │
│  │  Edge    │  │  │  Edge    │      │
│  │ Gateway  │  │  │ Gateway  │      │
│  │ (K3s)    │  │  │ (K3s)    │      │
│  └─────┬────┘  │  └────┬─────┘      │
│        │       │       │             │
│   [LoRaWAN]    │  [BLE/WiFi]        │
│        │       │       │             │
│  ┌─────▼────┐  │  ┌───▼────┐        │
│  │IoT Device│  │  │ Sensor │        │
│  │ Fleet    │  │  │ Array  │        │
│  └──────────┘  │  └────────┘        │
└─────────────────────────────────────┘
```

## 検証項目

### 1. エッジインフラストラクチャ
- **K3s deployment**: 軽量Kubernetes
- **Edge runtime**: WebAssembly/容器
- **Local storage**: 時系列データベース
- **Offline operation**: 自律動作

### 2. IoTデバイス管理
- **Device provisioning**: ゼロタッチ設定
- **OTA updates**: 段階的更新
- **Security**: デバイス認証/暗号化
- **Monitoring**: ヘルスチェック

### 3. データ処理パイプライン
- **Stream processing**: Apache Pulsar/Kafka
- **Edge analytics**: TinyML/推論
- **Data filtering**: エッジでの前処理
- **Aggregation**: 効率的な集約

### 4. エッジ-クラウド連携
- **Synchronization**: 差分同期
- **Caching**: インテリジェントキャッシュ
- **Failover**: 自動フェイルオーバー
- **Load distribution**: 動的負荷分散

## TDDアプローチ

### Red Phase (エッジ/IoTシステムのテスト)
```javascript
// test/edge-iot-system.test.js
const { EdgeManager, IoTDeviceSimulator } = require('../src/edge-iot');
const mqtt = require('mqtt');
const k3s = require('@rancher/k3s');

describe('Edge Computing and IoT Integration', () => {
  let edgeManager;
  let deviceFleet;
  let cloudBackend;
  
  beforeAll(async () => {
    // エッジインフラの初期化
    edgeManager = new EdgeManager({
      edgeNodes: [
        { id: 'edge-1', location: 'factory-floor', type: 'industrial' },
        { id: 'edge-2', location: 'warehouse', type: 'logistics' },
        { id: 'edge-3', location: 'retail-store', type: 'retail' }
      ],
      orchestration: 'k3s',
      connectivity: {
        uplink: 'lte',
        backup: 'satellite'
      }
    });
    
    // IoTデバイスフリートの初期化
    deviceFleet = new IoTDeviceFleet({
      devices: [
        { type: 'temperature', count: 100, protocol: 'mqtt' },
        { type: 'motion', count: 50, protocol: 'coap' },
        { type: 'camera', count: 20, protocol: 'rtsp' },
        { type: 'vibration', count: 30, protocol: 'opcua' }
      ]
    });
    
    // クラウドバックエンドの接続
    cloudBackend = new CloudBackend({
      endpoint: process.env.CLOUD_ENDPOINT,
      auth: process.env.CLOUD_AUTH
    });
  });

  it('should deploy K3s on edge nodes', async () => {
    // K3s クラスターのデプロイ
    const deployments = await Promise.all(
      edgeManager.nodes.map(node => 
        edgeManager.deployK3s(node, {
          version: 'v1.28.5+k3s1',
          config: {
            'disable': ['traefik'],
            'cluster-init': node.id === 'edge-1',
            'server': node.id !== 'edge-1' ? 'https://edge-1:6443' : undefined,
            'node-label': [
              `edge.io/location=${node.location}`,
              `edge.io/type=${node.type}`
            ]
          }
        })
      )
    );
    
    // デプロイメント成功確認
    deployments.forEach(deployment => {
      expect(deployment.status).toBe('ready');
      expect(deployment.k3sVersion).toMatch(/v1.28.5/);
    });
    
    // エッジクラスターの形成確認
    const clusterInfo = await edgeManager.getClusterInfo();
    expect(clusterInfo.nodes.length).toBe(3);
    expect(clusterInfo.status).toBe('healthy');
    
    // エッジワークロードのデプロイ
    const edgeWorkloads = [
      {
        name: 'mqtt-broker',
        image: 'eclipse-mosquitto:2.0',
        nodeSelector: { 'edge.io/type': 'industrial' }
      },
      {
        name: 'edge-analytics',
        image: 'edge-analytics:latest',
        resources: { limits: { cpu: '500m', memory: '512Mi' } }
      },
      {
        name: 'local-storage',
        image: 'timescaledb:latest-pg15',
        volumeSize: '10Gi'
      }
    ];
    
    for (const workload of edgeWorkloads) {
      const deployed = await edgeManager.deployWorkload(workload);
      expect(deployed.status).toBe('running');
    }
  });

  it('should handle massive IoT device connections', async () => {
    // デバイス接続のシミュレーション
    const connectionPromises = [];
    const startTime = Date.now();
    
    // 1000デバイスの同時接続
    for (let i = 0; i < 1000; i++) {
      const device = deviceFleet.createDevice({
        id: `device-${i}`,
        type: 'temperature',
        location: `zone-${i % 10}`
      });
      
      connectionPromises.push(
        device.connect({
          broker: 'mqtt://edge-1:1883',
          clientId: device.id,
          clean: true,
          reconnectPeriod: 5000
        })
      );
    }
    
    const connectionResults = await Promise.allSettled(connectionPromises);
    const successCount = connectionResults.filter(r => r.status === 'fulfilled').length;
    
    expect(successCount).toBeGreaterThan(950); // 95%以上成功
    
    const connectionTime = Date.now() - startTime;
    expect(connectionTime).toBeLessThan(30000); // 30秒以内
    
    // 接続統計
    const stats = await edgeManager.getConnectionStats();
    console.log('Connection stats:', {
      total: stats.totalConnections,
      active: stats.activeConnections,
      throughput: stats.messagesPerSecond
    });
    
    // スケーラビリティテスト
    const loadTest = await deviceFleet.runLoadTest({
      duration: 60000, // 1分
      messagesPerSecond: 10000,
      payloadSize: 1024 // 1KB
    });
    
    expect(loadTest.successRate).toBeGreaterThan(0.99);
    expect(loadTest.avgLatency).toBeLessThan(100); // 100ms以下
  });

  it('should process data at the edge', async () => {
    // エッジアナリティクスパイプライン
    const pipeline = await edgeManager.createPipeline({
      name: 'anomaly-detection',
      stages: [
        {
          name: 'ingestion',
          type: 'mqtt-consumer',
          config: {
            topics: ['sensors/+/temperature', 'sensors/+/vibration'],
            qos: 1
          }
        },
        {
          name: 'preprocessing',
          type: 'transform',
          config: {
            operations: [
              { type: 'normalize', range: [0, 100] },
              { type: 'window', size: '1m', slide: '10s' }
            ]
          }
        },
        {
          name: 'inference',
          type: 'ml-model',
          config: {
            model: 'anomaly-detector-v2',
            runtime: 'tensorflow-lite',
            threshold: 0.95
          }
        },
        {
          name: 'alerting',
          type: 'conditional',
          config: {
            condition: 'anomaly_score > 0.95',
            action: {
              type: 'webhook',
              url: 'http://cloud-backend/alerts'
            }
          }
        }
      ]
    });
    
    // パイプラインのデプロイと起動
    await pipeline.deploy();
    await pipeline.start();
    
    // テストデータの送信
    const testData = generateAnomalousData(1000);
    await deviceFleet.sendBatch(testData);
    
    // 処理結果の確認
    await new Promise(resolve => setTimeout(resolve, 5000)); // 処理待ち
    
    const results = await pipeline.getMetrics();
    expect(results.processed).toBe(1000);
    expect(results.anomaliesDetected).toBeGreaterThan(50);
    expect(results.avgProcessingTime).toBeLessThan(50); // 50ms以下
    
    // エッジでの推論パフォーマンス
    const inferenceStats = await pipeline.getStageMetrics('inference');
    expect(inferenceStats.throughput).toBeGreaterThan(100); // 100 msgs/sec
    expect(inferenceStats.cpuUsage).toBeLessThan(50); // CPU 50%以下
  });

  it('should handle offline operation and sync', async () => {
    // オフラインモードのシミュレーション
    await edgeManager.simulateNetworkOutage('edge-1');
    
    // オフライン中のデータ収集
    const offlineData = [];
    const offlineStartTime = Date.now();
    
    // 5分間のオフライン動作
    const dataCollection = setInterval(() => {
      const batch = deviceFleet.generateData(100);
      offlineData.push(...batch);
    }, 1000);
    
    await new Promise(resolve => setTimeout(resolve, 300000)); // 5分
    clearInterval(dataCollection);
    
    // ローカルストレージ確認
    const localStorage = await edgeManager.getLocalStorage('edge-1');
    expect(localStorage.dataPoints).toBeGreaterThan(30000); // 30k データポイント
    expect(localStorage.usedSpace).toBeLessThan(1024 * 1024 * 1024); // 1GB以下
    
    // ネットワーク復旧
    await edgeManager.restoreNetwork('edge-1');
    
    // データ同期の開始
    const syncJob = await edgeManager.startSync('edge-1', {
      strategy: 'incremental',
      compression: true,
      priority: 'time-critical'
    });
    
    // 同期の監視
    let syncProgress = 0;
    while (syncProgress < 100) {
      await new Promise(resolve => setTimeout(resolve, 5000));
      const status = await syncJob.getStatus();
      syncProgress = status.progress;
      
      console.log(`Sync progress: ${syncProgress}%`);
      expect(status.errors).toBe(0);
    }
    
    // 同期完了確認
    const cloudData = await cloudBackend.query({
      timeRange: {
        start: offlineStartTime,
        end: Date.now()
      }
    });
    
    expect(cloudData.count).toBe(offlineData.length);
    expect(syncJob.duration).toBeLessThan(60000); // 1分以内に同期
  });

  it('should perform OTA updates on devices', async () => {
    // ファームウェアアップデート準備
    const updateCampaign = await deviceFleet.createUpdateCampaign({
      name: 'security-patch-2024-01',
      targetDevices: {
        type: 'temperature',
        version: '<2.0.0'
      },
      firmware: {
        version: '2.0.1',
        url: 'https://updates.example.com/firmware/temp-sensor-v2.0.1.bin',
        checksum: 'sha256:abcdef123456...',
        size: 512 * 1024 // 512KB
      },
      rollout: {
        strategy: 'canary',
        phases: [
          { percentage: 10, duration: '1h' },
          { percentage: 50, duration: '2h' },
          { percentage: 100, duration: '4h' }
        ]
      }
    });
    
    // アップデートキャンペーンの開始
    await updateCampaign.start();
    
    // 進捗の監視
    const monitorUpdate = async () => {
      const status = await updateCampaign.getStatus();
      
      console.log('Update campaign status:', {
        phase: status.currentPhase,
        progress: status.progress,
        successful: status.successful,
        failed: status.failed,
        pending: status.pending
      });
      
      // 失敗率の確認
      const failureRate = status.failed / (status.successful + status.failed);
      expect(failureRate).toBeLessThan(0.05); // 5%以下
      
      // カナリーフェーズでの問題検出
      if (status.currentPhase === 0 && failureRate > 0.1) {
        await updateCampaign.rollback();
        throw new Error('High failure rate in canary phase');
      }
    };
    
    // 定期的な監視
    const monitorInterval = setInterval(monitorUpdate, 30000); // 30秒ごと
    
    // キャンペーン完了待ち
    await updateCampaign.waitForCompletion();
    clearInterval(monitorInterval);
    
    // 最終結果
    const finalStatus = await updateCampaign.getFinalReport();
    expect(finalStatus.successRate).toBeGreaterThan(0.95);
    expect(finalStatus.totalDuration).toBeLessThan(8 * 3600 * 1000); // 8時間以内
  });

  it('should implement edge AI inference', async () => {
    // TinyMLモデルのデプロイ
    const models = [
      {
        name: 'vibration-anomaly',
        type: 'tensorflow-lite',
        size: '50KB',
        inputShape: [1, 100, 1],
        outputShape: [1, 2]
      },
      {
        name: 'visual-inspection',
        type: 'onnx',
        size: '5MB',
        inputShape: [1, 3, 224, 224],
        outputShape: [1, 10]
      }
    ];
    
    // モデルのエッジへのデプロイ
    for (const model of models) {
      const deployment = await edgeManager.deployModel(model, {
        targetNodes: ['edge-1', 'edge-2'],
        runtime: model.type === 'tensorflow-lite' ? 'tflite' : 'onnxruntime',
        acceleration: 'cpu' // or 'gpu', 'npu'
      });
      
      expect(deployment.status).toBe('deployed');
    }
    
    // リアルタイム推論のテスト
    const inferenceTest = async (modelName, testData) => {
      const startTime = Date.now();
      const results = [];
      
      for (const data of testData) {
        const prediction = await edgeManager.predict(modelName, data);
        results.push({
          input: data,
          output: prediction,
          latency: prediction.inferenceTime
        });
      }
      
      const totalTime = Date.now() - startTime;
      const avgLatency = results.reduce((sum, r) => sum + r.latency, 0) / results.length;
      
      return {
        results,
        totalTime,
        avgLatency,
        throughput: testData.length / (totalTime / 1000)
      };
    };
    
    // 振動異常検出モデルのテスト
    const vibrationData = generateVibrationTestData(1000);
    const vibrationResults = await inferenceTest('vibration-anomaly', vibrationData);
    
    expect(vibrationResults.avgLatency).toBeLessThan(10); // 10ms以下
    expect(vibrationResults.throughput).toBeGreaterThan(100); // 100 predictions/sec
    
    // ビジュアル検査モデルのテスト
    const imageData = generateImageTestData(100);
    const visualResults = await inferenceTest('visual-inspection', imageData);
    
    expect(visualResults.avgLatency).toBeLessThan(100); // 100ms以下
    expect(visualResults.throughput).toBeGreaterThan(10); // 10 predictions/sec
  });

  it('should handle complex event processing', async () => {
    // 複合イベント処理エンジン
    const cepEngine = await edgeManager.createCEPEngine({
      rules: [
        {
          name: 'temperature-spike',
          pattern: 'EVERY (temp WHERE value > 80) -> (temp WHERE value > 90) WITHIN 5 minutes',
          action: 'alert("Temperature spike detected")'
        },
        {
          name: 'coordinated-motion',
          pattern: 'motion[5] WHERE zone = "entrance" WITHIN 10 seconds',
          action: 'triggerSecurityProtocol()'
        },
        {
          name: 'machine-failure-prediction',
          pattern: `
            (vibration WHERE anomaly_score > 0.8) AND 
            (temperature WHERE value > baseline * 1.2) 
            FOLLOWED BY 
            (sound WHERE db_level > 85)
            WITHIN 30 minutes
          `,
          action: 'scheduleMaintenance(machine_id, "urgent")'
        }
      ]
    });
    
    // イベントストリームのシミュレーション
    const eventStream = new EventStreamSimulator({
      scenarios: [
        'normal-operation',
        'temperature-anomaly',
        'security-breach',
        'machine-degradation'
      ]
    });
    
    // イベント処理の開始
    await cepEngine.start();
    await eventStream.start();
    
    // 5分間の実行
    await new Promise(resolve => setTimeout(resolve, 300000));
    
    // 検出されたパターンの確認
    const detectedPatterns = await cepEngine.getDetectedPatterns();
    
    expect(detectedPatterns).toContainEqual(
      expect.objectContaining({ rule: 'temperature-spike' })
    );
    
    // パフォーマンスメトリクス
    const performance = await cepEngine.getPerformanceMetrics();
    expect(performance.eventsProcessed).toBeGreaterThan(100000);
    expect(performance.avgLatency).toBeLessThan(5); // 5ms以下
    expect(performance.patternMatchRate).toBeGreaterThan(0.1);
  });
});

// エッジセキュリティのテスト
describe('Edge Security', () => {
  it('should secure device communications', async () => {
    // デバイス証明書の生成と配布
    const pki = new EdgePKI({
      rootCA: await generateRootCA(),
      intermediateCA: await generateIntermediateCA()
    });
    
    // デバイスごとの証明書発行
    const deviceCerts = await Promise.all(
      deviceFleet.devices.map(device => 
        pki.issueDeviceCertificate({
          deviceId: device.id,
          deviceType: device.type,
          validityDays: 365
        })
      )
    );
    
    // mTLS接続のテスト
    const secureDevice = deviceFleet.devices[0];
    const secureConnection = await secureDevice.connectSecure({
      cert: deviceCerts[0].cert,
      key: deviceCerts[0].key,
      ca: pki.getCACert(),
      rejectUnauthorized: true
    });
    
    expect(secureConnection.authorized).toBe(true);
    expect(secureConnection.protocol).toBe('TLSv1.3');
    
    // 不正な証明書での接続試行
    const invalidCert = await generateSelfSignedCert();
    
    await expect(
      secureDevice.connectSecure({
        cert: invalidCert.cert,
        key: invalidCert.key,
        ca: pki.getCACert()
      })
    ).rejects.toThrow('Certificate verification failed');
    
    // 証明書の失効テスト
    await pki.revokeCertificate(deviceCerts[0].serial, 'compromised');
    
    await expect(
      secureDevice.connectSecure({
        cert: deviceCerts[0].cert,
        key: deviceCerts[0].key,
        ca: pki.getCACert()
      })
    ).rejects.toThrow('Certificate revoked');
  });
});
```

### Green Phase (エッジ/IoT実装)
```javascript
// edge-manager.js
const k3s = require('@rancher/k3s');
const mqtt = require('mqtt');
const { KubeConfig } = require('@kubernetes/client-node');

class EdgeManager {
  constructor(config) {
    this.config = config;
    this.nodes = config.edgeNodes.map(node => new EdgeNode(node));
    this.orchestrator = new K3sOrchestrator();
  }
  
  async deployK3s(node, options) {
    console.log(`Deploying K3s on ${node.id}...`);
    
    const deployment = await this.orchestrator.deploy({
      node,
      version: options.version,
      config: options.config,
      networking: {
        flannel: {
          backend: 'vxlan',
          iface: node.networkInterface || 'eth0'
        }
      }
    });
    
    // エージェントの設定
    if (options.config['cluster-init']) {
      await this.orchestrator.initializeCluster(deployment);
    } else {
      await this.orchestrator.joinCluster(deployment, options.config.server);
    }
    
    // ヘルスチェック
    await this.waitForNodeReady(deployment);
    
    return deployment;
  }
  
  async deployWorkload(workload) {
    const manifest = this.generateWorkloadManifest(workload);
    
    // 適切なノードを選択
    const targetNode = this.selectNode(workload.nodeSelector);
    
    // デプロイ
    const result = await this.orchestrator.apply(targetNode, manifest);
    
    // 起動確認
    await this.waitForWorkloadReady(result);
    
    return result;
  }
  
  async createPipeline(config) {
    return new EdgeAnalyticsPipeline(config, this);
  }
  
  async deployModel(model, options) {
    const modelServer = new EdgeModelServer({
      runtime: options.runtime,
      acceleration: options.acceleration
    });
    
    // モデルの最適化
    const optimizedModel = await this.optimizeModelForEdge(model);
    
    // 各ノードへのデプロイ
    const deployments = await Promise.all(
      options.targetNodes.map(nodeId => {
        const node = this.nodes.find(n => n.id === nodeId);
        return modelServer.deploy(node, optimizedModel);
      })
    );
    
    return {
      status: 'deployed',
      deployments,
      endpoints: deployments.map(d => d.endpoint)
    };
  }
  
  async optimizeModelForEdge(model) {
    // モデルの量子化
    if (model.type === 'tensorflow-lite') {
      return this.quantizeTFLiteModel(model);
    } else if (model.type === 'onnx') {
      return this.optimizeONNXModel(model);
    }
    
    return model;
  }
  
  async predict(modelName, input) {
    const model = this.models.get(modelName);
    const node = this.selectOptimalNode(model);
    
    const startTime = Date.now();
    const prediction = await node.infer(modelName, input);
    const inferenceTime = Date.now() - startTime;
    
    return {
      ...prediction,
      inferenceTime,
      nodeId: node.id
    };
  }
  
  selectOptimalNode(model) {
    // レイテンシとリソース使用率に基づいて最適なノードを選択
    const candidates = this.nodes.filter(node => 
      node.hasModel(model.name)
    );
    
    return candidates.reduce((best, node) => {
      const score = this.calculateNodeScore(node, model);
      return score > best.score ? { node, score } : best;
    }, { node: null, score: -1 }).node;
  }
  
  async createCEPEngine(config) {
    const engine = new ComplexEventProcessor(config.rules);
    
    // エッジノードにエンジンをデプロイ
    await this.deployWorkload({
      name: 'cep-engine',
      image: 'edge-cep:latest',
      config: engine.serialize()
    });
    
    return engine;
  }
}

// エッジノード実装
class EdgeNode {
  constructor(config) {
    this.id = config.id;
    this.location = config.location;
    this.type = config.type;
    this.resources = {
      cpu: config.cpu || 4,
      memory: config.memory || 8192,
      storage: config.storage || 100
    };
    this.models = new Map();
    this.metrics = new MetricsCollector();
  }
  
  async infer(modelName, input) {
    const model = this.models.get(modelName);
    if (!model) {
      throw new Error(`Model ${modelName} not found on node ${this.id}`);
    }
    
    // リソース使用率チェック
    if (this.metrics.cpuUsage > 80) {
      throw new Error('Node overloaded');
    }
    
    // 推論実行
    return model.predict(input);
  }
  
  hasModel(modelName) {
    return this.models.has(modelName);
  }
}

// IoTデバイスフリート管理
class IoTDeviceFleet {
  constructor(config) {
    this.devices = [];
    this.protocols = new Map();
    
    // デバイスの初期化
    for (const deviceType of config.devices) {
      for (let i = 0; i < deviceType.count; i++) {
        this.devices.push(
          this.createDevice({
            id: `${deviceType.type}-${i}`,
            type: deviceType.type,
            protocol: deviceType.protocol
          })
        );
      }
    }
  }
  
  createDevice(config) {
    switch (config.protocol) {
      case 'mqtt':
        return new MQTTDevice(config);
      case 'coap':
        return new CoAPDevice(config);
      case 'opcua':
        return new OPCUADevice(config);
      default:
        throw new Error(`Unknown protocol: ${config.protocol}`);
    }
  }
  
  async createUpdateCampaign(config) {
    return new OTAUpdateCampaign(config, this);
  }
  
  async runLoadTest(config) {
    const loadGenerator = new IoTLoadGenerator(this.devices);
    
    return loadGenerator.run({
      duration: config.duration,
      messagesPerSecond: config.messagesPerSecond,
      payloadSize: config.payloadSize,
      pattern: 'constant' // or 'burst', 'ramp'
    });
  }
}

// MQTTデバイス実装
class MQTTDevice {
  constructor(config) {
    this.id = config.id;
    this.type = config.type;
    this.location = config.location;
    this.client = null;
    this.connected = false;
  }
  
  async connect(options) {
    this.client = mqtt.connect(options.broker, {
      clientId: options.clientId,
      clean: options.clean,
      reconnectPeriod: options.reconnectPeriod,
      username: this.id,
      password: this.generateToken()
    });
    
    return new Promise((resolve, reject) => {
      this.client.on('connect', () => {
        this.connected = true;
        resolve(this);
      });
      
      this.client.on('error', reject);
    });
  }
  
  async connectSecure(options) {
    this.client = mqtt.connect({
      ...options,
      protocol: 'mqtts',
      cert: options.cert,
      key: options.key,
      ca: options.ca,
      rejectUnauthorized: options.rejectUnauthorized
    });
    
    return new Promise((resolve, reject) => {
      this.client.on('connect', () => {
        this.connected = true;
        resolve({
          authorized: true,
          protocol: 'TLSv1.3'
        });
      });
      
      this.client.on('error', (err) => {
        if (err.message.includes('certificate')) {
          reject(new Error('Certificate verification failed'));
        } else {
          reject(err);
        }
      });
    });
  }
  
  async publish(topic, data) {
    if (!this.connected) {
      throw new Error('Device not connected');
    }
    
    return new Promise((resolve, reject) => {
      this.client.publish(topic, JSON.stringify(data), { qos: 1 }, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }
  
  generateToken() {
    // JWT token generation for device authentication
    return jwt.sign(
      { deviceId: this.id, type: this.type },
      Deno.env.get('DEVICE_SECRET'),
      { expiresIn: '24h' }
    );
  }
}

// エッジ分析パイプライン
class EdgeAnalyticsPipeline {
  constructor(config, edgeManager) {
    this.name = config.name;
    this.stages = config.stages.map(s => this.createStage(s));
    this.edgeManager = edgeManager;
    this.metrics = new PipelineMetrics();
  }
  
  createStage(stageConfig) {
    switch (stageConfig.type) {
      case 'mqtt-consumer':
        return new MQTTConsumerStage(stageConfig);
      case 'transform':
        return new TransformStage(stageConfig);
      case 'ml-model':
        return new MLInferenceStage(stageConfig);
      case 'conditional':
        return new ConditionalStage(stageConfig);
      default:
        throw new Error(`Unknown stage type: ${stageConfig.type}`);
    }
  }
  
  async deploy() {
    // Kubernetes オペレーターとしてデプロイ
    const pipelineOperator = {
      apiVersion: 'edge.io/v1',
      kind: 'AnalyticsPipeline',
      metadata: {
        name: this.name
      },
      spec: {
        stages: this.stages.map(s => s.toSpec()),
        resources: {
          requests: { cpu: '100m', memory: '128Mi' },
          limits: { cpu: '1000m', memory: '1Gi' }
        }
      }
    };
    
    await this.edgeManager.orchestrator.apply('edge-1', pipelineOperator);
  }
  
  async start() {
    for (const stage of this.stages) {
      await stage.start();
    }
    
    // ステージ間の接続
    for (let i = 0; i < this.stages.length - 1; i++) {
      this.stages[i].pipe(this.stages[i + 1]);
    }
  }
  
  async getMetrics() {
    return {
      processed: this.metrics.totalProcessed,
      anomaliesDetected: this.metrics.anomaliesDetected,
      avgProcessingTime: this.metrics.avgProcessingTime
    };
  }
}

// OTAアップデートキャンペーン
class OTAUpdateCampaign {
  constructor(config, fleet) {
    this.config = config;
    this.fleet = fleet;
    this.phases = config.rollout.phases;
    this.currentPhase = -1;
    this.status = {
      successful: 0,
      failed: 0,
      pending: 0
    };
  }
  
  async start() {
    // 対象デバイスの特定
    this.targetDevices = this.fleet.devices.filter(device => 
      device.type === this.config.targetDevices.type &&
      this.compareVersions(device.version, this.config.targetDevices.version) < 0
    );
    
    this.status.pending = this.targetDevices.length;
    
    // フェーズごとの実行
    for (let i = 0; i < this.phases.length; i++) {
      this.currentPhase = i;
      await this.executePhase(this.phases[i]);
      
      // フェーズ間の待機
      if (i < this.phases.length - 1) {
        await this.waitForStabilization(this.phases[i].duration);
      }
    }
  }
  
  async executePhase(phase) {
    const devicesInPhase = Math.floor(
      this.targetDevices.length * (phase.percentage / 100)
    );
    
    const batch = this.targetDevices.slice(0, devicesInPhase);
    
    // 並列アップデート
    const updatePromises = batch.map(device => 
      this.updateDevice(device).catch(err => {
        this.status.failed++;
        return { device: device.id, error: err.message };
      })
    );
    
    const results = await Promise.allSettled(updatePromises);
    
    // 成功数の更新
    const successCount = results.filter(r => r.status === 'fulfilled').length;
    this.status.successful += successCount;
    this.status.pending -= batch.length;
  }
  
  async updateDevice(device) {
    // ダウンロード
    await device.downloadFirmware(this.config.firmware.url);
    
    // 検証
    await device.verifyFirmware(this.config.firmware.checksum);
    
    // インストール
    await device.installFirmware();
    
    // 再起動
    await device.reboot();
    
    // 動作確認
    await device.waitForReady();
    await device.verifyVersion(this.config.firmware.version);
    
    return { device: device.id, success: true };
  }
  
  async getStatus() {
    return {
      currentPhase: this.currentPhase,
      progress: (this.status.successful / this.targetDevices.length) * 100,
      ...this.status
    };
  }
  
  compareVersions(current, required) {
    // セマンティックバージョニング比較
    const currentParts = current.split('.').map(Number);
    const requiredParts = required.replace(/[<>=]/g, '').split('.').map(Number);
    
    for (let i = 0; i < 3; i++) {
      if (currentParts[i] < requiredParts[i]) return -1;
      if (currentParts[i] > requiredParts[i]) return 1;
    }
    
    return 0;
  }
}

// 複合イベント処理エンジン
class ComplexEventProcessor {
  constructor(rules) {
    this.rules = rules.map(r => new CEPRule(r));
    this.eventBuffer = new CircularBuffer(10000);
    this.patternMatcher = new PatternMatcher();
    this.detectedPatterns = [];
  }
  
  async processEvent(event) {
    this.eventBuffer.add(event);
    
    // 各ルールに対してパターンマッチング
    for (const rule of this.rules) {
      const matches = this.patternMatcher.match(
        rule.pattern,
        this.eventBuffer,
        rule.window
      );
      
      if (matches.length > 0) {
        this.detectedPatterns.push({
          rule: rule.name,
          matches,
          timestamp: Date.now()
        });
        
        // アクション実行
        await this.executeAction(rule.action, matches);
      }
    }
  }
  
  async executeAction(action, matches) {
    // アクションの評価と実行
    const context = { matches, alert: console.log };
    const actionFn = new Function('context', `with(context) { ${action} }`);
    actionFn(context);
  }
}

module.exports = {
  EdgeManager,
  IoTDeviceFleet,
  EdgeNode,
  MQTTDevice,
  EdgeAnalyticsPipeline,
  OTAUpdateCampaign,
  ComplexEventProcessor
};
```

### Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  # エッジゲートウェイ1（工場）
  edge-gateway-1:
    image: rancher/k3s:v1.28.5-k3s1
    privileged: true
    environment:
      K3S_TOKEN: ${K3S_TOKEN}
      K3S_CLUSTER_INIT: "true"
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
      - edge1-data:/var/lib/rancher/k3s
    ports:
      - "6443:6443"
      - "1883:1883"  # MQTT
      - "8086:8086"  # InfluxDB
    networks:
      - edge-network

  # エッジゲートウェイ2（倉庫）
  edge-gateway-2:
    image: rancher/k3s:v1.28.5-k3s1
    privileged: true
    environment:
      K3S_TOKEN: ${K3S_TOKEN}
      K3S_URL: https://edge-gateway-1:6443
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
      - edge2-data:/var/lib/rancher/k3s
    depends_on:
      - edge-gateway-1
    networks:
      - edge-network

  # MQTTブローカー
  mqtt-broker:
    image: eclipse-mosquitto:2.0
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log
      - ./certs:/mosquitto/certs
    ports:
      - "1884:1883"
      - "8883:8883"  # MQTT over TLS
    networks:
      - edge-network

  # 時系列データベース
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_PASSWORD: edgedb
      POSTGRES_DB: iot_data
    volumes:
      - timescale-data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    networks:
      - edge-network

  # エッジML推論サーバー
  edge-ml-server:
    build:
      context: .
      dockerfile: Dockerfile.ml
    environment:
      MODEL_PATH: /models
      INFERENCE_ENGINE: tensorflow-lite
    volumes:
      - ./models:/models
    ports:
      - "8501:8501"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
    networks:
      - edge-network

  # IoTデバイスシミュレーター
  device-simulator:
    build:
      context: .
      dockerfile: Dockerfile.simulator
    environment:
      DEVICE_COUNT: 1000
      MQTT_BROKER: mqtt://mqtt-broker:1883
      DATA_RATE: 10  # messages per second per device
    depends_on:
      - mqtt-broker
    networks:
      - edge-network

networks:
  edge-network:
    driver: bridge

volumes:
  edge1-data:
  edge2-data:
  timescale-data:
```

### K3sマニフェスト
```yaml
# k3s-manifests/edge-workloads.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: edge-computing
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: edge-data-collector
  namespace: edge-computing
spec:
  selector:
    matchLabels:
      app: data-collector
  template:
    metadata:
      labels:
        app: data-collector
    spec:
      hostNetwork: true
      containers:
      - name: collector
        image: edge-data-collector:latest
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: MQTT_BROKER
          value: "mqtt://mqtt-broker:1883"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        volumeMounts:
        - name: device-data
          mountPath: /var/lib/edge/data
      volumes:
      - name: device-data
        hostPath:
          path: /var/lib/edge/data
          type: DirectoryOrCreate
---
apiVersion: v1
kind: Service
metadata:
  name: edge-inference
  namespace: edge-computing
spec:
  type: ClusterIP
  selector:
    app: ml-inference
  ports:
  - port: 8501
    targetPort: 8501
    name: http
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-inference
  namespace: edge-computing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ml-inference
  template:
    metadata:
      labels:
        app: ml-inference
    spec:
      containers:
      - name: inference-server
        image: edge-ml-server:latest
        ports:
        - containerPort: 8501
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2
            memory: 2Gi
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        configMap:
          name: ml-models
```

## 実行と検証

### 1. エッジインフラの起動
```bash
# K3sクラスターの起動
docker-compose up -d edge-gateway-1 edge-gateway-2

# クラスター状態確認
kubectl get nodes
```

### 2. IoTデバイスのシミュレーション
```bash
# デバイスシミュレーターの起動
docker-compose up -d device-simulator

# MQTT トピックの監視
mosquitto_sub -h localhost -p 1884 -t 'sensors/+/+' -v
```

### 3. エッジ分析の実行
```bash
# 分析パイプラインのデプロイ
kubectl apply -f k3s-manifests/edge-workloads.yaml

# ログ確認
kubectl logs -f deployment/ml-inference -n edge-computing
```

## 成功基準

- [ ] 1000+ IoTデバイスの同時接続
- [ ] エッジでの推論レイテンシ <50ms
- [ ] オフライン動作5分以上
- [ ] OTAアップデート成功率 >95%
- [ ] データ同期時間 <1分

## 運用ガイド

### デバイス管理
```bash
# デバイス一覧
./scripts/list-devices.sh

# ファームウェアアップデート
./scripts/ota-update.sh --campaign security-patch-2024-01

# デバイス監視
./scripts/monitor-devices.sh --type temperature
```

### エッジノード管理
```bash
# ノード状態確認
kubectl get nodes -o wide

# リソース使用状況
kubectl top nodes
```

## トラブルシューティング

### 問題: デバイス接続失敗
```bash
# MQTT ブローカーログ確認
docker logs mqtt-broker

# 証明書の検証
openssl verify -CAfile ca.crt device.crt
```

### 問題: 推論性能低下
```bash
# CPU使用率確認
kubectl top pods -n edge-computing

# モデル最適化
./scripts/optimize-model.sh --model vibration-anomaly
```

## 次のステップ

エッジコンピューティングとIoT統合を確立後、`19_chaos_engineering_testing`でカオスエンジニアリングによる堅牢性テストを実装します。

## 学んだこと

- エッジでの分散処理の利点
- IoTデバイス管理の複雑性
- リアルタイム処理の課題
- オフライン動作の重要性

## 参考資料

- [K3s Documentation](https://docs.k3s.io/)
- [Edge Computing Patterns](https://www.lfedge.org/projects/)
- [IoT Security Best Practices](https://www.iotsecurityfoundation.org/)
- [TinyML Book](https://www.oreilly.com/library/view/tinyml/9781492052036/)