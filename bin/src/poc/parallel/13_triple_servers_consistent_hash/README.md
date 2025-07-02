# 13_triple_servers_consistent_hash

## 概要

3台以上のサーバーでConsistent Hashingを実装し、スケーラブルで柔軟な分散システムを構築します。サーバーの追加・削除時のデータ移動を最小化します。

## 目的

- Consistent Hashingアルゴリズムの実装
- 最小限のデータ再配置
- 仮想ノードによる負荷均等化
- 動的なサーバー追加・削除

## アーキテクチャ

```
┌─────────────────────────────────┐
│       Consistent Hash Ring      │
│                                 │
│         0°    Server-1          │
│       ╱   ╲   (vnodes)         │
│     ╱       ╲                  │
│   Server-3    ╲                │
│  (vnodes)      90°             │
│   │                            │
│   │         Hash(Key)          │
│   │            ↓               │
│ 270°         180°              │
│     ╲       ╱                 │
│       ╲   ╱  Server-2         │
│         ╲╱   (vnodes)         │
│                                │
└─────────────────────────────────┘
         │
         ▼
┌────────┬────────┬────────┐
│Server-1│Server-2│Server-3│
│ 33.3%  │ 33.3%  │ 33.3%  │
│        │        │        │
│ Data   │ Data   │ Data   │
│ Range  │ Range  │ Range  │
└────────┴────────┴────────┘
```

## 検証項目

### 1. Consistent Hashingの実装
- **ハッシュ関数**: MD5, SHA-1, MurmurHash
- **仮想ノード数**: 負荷分散の均等性
- **キー配置**: データの分散状況
- **リング構造**: ノードの配置と探索

### 2. スケーラビリティ
- **サーバー追加**: 影響を受けるキーの割合
- **サーバー削除**: データ移行の効率
- **リバランシング**: 自動的な再配置
- **ホットスポット回避**: 仮想ノードの効果

### 3. 可用性とレプリケーション
- **レプリカ配置**: N個の後続ノード
- **読み取りクォーラム**: R個のレプリカから読む
- **書き込みクォーラム**: W個のレプリカに書く
- **整合性レベル**: 調整可能な一貫性

## TDDアプローチ

