# 14_multi_server_service_discovery

## 概要

複数サーバー環境でのサービスディスカバリーを実装し、動的なサービス登録、健全性監視、自動フェイルオーバーを実現します。Consul/etcdパターンを検証します。

## 目的

- 動的なサービス登録と発見
- ヘルスチェックによる自動除外
- DNS/HTTP APIによるサービス解決
- 設定の集中管理とウォッチ機能

## アーキテクチャ

```
┌─────────────────────────────────┐
│    Service Discovery Cluster    │
│  ┌────────┬────────┬────────┐  │
│  │Consul-1│Consul-2│Consul-3│  │
│  │ Leader │Follower│Follower│  │
│  └────┬───┴───┬────┴───┬────┘  │
│       │       │        │       │
│    Raft Consensus Protocol     │
└───────┴───────┬────────┴───────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐   ┌──▼───┐   ┌──▼───┐
│Service│   │Service│   │Service│
│   A   │   │   B   │   │   C   │
│       │   │       │   │       │
│Agent  │   │Agent  │   │Agent  │
│Health │   │Health │   │Health │
└───────┘   └───────┘   └───────┘
    │           │           │
    └───────────┼───────────┘
                │
         [Clients Query]
           - DNS: api.service.consul
           - HTTP: /v1/catalog/service/api
```

## 検証項目

### 1. サービス登録と発見
- **自動登録**: サービス起動時の登録
- **メタデータ**: タグ、バージョン、環境
- **TTL更新**: 定期的な生存確認
- **グレースフル登録解除**: 終了時の削除

### 2. ヘルスチェック
- **HTTPチェック**: エンドポイント監視
- **TCPチェック**: ポート接続確認
- **スクリプトチェック**: カスタムロジック
- **複合チェック**: 複数条件の組み合わせ

### 3. サービスメッシュ機能
- **ロードバランシング**: クライアント側LB
- **サーキットブレーカー**: 障害の隔離
- **リトライ**: 自動再試行
- **認証/認可**: mTLSサポート

### 4. 設定管理
- **Key-Valueストア**: 動的設定
- **ウォッチ機能**: 変更通知
- **テンプレート**: 設定ファイル生成
- **バージョニング**: 履歴管理

## TDDアプローチ

### Red Phase (サービスディスカバリーのテスト)
```javascript
// test/service-discovery.test.js
describe('Service Discovery with Consul', () => {
  let consul;
  let services;
  
  beforeAll(async () => {
    // Consulクライアントの初期化
    consul = new ConsulClient({
      host: 'localhost',
      port: 8500,
      promisify: true
    });
    
    // テストサービスの準備
    services = [
      { name: 'api', port: 3001, tags: ['v1', 'production'] },
      { name: 'api', port: 3002, tags: ['v2', 'canary'] },
      { name: 'database', port: 5432, tags: ['primary', 'postgres'] },
      { name: 'cache', port: 6379, tags: ['redis', 'session'] }
    ];
  });

  it('should register services with health checks', async () => {
    const registrations = [];
    
    for (const service of services) {
      const registration = {
        id: `${service.name}-${service.port}`,
        name: service.name,
        port: service.port,
        tags: service.tags,
        check: {
          http: `http://localhost:${service.port}/health`,
          interval: '10s',
          timeout: '5s',
          deregister_critical_service_after: '30s'
        },
        meta: {
          version: service.tags.includes('v2') ? '2.0.0' : '1.0.0',
          environment: 'test'
        }
      };
      
      await consul.agent.service.register(registration);
      registrations.push(registration);
    }
    
    // 登録確認
    const catalog = await consul.catalog.service.list();
    expect(Object.keys(catalog)).toContain('api');
    expect(Object.keys(catalog)).toContain('database');
    expect(Object.keys(catalog)).toContain('cache');
    
    // 各サービスの詳細確認
    const apiServices = await consul.health.service('api');
    expect(apiServices).toHaveLength(2); // v1とv2
    
    // タグでのフィルタリング
    const v2Services = apiServices.filter(s => 
      s.Service.Tags.includes('v2')
    );
    expect(v2Services).toHaveLength(1);
    expect(v2Services[0].Service.Port).toBe(3002);
  });

  it('should handle service health state changes', async () => {
    // 初期状態：すべて健全
    let healthyServices = await consul.health.service('api', { passing: true });
    expect(healthyServices).toHaveLength(2);
    
    // 1つのサービスを不健全に
    await simulateServiceFailure('api-3001');
    
    // ヘルスチェックの更新を待つ
    await new Promise(resolve => setTimeout(resolve, 15000));
    
    // 健全なサービスのみ取得
    healthyServices = await consul.health.service('api', { passing: true });
    expect(healthyServices).toHaveLength(1);
    expect(healthyServices[0].Service.ID).toBe('api-3002');
    
    // 不健全なサービスも含めて取得
    const allServices = await consul.health.service('api');
    const unhealthyService = allServices.find(s => 
      s.Checks.some(c => c.Status === 'critical')
    );
    expect(unhealthyService).toBeDefined();
    expect(unhealthyService.Service.ID).toBe('api-3001');
  });

  it('should support DNS-based service discovery', async () => {
    const dns = require('dns').promises;
    
    // ConsulのDNSインターフェース経由で解決
    const addresses = await dns.resolve4('api.service.consul');
    
    expect(addresses).toHaveLength(2); // 2つのAPIサービス
    expect(addresses).toEqual(
      expect.arrayContaining(['127.0.0.1', '127.0.0.2'])
    );
    
    // SRVレコードでポート情報も取得
    const srvRecords = await dns.resolveSrv('_api._tcp.service.consul');
    
    expect(srvRecords).toHaveLength(2);
    expect(srvRecords).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ port: 3001 }),
        expect.objectContaining({ port: 3002 })
      ])
    );
    
    // タグベースのDNS解決
    const v2Addresses = await dns.resolve4('v2.api.service.consul');
    expect(v2Addresses).toHaveLength(1);
  });

  it('should provide client-side load balancing', async () => {
    const servicePool = new ServicePool(consul, 'api');
    await servicePool.initialize();
    
    const requestDistribution = {
      'api-3001': 0,
      'api-3002': 0
    };
    
    // 1000リクエストを送信
    for (let i = 0; i < 1000; i++) {
      const instance = await servicePool.getInstance();
      const response = await makeRequest(instance);
      
      requestDistribution[instance.id]++;
    }
    
    // ほぼ均等に分散（±10%）
    expect(requestDistribution['api-3001']).toBeGreaterThan(450);
    expect(requestDistribution['api-3001']).toBeLessThan(550);
    expect(requestDistribution['api-3002']).toBeGreaterThan(450);
    expect(requestDistribution['api-3002']).toBeLessThan(550);
    
    // ヘルスチェック失敗時の自動除外
    await simulateServiceFailure('api-3001');
    await servicePool.refresh();
    
    // 失敗後は全てapi-3002へ
    for (let i = 0; i < 100; i++) {
      const instance = await servicePool.getInstance();
      expect(instance.id).toBe('api-3002');
    }
  });

  it('should manage configuration through KV store', async () => {
    // 設定の保存
    const config = {
      database: {
        host: 'localhost',
        port: 5432,
        pool: {
          min: 2,
          max: 10
        }
      },
      cache: {
        ttl: 3600,
        maxSize: 1000
      },
      features: {
        newFeature: {
          enabled: false,
          rolloutPercentage: 0
        }
      }
    };
    
    await consul.kv.set('config/app/production', JSON.stringify(config));
    
    // 設定の取得
    const result = await consul.kv.get('config/app/production');
    const retrievedConfig = JSON.parse(result.Value);
    
    expect(retrievedConfig).toEqual(config);
    
    // 設定の監視（ウォッチ）
    const watcher = consul.watch({
      method: consul.kv.get,
      options: { key: 'config/app/production' }
    });
    
    const changes = [];
    watcher.on('change', (data) => {
      changes.push(JSON.parse(data.Value));
    });
    
    // 設定を更新
    config.features.newFeature.enabled = true;
    config.features.newFeature.rolloutPercentage = 10;
    await consul.kv.set('config/app/production', JSON.stringify(config));
    
    // 変更通知を確認
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    expect(changes).toHaveLength(1);
    expect(changes[0].features.newFeature.enabled).toBe(true);
    
    watcher.end();
  });

  it('should handle distributed locks', async () => {
    const lockKey = 'locks/critical-section';
    const results = [];
    
    // 3つの並行プロセスが同じリソースにアクセス
    const processes = Array(3).fill(0).map((_, i) => 
      (async () => {
        const session = await consul.session.create({
          ttl: '10s',
          behavior: 'delete'
        });
        
        // ロックの取得を試みる
        const acquired = await consul.kv.set({
          key: lockKey,
          value: `process-${i}`,
          acquire: session.id
        });
        
        if (acquired) {
          results.push({ process: i, action: 'acquired', time: Date.now() });
          
          // クリティカルセクション
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // ロックの解放
          await consul.kv.delete(lockKey);
          await consul.session.destroy(session.id);
          
          results.push({ process: i, action: 'released', time: Date.now() });
        } else {
          results.push({ process: i, action: 'failed', time: Date.now() });
        }
      })()
    );
    
    await Promise.all(processes);
    
    // 同時に1つのプロセスのみがロックを保持
    const acquiredCount = results.filter(r => r.action === 'acquired').length;
    expect(acquiredCount).toBeGreaterThanOrEqual(1);
    expect(acquiredCount).toBeLessThanOrEqual(3);
    
    // 各取得の間に最低1秒の間隔
    const acquiredEvents = results
      .filter(r => r.action === 'acquired')
      .sort((a, b) => a.time - b.time);
    
    for (let i = 1; i < acquiredEvents.length; i++) {
      const timeDiff = acquiredEvents[i].time - acquiredEvents[i-1].time;
      expect(timeDiff).toBeGreaterThanOrEqual(1000);
    }
  });

  it('should support prepared queries', async () => {
    // 準備されたクエリの作成（フェイルオーバー付き）
    const query = await consul.query.create({
      name: 'api-with-failover',
      service: {
        service: 'api',
        tags: ['production'],
        failover: {
          nearestN: 2,
          datacenters: ['dc2', 'dc3']
        }
      }
    });
    
    // クエリの実行
    const results = await consul.query.execute(query.ID);
    
    expect(results.Service).toBe('api');
    expect(results.Nodes).toHaveLength(1); // production tagを持つもの
    
    // DNSでも利用可能
    const dns = require('dns').promises;
    const addresses = await dns.resolve4('api-with-failover.query.consul');
    
    expect(addresses).toHaveLength(1);
  });
});