### Red Phase (Consistent Hashingのテスト)
```javascript
// test/consistent-hashing.test.js
describe('Consistent Hashing Implementation', () => {
  let hashRing;
  let servers;
  
  beforeAll(() => {
    // 初期3サーバー構成
    servers = [
      { id: 'server-1', host: 'localhost:5001', vnodes: 150 },
      { id: 'server-2', host: 'localhost:5002', vnodes: 150 },
      { id: 'server-3', host: 'localhost:5003', vnodes: 150 }
    ];
    
    hashRing = new ConsistentHashRing({
      hashFunction: 'md5',
      virtualNodes: 150,
      servers: servers
    });
  });

  it('should distribute keys evenly across servers', () => {
    const keyCount = 10000;
    const distribution = {
      'server-1': 0,
      'server-2': 0,
      'server-3': 0
    };
    
    // 大量のキーを生成して分散を確認
    for (let i = 0; i < keyCount; i++) {
      const key = `key-${i}`;
      const server = hashRing.getNode(key);
      distribution[server.id]++;
    }
    
    // 理想的な分散は33.33%ずつ
    const idealCount = keyCount / 3;
    
    Object.entries(distribution).forEach(([server, count]) => {
      const deviation = Math.abs(count - idealCount) / idealCount;
      console.log(`${server}: ${count} keys (${(count/keyCount*100).toFixed(2)}%)`);
      
      // 5%以内の偏差を許容
      expect(deviation).toBeLessThan(0.05);
    });
    
    // 標準偏差の確認
    const values = Object.values(distribution);
    const stdDev = calculateStandardDeviation(values);
    expect(stdDev).toBeLessThan(idealCount * 0.05);
  });

  it('should minimize data movement when adding a server', () => {
    // 既存のキー配置を記録
    const keyCount = 10000;
    const originalPlacement = new Map();
    
    for (let i = 0; i < keyCount; i++) {
      const key = `key-${i}`;
      const server = hashRing.getNode(key);
      originalPlacement.set(key, server.id);
    }
    
    // 新しいサーバーを追加
    const newServer = { id: 'server-4', host: 'localhost:5004', vnodes: 150 };
    hashRing.addServer(newServer);
    
    // 移動したキーを数える
    let movedKeys = 0;
    const movementDetails = {
      'server-1': { lost: 0, gained: 0 },
      'server-2': { lost: 0, gained: 0 },
      'server-3': { lost: 0, gained: 0 },
      'server-4': { lost: 0, gained: 0 }
    };
    
    for (let i = 0; i < keyCount; i++) {
      const key = `key-${i}`;
      const newServer = hashRing.getNode(key);
      const oldServerId = originalPlacement.get(key);
      
      if (newServer.id !== oldServerId) {
        movedKeys++;
        movementDetails[oldServerId].lost++;
        movementDetails[newServer.id].gained++;
      }
    }
    
    // 理論的な移動率: 1/4 (25%)
    const moveRate = movedKeys / keyCount;
    console.log(`Moved keys: ${movedKeys}/${keyCount} (${(moveRate*100).toFixed(2)}%)`);
    console.log('Movement details:', movementDetails);
    
    // 実際の移動率が理論値に近いことを確認
    expect(moveRate).toBeGreaterThan(0.20);
    expect(moveRate).toBeLessThan(0.30);
    
    // 新サーバーがほぼ均等に引き受けたことを確認
    expect(movementDetails['server-4'].gained).toBeGreaterThan(movedKeys * 0.9);
  });

  it('should handle server removal gracefully', () => {
    // レプリケーション設定
    const replicatedRing = new ConsistentHashRing({
      servers: servers,
      replicationFactor: 3
    });
    
    // データを配置
    const data = new Map();
    for (let i = 0; i < 1000; i++) {
      const key = `item-${i}`;
      const value = { data: `value-${i}`, version: 1 };
      
      // プライマリと2つのレプリカに保存
      const nodes = replicatedRing.getNodes(key, 3);
      data.set(key, { primary: nodes[0].id, replicas: nodes.slice(1).map(n => n.id) });
    }
    
    // server-2を削除
    replicatedRing.removeServer('server-2');
    
    // すべてのデータがまだアクセス可能か確認
    let accessibleCount = 0;
    let replicationMaintained = 0;
    
    for (const [key, placement] of data.entries()) {
      const newNodes = replicatedRing.getNodes(key, 3);
      
      // 少なくとも1つのレプリカが残っているか
      const survivingReplicas = placement.replicas.filter(r => r !== 'server-2');
      if (placement.primary !== 'server-2' || survivingReplicas.length > 0) {
        accessibleCount++;
      }
      
      // レプリケーション係数が維持されているか
      if (newNodes.length === 3) {
        replicationMaintained++;
      }
    }
    
    // すべてのデータがアクセス可能
    expect(accessibleCount).toBe(1000);
    
    // レプリケーションが再構築される
    expect(replicationMaintained).toBe(1000);
  });

  it('should support virtual nodes for better distribution', () => {
    // 仮想ノード数による分散の改善を検証
    const testConfigs = [
      { vnodes: 1, expectedStdDev: 0.15 },
      { vnodes: 10, expectedStdDev: 0.10 },
      { vnodes: 50, expectedStdDev: 0.05 },
      { vnodes: 150, expectedStdDev: 0.03 }
    ];
    
    const results = [];
    
    for (const config of testConfigs) {
      const ring = new ConsistentHashRing({
        servers: servers.map(s => ({ ...s, vnodes: config.vnodes })),
        virtualNodes: config.vnodes
      });
      
      // キー分散をテスト
      const distribution = testKeyDistribution(ring, 10000);
      const stdDevRatio = distribution.stdDev / distribution.mean;
      
      results.push({
        vnodes: config.vnodes,
        stdDevRatio,
        maxDeviation: distribution.maxDeviation
      });
      
      // 期待される標準偏差以下であることを確認
      expect(stdDevRatio).toBeLessThan(config.expectedStdDev);
    }
    
    console.table(results);
    
    // 仮想ノードが増えるほど分散が改善
    for (let i = 1; i < results.length; i++) {
      expect(results[i].stdDevRatio).toBeLessThan(results[i-1].stdDevRatio);
    }
  });

  it('should handle hot keys with bounded loads', () => {
    // Consistent Hashing with Bounded Loadsの実装
    const boundedRing = new ConsistentHashRing({
      servers: servers,
      loadFactor: 1.25 // 25%の過負荷まで許容
    });
    
    // ホットキーをシミュレート
    const hotKeys = ['popular-item-1', 'viral-content', 'trending-topic'];
    const normalKeys = Array(1000).fill(0).map((_, i) => `normal-key-${i}`);
    
    const load = {
      'server-1': 0,
      'server-2': 0,
      'server-3': 0
    };
    
    // ホットキーは100倍のアクセス
    for (const key of hotKeys) {
      const server = boundedRing.getNodeWithBoundedLoad(key, 100);
      load[server.id] += 100;
    }
    
    // 通常キー
    for (const key of normalKeys) {
      const server = boundedRing.getNodeWithBoundedLoad(key, 1);
      load[server.id] += 1;
    }
    
    // 負荷の確認
    const totalLoad = Object.values(load).reduce((a, b) => a + b, 0);
    const avgLoad = totalLoad / 3;
    
    console.log('Load distribution:', load);
    console.log(`Average load: ${avgLoad}`);
    
    // どのサーバーも平均の125%を超えない
    Object.values(load).forEach(serverLoad => {
      expect(serverLoad).toBeLessThan(avgLoad * 1.25);
    });
  });

  it('should support range queries efficiently', () => {
    // 順序を保持するConsistent Hashingの拡張
    const orderedRing = new OrderPreservingHashRing({
      servers: servers,
      partitions: 100
    });
    
    // 連続したキーを挿入
    const startKey = 'user:1000';
    const endKey = 'user:2000';
    
    // 範囲クエリの実行
    const rangeServers = orderedRing.getServersForRange(startKey, endKey);
    
    // 最大3台のサーバーに分散（理想的）
    expect(rangeServers.length).toBeLessThanOrEqual(3);
    
    // 各サーバーが担当する範囲
    const ranges = orderedRing.getRangesPerServer();
    console.log('Range assignments:', ranges);
    
    // 範囲が重複していないことを確認
    for (let i = 0; i < ranges.length - 1; i++) {
      expect(ranges[i].end).toBeLessThanOrEqual(ranges[i + 1].start);
    }
  });
});

// クォーラムベースの読み書きテスト
describe('Quorum-based Operations', () => {
  it('should handle read/write with configurable consistency', async () => {
    const quorumRing = new ConsistentHashRing({
      servers: servers,
      replicationFactor: 3,
      readQuorum: 2,    // R = 2
      writeQuorum: 2    // W = 2
    });
    
    // 書き込みテスト
    const key = 'important-data';
    const value = { content: 'critical', timestamp: Date.now() };
    
    const writeResult = await quorumRing.write(key, value);
    
    expect(writeResult.successful).toBeGreaterThanOrEqual(2);
    expect(writeResult.failed).toBeLessThanOrEqual(1);
    
    // 読み取りテスト
    const readResult = await quorumRing.read(key);
    
    expect(readResult.successful).toBeGreaterThanOrEqual(2);
    expect(readResult.value).toEqual(value);
    
    // 一貫性の検証 (R + W > N)
    const N = 3; // レプリケーション係数
    const R = 2; // 読み取りクォーラム
    const W = 2; // 書き込みクォーラム
    
    expect(R + W).toBeGreaterThan(N); // 強一貫性を保証
  });
});
```