// サービスメッシュ機能のテスト
describe('Service Mesh Features', () => {
  it('should handle service intentions', async () => {
    // サービス間の通信ポリシー設定
    await consul.connect.intentions.create({
      source: 'web',
      destination: 'api',
      action: 'allow'
    });
    
    await consul.connect.intentions.create({
      source: 'web',
      destination: 'database',
      action: 'deny'
    });
    
    // インテンションの確認
    const intentions = await consul.connect.intentions.list();
    
    const webToApi = intentions.find(i => 
      i.Source === 'web' && i.Destination === 'api'
    );
    expect(webToApi.Action).toBe('allow');
    
    const webToDb = intentions.find(i => 
      i.Source === 'web' && i.Destination === 'database'
    );
    expect(webToDb.Action).toBe('deny');
  });
});
```

### Green Phase (サービスディスカバリー実装)
```javascript
// service-registry.js
const consul = require('consul');
const EventEmitter = require('events');

class ServiceRegistry extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.consul = consul({
      host: options.consulHost || 'consul',
      port: options.consulPort || 8500,
      promisify: true
    });
    
    this.serviceId = null;
    this.healthCheckInterval = null;
    this.watchHandles = new Map();
  }
  
  async register(serviceConfig) {
    const { name, port, tags = [], meta = {}, healthCheck } = serviceConfig;
    
    this.serviceId = `${name}-${port}-${process.pid}`;
    
    const registration = {
      id: this.serviceId,
      name,
      port,
      tags,
      meta: {
        ...meta,
        pid: process.pid.toString(),
        startTime: new Date().toISOString()
      },
      check: this.buildHealthCheck(healthCheck, port)
    };
    
    try {
      await this.consul.agent.service.register(registration);
      console.log(`Service ${this.serviceId} registered successfully`);
      
      // TTLベースのヘルスチェックの場合は定期更新
      if (healthCheck && healthCheck.ttl) {
        this.startTTLUpdate(healthCheck.ttl);
      }
      
      this.emit('registered', registration);
    } catch (error) {
      console.error('Service registration failed:', error);
      throw error;
    }
  }
  
  buildHealthCheck(healthCheck, port) {
    if (!healthCheck) {
      return {
        http: `http://localhost:${port}/health`,
        interval: '10s',
        timeout: '5s'
      };
    }
    
    if (healthCheck.ttl) {
      return {
        ttl: healthCheck.ttl,
        deregister_critical_service_after: '1m'
      };
    }
    
    if (healthCheck.script) {
      return {
        script: healthCheck.script,
        interval: healthCheck.interval || '10s'
      };
    }
    
    return {
      http: healthCheck.http || `http://localhost:${port}/health`,
      interval: healthCheck.interval || '10s',
      timeout: healthCheck.timeout || '5s',
      deregister_critical_service_after: healthCheck.deregister || '30s'
    };
  }
  
  startTTLUpdate(ttl) {
    // TTLの80%の間隔で更新
    const interval = this.parseTTL(ttl) * 0.8 * 1000;
    
    this.healthCheckInterval = setInterval(async () => {
      try {
        await this.consul.agent.check.pass(`service:${this.serviceId}`);
      } catch (error) {
        console.error('TTL update failed:', error);
      }
    }, interval);
  }
  
  parseTTL(ttl) {
    const match = ttl.match(/(\d+)([smh])/);
    if (!match) return 10;
    
    const value = parseInt(match[1]);
    const unit = match[2];
    
    switch (unit) {
      case 's': return value;
      case 'm': return value * 60;
      case 'h': return value * 3600;
      default: return 10;
    }
  }
  
  async deregister() {
    if (!this.serviceId) return;
    
    try {
      await this.consul.agent.service.deregister(this.serviceId);
      console.log(`Service ${this.serviceId} deregistered`);
      
      if (this.healthCheckInterval) {
        clearInterval(this.healthCheckInterval);
      }
      
      // ウォッチャーの停止
      for (const [key, watcher] of this.watchHandles) {
        watcher.end();
      }
      this.watchHandles.clear();
      
      this.emit('deregistered', this.serviceId);
    } catch (error) {
      console.error('Service deregistration failed:', error);
    }
  }
  
  async discover(serviceName, options = {}) {
    const { tags, passing = true, near = '_agent' } = options;
    
    const queryOptions = {
      passing,
      near,
      tag: tags
    };
    
    const services = await this.consul.health.service(serviceName, queryOptions);
    
    return services.map(entry => ({
      id: entry.Service.ID,
      address: entry.Service.Address || entry.Node.Address,
      port: entry.Service.Port,
      tags: entry.Service.Tags,
      meta: entry.Service.Meta,
      status: this.getOverallStatus(entry.Checks)
    }));
  }
  
  getOverallStatus(checks) {
    if (checks.some(c => c.Status === 'critical')) return 'critical';
    if (checks.some(c => c.Status === 'warning')) return 'warning';
    return 'passing';
  }
  
  watchService(serviceName, callback) {
    const watcher = this.consul.watch({
      method: this.consul.health.service,
      options: { service: serviceName, passing: true }
    });
    
    watcher.on('change', (data) => {
      const services = data.map(entry => ({
        id: entry.Service.ID,
        address: entry.Service.Address || entry.Node.Address,
        port: entry.Service.Port,
        tags: entry.Service.Tags,
        meta: entry.Service.Meta
      }));
      
      callback(services);
    });
    
    watcher.on('error', (err) => {
      console.error('Watch error:', err);
      this.emit('watch-error', { service: serviceName, error: err });
    });
    
    this.watchHandles.set(serviceName, watcher);
    
    return watcher;
  }
  
  async getConfig(key) {
    try {
      const result = await this.consul.kv.get(key);
      return result ? JSON.parse(result.Value) : null;
    } catch (error) {
      console.error(`Failed to get config ${key}:`, error);
      return null;
    }
  }
  
  async setConfig(key, value) {
    try {
      await this.consul.kv.set(key, JSON.stringify(value));
      this.emit('config-updated', { key, value });
    } catch (error) {
      console.error(`Failed to set config ${key}:`, error);
      throw error;
    }
  }
  
  watchConfig(key, callback) {
    const watcher = this.consul.watch({
      method: this.consul.kv.get,
      options: { key }
    });
    
    watcher.on('change', (data) => {
      const value = data ? JSON.parse(data.Value) : null;
      callback(value);
    });
    
    this.watchHandles.set(`config:${key}`, watcher);
    
    return watcher;
  }
  
  async acquireLock(key, options = {}) {
    const { ttl = '15s', behavior = 'release' } = options;
    
    // セッションの作成
    const session = await this.consul.session.create({
      ttl,
      behavior,
      lockdelay: '5s'
    });
    
    // ロックの取得
    const acquired = await this.consul.kv.set({
      key: `locks/${key}`,
      value: this.serviceId,
      acquire: session.id
    });
    
    if (acquired) {
      return new Lock(this.consul, key, session.id);
    }
    
    // ロックが取得できなかった場合はセッションを破棄
    await this.consul.session.destroy(session.id);
    return null;
  }
}

// 分散ロック実装
class Lock {
  constructor(consul, key, sessionId) {
    this.consul = consul;
    this.key = `locks/${key}`;
    this.sessionId = sessionId;
    this.renewInterval = null;
  }
  
  async release() {
    if (this.renewInterval) {
      clearInterval(this.renewInterval);
    }
    
    await this.consul.kv.delete(this.key);
    await this.consul.session.destroy(this.sessionId);
  }
  
  startRenewal(ttl = '15s') {
    const interval = this.parseTTL(ttl) * 0.5 * 1000;
    
    this.renewInterval = setInterval(async () => {
      try {
        await this.consul.session.renew(this.sessionId);
      } catch (error) {
        console.error('Session renewal failed:', error);
        clearInterval(this.renewInterval);
      }
    }, interval);
  }
  
  parseTTL(ttl) {
    const match = ttl.match(/(\d+)s/);
    return match ? parseInt(match[1]) : 15;
  }
}

// サービスプール（クライアント側ロードバランシング）
class ServicePool {
  constructor(registry, serviceName, options = {}) {
    this.registry = registry;
    this.serviceName = serviceName;
    this.instances = [];
    this.currentIndex = 0;
    this.strategy = options.strategy || 'round-robin';
    
    this.updateInterval = null;
    this.watcher = null;
  }
  