### Green Phase (Consistent Hashing実装)
```javascript
// consistent-hash-ring.js
const crypto = require('crypto');

class ConsistentHashRing {
  constructor(options = {}) {
    this.servers = new Map();
    this.ring = new Map();
    this.sortedKeys = [];
    
    this.virtualNodes = options.virtualNodes || 150;
    this.hashFunction = options.hashFunction || 'md5';
    this.replicationFactor = options.replicationFactor || 1;
    this.loadFactor = options.loadFactor || 1.0;
    
    // 負荷追跡
    this.loads = new Map();
    
    // 初期サーバーを追加
    if (options.servers) {
      options.servers.forEach(server => this.addServer(server));
    }
  }
  
  hash(key) {
    return crypto
      .createHash(this.hashFunction)
      .update(key)
      .digest('hex');
  }
  
  hashToPosition(hash) {
    // ハッシュを0-2^32の整数に変換
    return parseInt(hash.substring(0, 8), 16);
  }
  
  addServer(server) {
    if (this.servers.has(server.id)) {
      throw new Error(`Server ${server.id} already exists`);
    }
    
    this.servers.set(server.id, server);
    this.loads.set(server.id, 0);
    
    // 仮想ノードを追加
    const vnodes = server.vnodes || this.virtualNodes;
    
    for (let i = 0; i < vnodes; i++) {
      const virtualKey = `${server.id}:${i}`;
      const hash = this.hash(virtualKey);
      const position = this.hashToPosition(hash);
      
      this.ring.set(position, {
        id: server.id,
        server: server,
        virtual: i
      });
    }
    
    // ソート済みキーを更新
    this.updateSortedKeys();
    
    console.log(`Added server ${server.id} with ${vnodes} virtual nodes`);
  }
  
  removeServer(serverId) {
    if (!this.servers.has(serverId)) {
      throw new Error(`Server ${serverId} not found`);
    }
    
    // リングから仮想ノードを削除
    const toRemove = [];
    
    for (const [position, node] of this.ring.entries()) {
      if (node.id === serverId) {
        toRemove.push(position);
      }
    }
    
    toRemove.forEach(position => this.ring.delete(position));
    
    this.servers.delete(serverId);
    this.loads.delete(serverId);
    
    // ソート済みキーを更新
    this.updateSortedKeys();
    
    console.log(`Removed server ${serverId} (${toRemove.length} virtual nodes)`);
  }
  
  updateSortedKeys() {
    this.sortedKeys = Array.from(this.ring.keys()).sort((a, b) => a - b);
  }
  
  getNode(key) {
    if (this.sortedKeys.length === 0) {
      throw new Error('No servers available');
    }
    
    const hash = this.hash(key);
    const position = this.hashToPosition(hash);
    
    // 二分探索で最初の大きいキーを見つける
    let left = 0;
    let right = this.sortedKeys.length - 1;
    
    while (left < right) {
      const mid = Math.floor((left + right) / 2);
      if (this.sortedKeys[mid] < position) {
        left = mid + 1;
      } else {
        right = mid;
      }
    }
    
    // リングをラップアラウンド
    const nodePosition = this.sortedKeys[left] >= position 
      ? this.sortedKeys[left] 
      : this.sortedKeys[0];
    
    return this.ring.get(nodePosition).server;
  }
  
  getNodes(key, count = 1) {
    if (count > this.servers.size) {
      count = this.servers.size;
    }
    
    const nodes = [];
    const seen = new Set();
    
    const hash = this.hash(key);
    const position = this.hashToPosition(hash);
    
    // 開始位置を見つける
    let startIdx = this.sortedKeys.findIndex(k => k >= position);
    if (startIdx === -1) startIdx = 0;
    
    // 時計回りに探索
    let idx = startIdx;
    while (nodes.length < count) {
      const nodePosition = this.sortedKeys[idx];
      const node = this.ring.get(nodePosition);
      
      if (!seen.has(node.id)) {
        nodes.push(node.server);
        seen.add(node.id);
      }
      
      idx = (idx + 1) % this.sortedKeys.length;
      
      // 一周した場合は終了
      if (idx === startIdx && nodes.length > 0) break;
    }
    
    return nodes;
  }
  
  getNodeWithBoundedLoad(key, weight = 1) {
    const candidates = this.getNodes(key, this.servers.size);
    
    for (const server of candidates) {
      const currentLoad = this.loads.get(server.id) || 0;
      const avgLoad = this.getTotalLoad() / this.servers.size;
      const maxLoad = avgLoad * this.loadFactor;
      
      if (currentLoad + weight <= maxLoad) {
        this.loads.set(server.id, currentLoad + weight);
        return server;
      }
    }
    
    // すべてのサーバーが過負荷の場合は最初の候補を返す
    const server = candidates[0];
    this.loads.set(server.id, (this.loads.get(server.id) || 0) + weight);
    return server;
  }
  
  getTotalLoad() {
    return Array.from(this.loads.values()).reduce((a, b) => a + b, 0);
  }
  
  async write(key, value, options = {}) {
    const quorum = options.writeQuorum || Math.floor(this.replicationFactor / 2) + 1;
    const nodes = this.getNodes(key, this.replicationFactor);
    
    const results = await Promise.allSettled(
      nodes.map(node => this.writeToNode(node, key, value))
    );
    
    const successful = results.filter(r => r.status === 'fulfilled').length;
    const failed = results.filter(r => r.status === 'rejected').length;
    
    if (successful < quorum) {
      throw new Error(`Write failed: only ${successful}/${quorum} nodes responded`);
    }
    
    return { successful, failed, quorum };
  }
  
  async read(key, options = {}) {
    const quorum = options.readQuorum || Math.floor(this.replicationFactor / 2) + 1;
    const nodes = this.getNodes(key, this.replicationFactor);
    
    const results = await Promise.allSettled(
      nodes.map(node => this.readFromNode(node, key))
    );
    
    const successful = results.filter(r => r.status === 'fulfilled');
    
    if (successful.length < quorum) {
      throw new Error(`Read failed: only ${successful.length}/${quorum} nodes responded`);
    }
    
    // 最新のバージョンを選択（タイムスタンプベース）
    const values = successful.map(r => r.value);
    const latest = values.reduce((a, b) => 
      a.timestamp > b.timestamp ? a : b
    );
    
    return {
      value: latest,
      successful: successful.length,
      quorum
    };
  }
  
  async writeToNode(node, key, value) {
    // 実際の実装ではHTTPリクエストなど
    console.log(`Writing to ${node.id}: ${key}`);
    return { success: true };
  }
  
  async readFromNode(node, key) {
    // 実際の実装ではHTTPリクエストなど
    console.log(`Reading from ${node.id}: ${key}`);
    return { data: 'value', timestamp: Date.now() };
  }
  
  getStatistics() {
    const stats = {
      servers: this.servers.size,
      virtualNodes: this.sortedKeys.length,
      avgVirtualNodesPerServer: this.sortedKeys.length / this.servers.size,
      keyDistribution: this.analyzeKeyDistribution(),
      loadDistribution: Object.fromEntries(this.loads)
    };
    
    return stats;
  }
  
  analyzeKeyDistribution() {
    // リング上の各セグメントのサイズを計算
    const segments = [];
    
    for (let i = 0; i < this.sortedKeys.length; i++) {
      const start = this.sortedKeys[i];
      const end = this.sortedKeys[(i + 1) % this.sortedKeys.length];
      
      const size = end > start ? end - start : (Math.pow(2, 32) - start + end);
      const node = this.ring.get(start);
      
      segments.push({
        server: node.id,
        size: size,
        percentage: (size / Math.pow(2, 32)) * 100
      });
    }
    
    // サーバーごとに集計
    const distribution = {};
    
    for (const segment of segments) {
      if (!distribution[segment.server]) {
        distribution[segment.server] = {
          segments: 0,
          totalSize: 0,
          percentage: 0
        };
      }
      
      distribution[segment.server].segments++;
      distribution[segment.server].totalSize += segment.size;
      distribution[segment.server].percentage += segment.percentage;
    }
    
    return distribution;
  }
}

// 順序保持版（範囲クエリ対応）
class OrderPreservingHashRing extends ConsistentHashRing {
  constructor(options) {
    super(options);
    this.partitions = options.partitions || 100;
    this.setupPartitions();
  }
  
  setupPartitions() {
    // キー空間を均等に分割
    const partitionSize = Math.pow(2, 32) / this.partitions;
    
    this.partitionMap = new Map();
    
    for (let i = 0; i < this.partitions; i++) {
      const start = i * partitionSize;
      const end = (i + 1) * partitionSize - 1;
      
      // 各パーティションをサーバーに割り当て
      const serverIdx = i % this.servers.size;
      const server = Array.from(this.servers.values())[serverIdx];
      
      this.partitionMap.set(i, {
        start,
        end,
        server: server.id
      });
    }
  }
  
  getServersForRange(startKey, endKey) {
    const startHash = this.hashToPosition(this.hash(startKey));
    const endHash = this.hashToPosition(this.hash(endKey));
    
    const servers = new Set();
    
    // 範囲に含まれるパーティションを見つける
    for (const [id, partition] of this.partitionMap.entries()) {
      if (
        (partition.start <= startHash && startHash <= partition.end) ||
        (partition.start <= endHash && endHash <= partition.end) ||
        (startHash <= partition.start && partition.end <= endHash)
      ) {
        servers.add(partition.server);
      }
    }
    
    return Array.from(servers).map(id => this.servers.get(id));
  }
  
  getRangesPerServer() {
    const ranges = new Map();
    
    for (const [id, partition] of this.partitionMap.entries()) {
      if (!ranges.has(partition.server)) {
        ranges.set(partition.server, []);
      }
      
      ranges.get(partition.server).push({
        partitionId: id,
        start: partition.start,
        end: partition.end
      });
    }
    
    // 各サーバーの範囲を結合
    const result = [];
    
    for (const [server, partitions] of ranges.entries()) {
      // ソートして連続する範囲を結合
      partitions.sort((a, b) => a.start - b.start);
      
      const merged = [];
      let current = partitions[0];
      
      for (let i = 1; i < partitions.length; i++) {
        if (current.end + 1 === partitions[i].start) {
          current.end = partitions[i].end;
        } else {
          merged.push(current);
          current = partitions[i];
        }
      }
      
      merged.push(current);
      
      result.push({
        server,
        ranges: merged
      });
    }
    
    return result;
  }
}

module.exports = { ConsistentHashRing, OrderPreservingHashRing };
```

### Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Consistent Hashingコーディネーター
  coordinator:
    build:
      context: .
      dockerfile: Dockerfile.coordinator
    ports:
      - "8080:8080"
    environment:
      SERVERS: "server-1:5001,server-2:5002,server-3:5003"
      VIRTUAL_NODES: 150
      REPLICATION_FACTOR: 3
    depends_on:
      - server-1
      - server-2
      - server-3

  server-1:
    build: .
    ports:
      - "5001:5000"
    environment:
      SERVER_ID: server-1
      SERVER_PORT: 5000
      DATA_DIR: /data
    volumes:
      - server1-data:/data

  server-2:
    build: .
    ports:
      - "5002:5000"
    environment:
      SERVER_ID: server-2
      SERVER_PORT: 5000
      DATA_DIR: /data
    volumes:
      - server2-data:/data

  server-3:
    build: .
    ports:
      - "5003:5000"
    environment:
      SERVER_ID: server-3
      SERVER_PORT: 5000
      DATA_DIR: /data
    volumes:
      - server3-data:/data

  # 監視
  monitor:
    build:
      context: .
      dockerfile: Dockerfile.monitor
    ports:
      - "9000:9000"
    environment:
      COORDINATOR_URL: http://coordinator:8080

volumes:
  server1-data:
  server2-data:
  server3-data:
```

## 実行と検証

### 1. システム起動
```bash
docker-compose up -d

# リングの状態確認
curl http://localhost:8080/api/ring/status | jq
```

### 2. キー分散テスト
```bash
# テストデータの投入
npm run test:distribution -- --keys=10000

# 分散状況の確認
curl http://localhost:8080/api/ring/statistics | jq
```

### 3. サーバー追加/削除テスト
```bash
# 新サーバー追加
docker-compose up -d server-4

# リングに追加
curl -X POST http://localhost:8080/api/ring/servers \
  -H "Content-Type: application/json" \
  -d '{"id": "server-4", "host": "server-4:5000"}'

# データ移動の確認
curl http://localhost:8080/api/ring/rebalance/status | jq
```

## 成功基準

- [ ] キー分散の標準偏差が5%以内
- [ ] サーバー追加時のデータ移動が25%±5%
- [ ] 3ノードレプリケーションで99.9%可用性
- [ ] 仮想ノード150個で均等分散
- [ ] 範囲クエリの効率的サポート

## 運用ガイド

### リング可視化
```bash
# リングの視覚的表示
curl http://localhost:9000/visualize/ring

# キー配置の確認
curl http://localhost:8080/api/ring/lookup?key=user:123
```

### リバランシング
```bash
# 手動リバランシング開始
curl -X POST http://localhost:8080/api/ring/rebalance