  async initialize() {
    // 初期サービスリストの取得
    await this.refresh();
    
    // 定期更新
    this.updateInterval = setInterval(() => {
      this.refresh();
    }, 30000); // 30秒ごと
    
    // リアルタイム更新
    this.watcher = this.registry.watchService(this.serviceName, (services) => {
      this.instances = services;
      console.log(`Service pool updated: ${services.length} instances`);
    });
  }
  
  async refresh() {
    this.instances = await this.registry.discover(this.serviceName);
  }
  
  async getInstance() {
    if (this.instances.length === 0) {
      throw new Error(`No healthy instances of ${this.serviceName}`);
    }
    
    switch (this.strategy) {
      case 'round-robin':
        return this.roundRobin();
      case 'random':
        return this.random();
      case 'least-connections':
        return this.leastConnections();
      default:
        return this.roundRobin();
    }
  }
  
  roundRobin() {
    const instance = this.instances[this.currentIndex];
    this.currentIndex = (this.currentIndex + 1) % this.instances.length;
    return instance;
  }
  
  random() {
    const index = Math.floor(Math.random() * this.instances.length);
    return this.instances[index];
  }
  
  leastConnections() {
    // 実装は接続数の追跡が必要
    return this.roundRobin();
  }
  
  destroy() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
    
    if (this.watcher) {
      this.watcher.end();
    }
  }
}

// アプリケーション統合例
class ServiceDiscoveryApp {
  constructor(config) {
    this.config = config;
    this.registry = new ServiceRegistry({
      consulHost: config.consulHost
    });
    
    this.servicePools = new Map();
  }
  
  async start() {
    // 自身のサービスを登録
    await this.registry.register({
      name: this.config.serviceName,
      port: this.config.port,
      tags: this.config.tags,
      healthCheck: {
        http: `/health`,
        interval: '10s'
      }
    });
    
    // 依存サービスのプールを初期化
    for (const dep of this.config.dependencies || []) {
      const pool = new ServicePool(this.registry, dep);
      await pool.initialize();
      this.servicePools.set(dep, pool);
    }
    
    // 設定の監視
    if (this.config.watchConfig) {
      this.registry.watchConfig(
        `config/${this.config.serviceName}`,
        (newConfig) => {
          console.log('Configuration updated:', newConfig);
          this.handleConfigUpdate(newConfig);
        }
      );
    }
    
    // グレースフルシャットダウン
    process.on('SIGTERM', async () => {
      await this.shutdown();
    });
  }
  
  async callService(serviceName, path, options = {}) {
    const pool = this.servicePools.get(serviceName);
    if (!pool) {
      throw new Error(`Service ${serviceName} not configured`);
    }
    
    const instance = await pool.getInstance();
    const url = `http://${instance.address}:${instance.port}${path}`;
    
    // 実際のHTTPリクエスト（簡略化）
    return fetch(url, options);
  }
  
  handleConfigUpdate(newConfig) {
    // アプリケーション固有の設定更新処理
    Object.assign(this.config, newConfig);
  }
  
  async shutdown() {
    console.log('Shutting down service...');
    
    // サービスプールの破棄
    for (const pool of this.servicePools.values()) {
      pool.destroy();
    }
    
    // サービス登録解除
    await this.registry.deregister();
    
    process.exit(0);
  }
}

module.exports = {
  ServiceRegistry,
  ServicePool,
  ServiceDiscoveryApp,
  Lock
};
```

### Consul設定
```hcl
# consul-config.hcl
datacenter = "dc1"
data_dir = "/opt/consul"
log_level = "INFO"
node_name = "consul-server-1"
server = true
bootstrap_expect = 3

ui_config {
  enabled = true
}

connect {
  enabled = true
}

ports {
  grpc = 8502
}

performance {
  raft_multiplier = 1
}

telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}

dns_config {
  enable_truncate = true
  only_passing = true
}
```

### Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Consulクラスター
  consul-server-1:
    image: consul:1.16
    command: agent -server -ui -node=server-1 -bootstrap-expect=3 -client=0.0.0.0
    ports:
      - "8500:8500"  # HTTP API
      - "8600:8600/udp"  # DNS
    volumes:
      - consul-data-1:/consul/data
    environment:
      CONSUL_BIND_INTERFACE: eth0
    networks:
      - consul-net

  consul-server-2:
    image: consul:1.16
    command: agent -server -node=server-2 -bootstrap-expect=3 -join=consul-server-1
    volumes:
      - consul-data-2:/consul/data
    environment:
      CONSUL_BIND_INTERFACE: eth0
    networks:
      - consul-net

  consul-server-3:
    image: consul:1.16
    command: agent -server -node=server-3 -bootstrap-expect=3 -join=consul-server-1
    volumes:
      - consul-data-3:/consul/data
    environment:
      CONSUL_BIND_INTERFACE: eth0
    networks:
      - consul-net

  # サンプルサービス
  api-v1:
    build: .
    environment:
      SERVICE_NAME: api
      SERVICE_PORT: 3001
      SERVICE_TAGS: "v1,production"
      CONSUL_HOST: consul-server-1
    ports:
      - "3001:3001"
    depends_on:
      - consul-server-1
    networks:
      - consul-net

  api-v2:
    build: .
    environment:
      SERVICE_NAME: api
      SERVICE_PORT: 3002
      SERVICE_TAGS: "v2,canary"
      CONSUL_HOST: consul-server-1
    ports:
      - "3002:3002"
    depends_on:
      - consul-server-1
    networks:
      - consul-net

  # モニタリング
  consul-exporter:
    image: prom/consul-exporter
    command:
      - '--consul.server=consul-server-1:8500'
    ports:
      - "9107:9107"
    networks:
      - consul-net

networks:
  consul-net:
    driver: bridge

volumes:
  consul-data-1:
  consul-data-2:
  consul-data-3:
```