# 進捗確認
watch -n 1 'curl -s http://localhost:8080/api/ring/rebalance/progress'
```

## トラブルシューティング

### 問題: キー分散が偏る
```bash
# 仮想ノード数を増やす
curl -X PUT http://localhost:8080/api/ring/config \
  -d '{"virtualNodes": 300}'

# 再配置
curl -X POST http://localhost:8080/api/ring/redistribute
```

### 問題: ホットキー
```bash
# Bounded Loadを有効化
curl -X PUT http://localhost:8080/api/ring/config \
  -d '{"loadFactor": 1.25}'
```

## 次のステップ

Consistent Hashingを確立後、`14_multi_server_service_discovery`でサービスディスカバリーを実装します。

## 学んだこと

- 最小限のデータ移動でのスケーリング
- 仮想ノードによる負荷均等化
- レプリケーションとクォーラム
- 分散システムの基本アルゴリズム

## 参考資料

- [Consistent Hashing Paper](https://www.cs.princeton.edu/courses/archive/fall09/cos518/papers/chash.pdf)
- [Dynamo: Amazon's Highly Available Key-value Store](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
- [Chord: A Scalable Peer-to-peer Lookup Service](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf)
- [Consistent Hashing with Bounded Loads](https://ai.googleblog.com/2017/04/consistent-hashing-with-bounded-loads.html)