## WSL環境でのマルチホスト構成

### WSLインスタンスの準備
```bash
# WSL1 (メイン)
wsl --install -d Ubuntu-22.04

# WSL2 (追加ホスト)
wsl --import Ubuntu-Host2 C:\WSL\Host2 ubuntu.tar

# WSL3 (追加ホスト)
wsl --import Ubuntu-Host3 C:\WSL\Host3 ubuntu.tar
```

### ネットワーク設定
```bash
# 各WSLでのIPアドレス確認
ip addr show eth0

# hosts ファイルの更新
echo "172.x.x.x wsl-host1" >> /etc/hosts
echo "172.x.x.y wsl-host2" >> /etc/hosts
echo "172.x.x.z wsl-host3" >> /etc/hosts
```

### 分散Consulセットアップ
```bash
# Host1でConsulサーバー起動
consul agent -server -bootstrap-expect=3 \
  -node=wsl-host1 \
  -bind=172.x.x.x \
  -client=0.0.0.0 \
  -ui

# Host2でConsulサーバー起動
consul agent -server \
  -node=wsl-host2 \
  -bind=172.x.x.y \
  -join=172.x.x.x \
  -client=0.0.0.0

# Host3でConsulサーバー起動
consul agent -server \
  -node=wsl-host3 \
  -bind=172.x.x.z \
  -join=172.x.x.x \
  -client=0.0.0.0
```

## 実行と検証

### 1. Consulクラスター起動
```bash
docker-compose up -d consul-server-1 consul-server-2 consul-server-3

# クラスター状態確認
docker exec consul-server-1 consul members

# UI確認
open http://localhost:8500
```

### 2. サービス登録と確認
```bash
# サービス起動
docker-compose up -d api-v1 api-v2

# 登録サービス確認
curl http://localhost:8500/v1/catalog/services | jq

# 特定サービスの詳細
curl http://localhost:8500/v1/health/service/api | jq
```

### 3. DNS解決テスト
```bash
# DNSクエリ
dig @localhost -p 8600 api.service.consul

# SRVレコード
dig @localhost -p 8600 api.service.consul SRV

# タグベース
dig @localhost -p 8600 v2.api.service.consul
```

## 成功基準

- [ ] 3ノードConsulクラスターの安定稼働
- [ ] サービスの自動登録と健全性監視
- [ ] DNS/HTTP APIでのサービス解決
- [ ] 設定変更の即時反映（Watch機能）
- [ ] 分散ロックの正常動作

## 運用ガイド

### バックアップとリストア
```bash
# スナップショット作成
consul snapshot save backup.snap

# リストア
consul snapshot restore backup.snap
```

### ACL設定
```bash
# ACL有効化
consul acl bootstrap

# トークン作成
consul acl token create -description "api-service" \
  -policy-name "api-policy"
```

## トラブルシューティング

### 問題: サービスが見つからない
```bash
# ヘルスチェック状態確認
curl http://localhost:8500/v1/health/checks/api

# ログ確認
docker logs consul-server-1
```

### 問題: リーダー選出失敗
```bash
# Raftステータス確認
curl http://localhost:8500/v1/status/leader

# ピア情報
curl http://localhost:8500/v1/status/peers
```

## 次のステップ

サービスディスカバリーを確立後、`15_multi_server_data_partition`でデータパーティショニングを実装します。

## 学んだこと

- 動的なサービス登録と発見の威力
- ヘルスチェックによる自動回復
- 設定の集中管理とリアルタイム更新
- 分散システムの協調メカニズム

## 参考資料

- [Consul Documentation](https://www.consul.io/docs)
- [Service Discovery Patterns](https://microservices.io/patterns/server-side-discovery.html)
- [Consul Best Practices](https://www.consul.io/docs/install/performance)
- [HashiCorp Learn](https://learn.hashicorp.com/consul)