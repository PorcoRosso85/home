# 15_multi_server_data_partition

## 概要

複数サーバー環境でのデータパーティショニング戦略を実装し、大規模データセットの効率的な分散と管理を実現します。シャーディング、レプリケーション、データローカリティを最適化します。

## 目的

- 水平パーティショニング（シャーディング）
- データローカリティの最適化
- クロスシャードクエリの実装
- リバランシングとマイグレーション

## アーキテクチャ

```
┌─────────────────────────────────┐
│     Data Partitioning Layer     │
│  ┌─────────────────────────┐    │
│  │ Partition Strategy:     │    │
│  │ - Range-based          │    │
│  │ - Hash-based           │    │
│  │ - Geographic           │    │
│  │ - Composite            │    │
│  └─────────────────────────┘    │
└────────────┬────────────────────┘
             │
    ┌────────┼────────┬────────┐
    │        │        │        │
┌───▼───┐ ┌─▼────┐ ┌▼─────┐ ┌▼─────┐
│Shard-1│ │Shard-2│ │Shard-3│ │Shard-4│
│[A-F]  │ │[G-M]  │ │[N-S]  │ │[T-Z]  │
│       │ │       │ │       │ │       │
│Primary│ │Primary│ │Primary│ │Primary│
│Replica│ │Replica│ │Replica│ │Replica│
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    │         │         │         │
    └─────────┼─────────┼─────────┘
              │         │
        [Cross-Shard Queries]
```

## 検証項目

### 1. パーティション戦略
- **範囲ベース**: 連続した値による分割
- **ハッシュベース**: 均等分散
- **地理的分割**: リージョンベース
- **複合キー**: 多次元パーティショニング

### 2. データ分散と負荷均衡
- **ホットスポット回避**: 動的リバランシング
- **データスキュー対策**: 適応的分割
- **読み取り/書き込み分離**: レプリカ活用
- **キャッシュ戦略**: ローカルキャッシュ

### 3. クロスシャード操作
- **分散JOIN**: Scatter-Gather pattern
- **分散トランザクション**: 2PC/Saga
- **集計クエリ**: Map-Reduce
- **グローバルインデックス**: 分散インデックス

### 4. 運用とメンテナンス
- **オンラインリシャーディング**: 無停止
- **データマイグレーション**: 段階的移行
- **バックアップ/リストア**: シャード単位
- **監視とアラート**: シャード健全性

## TDDアプローチ

### Red Phase (データパーティショニングのテスト)
```javascript
// test/data-partitioning.test.js
describe('Multi-Server Data Partitioning', () => {
  let partitionManager;
  let shards;
  
  beforeAll(async () => {
    // 4シャード構成の初期化
    shards = await Promise.all([
      createShard({ id: 'shard-1', range: 'A-F', port: 5001 }),
      createShard({ id: 'shard-2', range: 'G-M', port: 5002 }),
      createShard({ id: 'shard-3', range: 'N-S', port: 5003 }),
      createShard({ id: 'shard-4', range: 'T-Z', port: 5004 })
    ]);
    
    partitionManager = new PartitionManager({
      shards,
      strategy: 'range-based',
      replicationFactor: 2
    });
  });

  it('should distribute data evenly across shards', async () => {
    // 大量のテストデータを生成
    const testData = generateTestUsers(10000);
    
    // データを挿入
    const insertPromises = testData.map(user => 
      partitionManager.insert('users', user)
    );
    
    await Promise.all(insertPromises);
    
    // 各シャードのデータ数を確認
    const distribution = await partitionManager.getDistribution('users');
    
    console.log('Data distribution:', distribution);
    
    // 理想的な分散（25%ずつ）からの偏差を確認
    const idealCount = 2500;
    Object.values(distribution).forEach(count => {
      const deviation = Math.abs(count - idealCount) / idealCount;
      expect(deviation).toBeLessThan(0.15); // 15%以内の偏差
    });
    
    // 標準偏差も確認
    const counts = Object.values(distribution);
    const stdDev = calculateStandardDeviation(counts);
    expect(stdDev).toBeLessThan(idealCount * 0.1);
  });

  it('should handle range queries efficiently', async () => {
    // 範囲クエリのテスト
    const rangeQueries = [
      { start: 'A', end: 'C' },    // 単一シャード
      { start: 'E', end: 'H' },    // 2シャードにまたがる
      { start: 'A', end: 'Z' },    // 全シャード
      { start: 'M', end: 'N' }     // 境界ケース
    ];
    
    for (const query of rangeQueries) {
      const startTime = Date.now();
      
      const results = await partitionManager.rangeQuery(
        'users',
        { 
          where: { 
            name: { $gte: query.start, $lte: query.end } 
          }
        }
      );
      
      const queryTime = Date.now() - startTime;
      
      // クエリが正しいデータを返すか確認
      results.forEach(user => {
        expect(user.name[0]).toBeGreaterThanOrEqual(query.start);
        expect(user.name[0]).toBeLessThanOrEqual(query.end);
      });
      
      // パフォーマンス基準
      if (query.start === 'A' && query.end === 'Z') {
        // 全シャードクエリは500ms以内
        expect(queryTime).toBeLessThan(500);
      } else {
        // 部分クエリは200ms以内
        expect(queryTime).toBeLessThan(200);
      }
      
      // クエリプランの確認
      const plan = await partitionManager.explainQuery(query);
      console.log(`Query ${query.start}-${query.end}:`, plan);
      
      // 必要なシャードのみアクセスしているか
      const expectedShards = getExpectedShards(query.start, query.end);
      expect(plan.accessedShards).toEqual(expectedShards);
    }
  });

  it('should perform distributed joins', async () => {
    // ユーザーと注文データの準備
    await partitionManager.createTable('orders', {
      partitionKey: 'user_id',
      schema: { order_id: 'string', user_id: 'string', amount: 'number' }
    });
    
    // テストデータ挿入
    const orders = generateTestOrders(5000);
    await Promise.all(
      orders.map(order => partitionManager.insert('orders', order))
    );
    
    // 分散JOINクエリ
    const joinQuery = {
      from: 'users',
      join: {
        table: 'orders',
        on: 'users.id = orders.user_id'
      },
      where: {
        'orders.amount': { $gt: 100 }
      },
      groupBy: 'users.region',
      select: ['users.region', 'COUNT(*) as order_count', 'SUM(orders.amount) as total']
    };
    
    const startTime = Date.now();
    const results = await partitionManager.executeJoin(joinQuery);
    const joinTime = Date.now() - startTime;
    
    console.log('Distributed join results:', results);
    console.log(`Join execution time: ${joinTime}ms`);
    
    // 結果の検証
    expect(results).toHaveLength(4); // 4リージョン
    results.forEach(row => {
      expect(row.order_count).toBeGreaterThan(0);
      expect(row.total).toBeGreaterThan(0);
    });
    
    // パフォーマンス基準（1秒以内）
    expect(joinTime).toBeLessThan(1000);
  });

  it('should handle shard failures with replicas', async () => {
    // レプリケーション設定の確認
    const replicationStatus = await partitionManager.getReplicationStatus();
    
    expect(replicationStatus.factor).toBe(2);
    expect(replicationStatus.healthy).toBe(true);
    
    // シャード1を停止
    await shards[0].stop();
    
    // データアクセスが継続できるか確認
    const testQueries = [
      { id: 'alice123' },  // シャード1のデータ
      { id: 'bob456' },    // シャード1のデータ
      { id: 'charlie789' } // シャード1のデータ
    ];
    
    for (const query of testQueries) {
      const result = await partitionManager.get('users', query.id);
      
      expect(result).toBeDefined();
      expect(result.id).toBe(query.id);
      
      // レプリカから読み取られたことを確認
      const queryLog = await partitionManager.getLastQueryLog();
      expect(queryLog.source).toContain('replica');
    }
    
    // 書き込みもレプリカに切り替わるか
    const writeResult = await partitionManager.update(
      'users',
      'alice123',
      { lastActive: new Date() }
    );
    
    expect(writeResult.success).toBe(true);
    expect(writeResult.promotedReplica).toBe(true);
  });

  it('should perform online resharding', async () => {
    // 現在の分散状況
    const beforeDistribution = await partitionManager.getDistribution('users');
    
    // ホットシャードを検出
    const hotShard = detectHotShard(beforeDistribution);
    console.log('Hot shard detected:', hotShard);
    
    // オンラインリシャーディング開始
    const reshardingPlan = {
      splitShard: hotShard.id,
      newShards: [
        { id: 'shard-1a', range: 'A-C' },
        { id: 'shard-1b', range: 'D-F' }
      ]
    };
    
    const resharding = await partitionManager.startResharding(reshardingPlan);
    
    // リシャーディング中も読み書き可能
    const concurrentOps = [];
    
    // 読み取りテスト
    for (let i = 0; i < 100; i++) {
      concurrentOps.push(
        partitionManager.get('users', `user${i}`)
          .then(result => ({ type: 'read', success: result !== null }))
      );
    }
    
    // 書き込みテスト
    for (let i = 0; i < 50; i++) {
      concurrentOps.push(
        partitionManager.insert('users', { id: `newuser${i}`, name: `New User ${i}` })
          .then(() => ({ type: 'write', success: true }))
          .catch(() => ({ type: 'write', success: false }))
      );
    }
    
    const opResults = await Promise.all(concurrentOps);
    
    // 95%以上の操作が成功
    const successRate = opResults.filter(r => r.success).length / opResults.length;
    expect(successRate).toBeGreaterThan(0.95);
    
    // リシャーディング完了を待つ
    await resharding.waitForCompletion();
    
    // 新しい分散を確認
    const afterDistribution = await partitionManager.getDistribution('users');
    console.log('After resharding:', afterDistribution);
    
    // より均等な分散になっているか
    const afterStdDev = calculateStandardDeviation(Object.values(afterDistribution));
    const beforeStdDev = calculateStandardDeviation(Object.values(beforeDistribution));
    
    expect(afterStdDev).toBeLessThan(beforeStdDev);
  });

  it('should optimize for data locality', async () => {
    // 地理的に分散したデータアクセスパターン
    const accessPatterns = [
      { region: 'us-east', users: ['alice', 'bob', 'charlie'] },
      { region: 'eu-west', users: ['david', 'emma', 'frank'] },
      { region: 'asia-pac', users: ['george', 'helen', 'ivan'] }
    ];
    
    // データローカリティ最適化を有効化
    await partitionManager.enableLocalityOptimization({
      strategy: 'geographic',
      rebalanceThreshold: 0.8
    });
    
    // アクセスパターンをシミュレート
    const accessMetrics = [];
    
    for (const pattern of accessPatterns) {
      const metrics = await simulateRegionalAccess(
        partitionManager,
        pattern.region,
        pattern.users,
        1000 // 1000リクエスト
      );
      
      accessMetrics.push(metrics);
    }
    
    // データが適切なリージョンに移動したか確認
    await new Promise(resolve => setTimeout(resolve, 5000)); // 再配置を待つ
    
    const localityStats = await partitionManager.getLocalityStats();
    
    console.log('Locality optimization results:', localityStats);
    
    // 各リージョンのローカルヒット率が向上
    accessMetrics.forEach((metrics, index) => {
      const region = accessPatterns[index].region;
      const hitRate = localityStats[region].localHitRate;
      
      expect(hitRate).toBeGreaterThan(0.8); // 80%以上のローカルヒット
    });
  });

  it('should handle composite partitioning', async () => {
    // 複合パーティション戦略（地理×時間）
    const compositeManager = new PartitionManager({
      shards,
      strategy: 'composite',
      dimensions: [
        { field: 'region', type: 'hash' },
        { field: 'timestamp', type: 'range', interval: 'month' }
      ]
    });
    
    // 時系列データの挿入
    const timeSeriesData = generateTimeSeriesData({
      regions: ['us', 'eu', 'asia'],
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      recordsPerDay: 1000
    });
    
    await compositeManager.bulkInsert('events', timeSeriesData);
    
    // 複合クエリのテスト
    const queries = [
      {
        region: 'us',
        timeRange: { start: '2024-03-01', end: '2024-03-31' }
      },
      {
        region: 'all',
        timeRange: { start: '2024-06-15', end: '2024-06-15' }
      }
    ];
    
    for (const query of queries) {
      const results = await compositeManager.timeRangeQuery(
        'events',
        query.region,
        query.timeRange
      );
      
      // 正しいパーティションがアクセスされたか
      const accessedPartitions = await compositeManager.getAccessedPartitions();
      
      if (query.region === 'all') {
        // 全リージョンだが特定の時間範囲のみ
        expect(accessedPartitions.length).toBeLessThanOrEqual(3);
      } else {
        // 特定リージョンの特定時間
        expect(accessedPartitions.length).toBe(1);
      }
    }
  });
});

// グローバルセカンダリインデックスのテスト
describe('Global Secondary Index', () => {
  it('should maintain distributed secondary indexes', async () => {
    // emailによるグローバルインデックス
    await partitionManager.createGlobalIndex('users', 'email', {
      unique: true,
      sparse: false
    });
    
    // インデックスを使用したクエリ
    const email = 'alice@example.com';
    const startTime = Date.now();
    
    const user = await partitionManager.findByIndex('users', 'email', email);
    
    const queryTime = Date.now() - startTime;
    
    expect(user).toBeDefined();
    expect(user.email).toBe(email);
    expect(queryTime).toBeLessThan(50); // インデックス使用で高速
    
    // インデックスの一貫性チェック
    const indexStats = await partitionManager.getIndexStats('users', 'email');
    
    expect(indexStats.totalEntries).toBe(10000);
    expect(indexStats.uniqueViolations).toBe(0);
    expect(indexStats.distribution).toBeDefined();
  });
});
```

### Green Phase (データパーティショニング実装)
```javascript
// partition-manager.js
const { ConsistentHashRing } = require('./consistent-hash');
const { Pool } = require('pg');

class PartitionManager {
  constructor(config) {
    this.config = config;
    this.shards = new Map();
    this.strategy = config.strategy || 'range-based';
    this.replicationFactor = config.replicationFactor || 1;
    
    // シャードの初期化
    this.initializeShards(config.shards);
    
    // パーティション戦略の設定
    this.partitioner = this.createPartitioner();
    
    // グローバルインデックス
    this.globalIndexes = new Map();
    
    // メトリクス収集
    this.metrics = new MetricsCollector();
  }
  
  initializeShards(shardConfigs) {
    for (const config of shardConfigs) {
      const shard = new Shard(config);
      this.shards.set(config.id, shard);
      
      // レプリカの設定
      if (this.replicationFactor > 1) {
        this.setupReplication(shard);
      }
    }
  }
  
  createPartitioner() {
    switch (this.strategy) {
      case 'range-based':
        return new RangePartitioner(this.shards);
      case 'hash-based':
        return new HashPartitioner(this.shards);
      case 'geographic':
        return new GeographicPartitioner(this.shards);
      case 'composite':
        return new CompositePartitioner(this.config.dimensions, this.shards);
      default:
        throw new Error(`Unknown partitioning strategy: ${this.strategy}`);
    }
  }
  
  async insert(table, data) {
    const shard = this.partitioner.getShardForData(table, data);
    
    try {
      // プライマリに書き込み
      const result = await shard.insert(table, data);
      
      // レプリケーション
      if (this.replicationFactor > 1) {
        await this.replicateWrite(shard, 'insert', table, data);
      }
      
      // グローバルインデックスの更新
      await this.updateGlobalIndexes(table, data, 'insert');
      
      // メトリクス記録
      this.metrics.recordWrite(shard.id, table);
      
      return result;
    } catch (error) {
      console.error(`Insert failed on shard ${shard.id}:`, error);
      throw error;
    }
  }
  
  async rangeQuery(table, query) {
    // 影響を受けるシャードを特定
    const targetShards = this.partitioner.getShardsForQuery(table, query);
    
    console.log(`Range query will access shards: ${targetShards.map(s => s.id).join(', ')}`);
    
    // 並列クエリ実行
    const shardQueries = targetShards.map(shard => 
      this.executeShardQuery(shard, table, query)
    );
    
    const results = await Promise.all(shardQueries);
    
    // 結果のマージとソート
    const mergedResults = this.mergeResults(results, query);
    
    return mergedResults;
  }
  
  async executeJoin(joinQuery) {
    // 分散JOINの実行計画
    const plan = this.createDistributedJoinPlan(joinQuery);
    
    console.log('Distributed join plan:', plan);
    
    if (plan.type === 'broadcast') {
      return this.executeBroadcastJoin(plan);
    } else if (plan.type === 'shuffle') {
      return this.executeShuffleJoin(plan);
    } else {
      return this.executeColocatedJoin(plan);
    }
  }
  
  async executeBroadcastJoin(plan) {
    // 小さいテーブルを各シャードにブロードキャスト
    const smallTable = await this.getAllData(plan.broadcastTable);
    
    // 各シャードでローカルJOIN
    const shardResults = await Promise.all(
      Array.from(this.shards.values()).map(shard =>
        shard.executeLocalJoin(plan.mainTable, smallTable, plan.joinCondition)
      )
    );
    
    // 結果の集約
    return this.aggregateJoinResults(shardResults, plan);
  }
  
  async executeShuffleJoin(plan) {
    // データの再分散が必要な場合
    const shuffleKey = plan.joinKey;
    
    // 一時的なシャッフル
    const shuffledData = await this.shuffleData(
      plan.leftTable,
      plan.rightTable,
      shuffleKey
    );
    
    // 各シャードでローカルJOIN
    const joinResults = await Promise.all(
      shuffledData.map(({ shard, leftData, rightData }) =>
        shard.executeLocalJoin(leftData, rightData, plan.joinCondition)
      )
    );
    
    return this.mergeResults(joinResults);
  }
  
  async startResharding(plan) {
    const resharding = new ReshardingOperation(plan);
    
    // Phase 1: 新しいシャードの準備
    await resharding.prepareNewShards();
    
    // Phase 2: 二重書き込み開始
    this.enableDoubleWrite(plan.splitShard, plan.newShards);
    
    // Phase 3: データのコピー
    resharding.startDataCopy();
    
    // Phase 4: カットオーバー
    resharding.onComplete(() => {
      this.switchToNewShards(plan);
      this.disableDoubleWrite(plan.splitShard);
    });
    
    return resharding;
  }
  
  async createGlobalIndex(table, field, options = {}) {
    const index = new GlobalSecondaryIndex({
      table,
      field,
      ...options,
      shards: this.shards
    });
    
    // 既存データのインデックス構築
    await index.buildFromExistingData();
    
    this.globalIndexes.set(`${table}.${field}`, index);
    
    return index;
  }
  
  async findByIndex(table, field, value) {
    const indexKey = `${table}.${field}`;
    const index = this.globalIndexes.get(indexKey);
    
    if (!index) {
      throw new Error(`No index found for ${indexKey}`);
    }
    
    // インデックスからシャード情報を取得
    const location = await index.lookup(value);
    
    if (!location) {
      return null;
    }
    
    // 該当シャードから直接取得
    const shard = this.shards.get(location.shardId);
    return shard.getByKey(table, location.primaryKey);
  }
  
  async getDistribution(table) {
    const distribution = {};
    
    for (const [shardId, shard] of this.shards) {
      const count = await shard.count(table);
      distribution[shardId] = count;
    }
    
    return distribution;
  }
  
  setupReplication(primaryShard) {
    const replicaShards = this.selectReplicaShards(primaryShard);
    
    primaryShard.replicas = replicaShards;
    
    // レプリケーションストリームの設定
    primaryShard.on('write', async (operation) => {
      await this.replicateToReplicas(primaryShard, operation);
    });
  }
  
  selectReplicaShards(primaryShard) {
    // 異なる物理ノードからレプリカを選択
    const candidates = Array.from(this.shards.values())
      .filter(s => s.id !== primaryShard.id && s.node !== primaryShard.node);
    
    return candidates.slice(0, this.replicationFactor - 1);
  }
  
  async replicateWrite(primaryShard, operation, table, data) {
    const replicationPromises = primaryShard.replicas.map(replica =>
      replica[operation](table, data)
        .catch(err => {
          console.error(`Replication to ${replica.id} failed:`, err);
          return { error: err };
        })
    );
    
    const results = await Promise.all(replicationPromises);
    
    // 成功したレプリカ数を確認
    const successCount = results.filter(r => !r.error).length;
    const requiredReplicas = Math.floor(this.replicationFactor / 2);
    
    if (successCount < requiredReplicas) {
      throw new Error('Insufficient replicas for write operation');
    }
  }
}

// シャード実装
class Shard {
  constructor(config) {
    this.id = config.id;
    this.range = config.range;
    this.pool = new Pool({
      host: config.host || 'localhost',
      port: config.port,
      database: config.database || `shard_${config.id}`,
      max: 20
    });
    
    this.replicas = [];
    this.metrics = new ShardMetrics();
  }
  
  async insert(table, data) {
    const keys = Object.keys(data);
    const values = Object.values(data);
    const placeholders = keys.map((_, i) => `$${i + 1}`).join(', ');
    
    const query = `INSERT INTO ${table} (${keys.join(', ')}) VALUES (${placeholders}) RETURNING *`;
    
    const result = await this.pool.query(query, values);
    this.metrics.recordInsert();
    
    return result.rows[0];
  }
  
  async executeQuery(table, conditions) {
    const { whereClause, values } = this.buildWhereClause(conditions);
    const query = `SELECT * FROM ${table} ${whereClause}`;
    
    const result = await this.pool.query(query, values);
    this.metrics.recordQuery();
    
    return result.rows;
  }
  
  async executeLocalJoin(leftData, rightData, joinCondition) {
    // メモリ内でのハッシュJOIN実装
    const hashTable = new Map();
    
    // Build phase
    for (const row of rightData) {
      const key = row[joinCondition.rightKey];
      if (!hashTable.has(key)) {
        hashTable.set(key, []);
      }
      hashTable.get(key).push(row);
    }
    
    // Probe phase
    const results = [];
    for (const leftRow of leftData) {
      const key = leftRow[joinCondition.leftKey];
      const rightRows = hashTable.get(key) || [];
      
      for (const rightRow of rightRows) {
        results.push({ ...leftRow, ...rightRow });
      }
    }
    
    return results;
  }
  
  async count(table) {
    const result = await this.pool.query(`SELECT COUNT(*) FROM ${table}`);
    return parseInt(result.rows[0].count);
  }
  
  buildWhereClause(conditions) {
    const clauses = [];
    const values = [];
    let paramCount = 1;
    
    for (const [field, condition] of Object.entries(conditions.where || {})) {
      if (typeof condition === 'object') {
        for (const [op, value] of Object.entries(condition)) {
          switch (op) {
            case '$gte':
              clauses.push(`${field} >= $${paramCount++}`);
              values.push(value);
              break;
            case '$lte':
              clauses.push(`${field} <= $${paramCount++}`);
              values.push(value);
              break;
            case '$gt':
              clauses.push(`${field} > $${paramCount++}`);
              values.push(value);
              break;
            // 他の演算子...
          }
        }
      } else {
        clauses.push(`${field} = $${paramCount++}`);
        values.push(condition);
      }
    }
    
    const whereClause = clauses.length > 0 ? `WHERE ${clauses.join(' AND ')}` : '';
    
    return { whereClause, values };
  }
}

// パーティショナー実装
class RangePartitioner {
  constructor(shards) {
    this.shards = shards;
    this.ranges = this.buildRangeMap();
  }
  
  buildRangeMap() {
    const ranges = [];
    
    for (const [id, shard] of this.shards) {
      const [start, end] = shard.range.split('-');
      ranges.push({
        shardId: id,
        shard,
        start,
        end
      });
    }
    
    // ソート
    ranges.sort((a, b) => a.start.localeCompare(b.start));
    
    return ranges;
  }
  
  getShardForData(table, data) {
    const partitionKey = this.getPartitionKey(table, data);
    
    for (const range of this.ranges) {
      if (partitionKey >= range.start && partitionKey <= range.end) {
        return range.shard;
      }
    }
    
    throw new Error(`No shard found for partition key: ${partitionKey}`);
  }
  
  getShardsForQuery(table, query) {
    const affectedShards = [];
    
    // クエリ条件から影響を受ける範囲を特定
    const queryRange = this.extractQueryRange(query);
    
    for (const range of this.ranges) {
      if (this.rangesOverlap(queryRange, range)) {
        affectedShards.push(range.shard);
      }
    }
    
    return affectedShards;
  }
  
  getPartitionKey(table, data) {
    // テーブルごとのパーティションキー設定
    const keyField = this.getKeyField(table);
    return data[keyField]?.[0]?.toUpperCase() || 'A';
  }
  
  getKeyField(table) {
    const keyFields = {
      users: 'name',
      orders: 'user_id',
      events: 'event_id'
    };
    
    return keyFields[table] || 'id';
  }
  
  extractQueryRange(query) {
    // WHERE句から範囲を抽出
    if (query.where?.name) {
      const condition = query.where.name;
      return {
        start: condition.$gte?.[0]?.toUpperCase() || 'A',
        end: condition.$lte?.[0]?.toUpperCase() || 'Z'
      };
    }
    
    return { start: 'A', end: 'Z' };
  }
  
  rangesOverlap(range1, range2) {
    return range1.start <= range2.end && range1.end >= range2.start;
  }
}

// グローバルセカンダリインデックス
class GlobalSecondaryIndex {
  constructor(config) {
    this.table = config.table;
    this.field = config.field;
    this.unique = config.unique || false;
    this.sparse = config.sparse || false;
    this.shards = config.shards;
    
    // インデックスデータの分散
    this.indexShards = new ConsistentHashRing({
      servers: Array.from(this.shards.values()).map(s => ({
        id: s.id,
        host: `${s.id}-index`
      }))
    });
  }
  
  async buildFromExistingData() {
    console.log(`Building global index for ${this.table}.${this.field}`);
    
    const buildPromises = [];
    
    for (const shard of this.shards.values()) {
      buildPromises.push(this.buildShardIndex(shard));
    }
    
    await Promise.all(buildPromises);
    
    console.log('Global index build complete');
  }
  
  async buildShardIndex(shard) {
    const batchSize = 1000;
    let offset = 0;
    
    while (true) {
      const batch = await shard.query(
        `SELECT id, ${this.field} FROM ${this.table} LIMIT ${batchSize} OFFSET ${offset}`
      );
      
      if (batch.length === 0) break;
      
      // インデックスエントリの作成
      for (const row of batch) {
        await this.addToIndex(row.id, row[this.field], shard.id);
      }
      
      offset += batchSize;
    }
  }
  
  async addToIndex(primaryKey, indexValue, shardId) {
    if (this.sparse && !indexValue) {
      return; // スパースインデックスはnull値をスキップ
    }
    
    const indexShard = this.indexShards.getNode(indexValue);
    
    const entry = {
      indexValue,
      primaryKey,
      shardId,
      timestamp: Date.now()
    };
    
    if (this.unique) {
      // ユニーク制約のチェック
      const existing = await this.lookup(indexValue);
      if (existing) {
        throw new Error(`Unique constraint violation for ${this.field}: ${indexValue}`);
      }
    }
    
    // インデックスエントリの保存
    await indexShard.insert(`${this.table}_${this.field}_idx`, entry);
  }
  
  async lookup(value) {
    const indexShard = this.indexShards.getNode(value);
    
    const result = await indexShard.query(
      `SELECT * FROM ${this.table}_${this.field}_idx WHERE indexValue = $1`,
      [value]
    );
    
    return result[0] || null;
  }
}

// リシャーディング操作
class ReshardingOperation extends EventEmitter {
  constructor(plan) {
    super();
    this.plan = plan;
    this.progress = 0;
    this.state = 'preparing';
  }
  
  async prepareNewShards() {
    this.state = 'preparing';
    
    // 新しいシャードの作成と初期化
    for (const shardConfig of this.plan.newShards) {
      await this.createNewShard(shardConfig);
    }
    
    this.state = 'copying';
  }
  
  async startDataCopy() {
    const sourceShardId = this.plan.splitShard;
    const totalRows = await this.countSourceRows(sourceShardId);
    
    let copiedRows = 0;
    const batchSize = 10000;
    
    // バッチコピー
    while (copiedRows < totalRows) {
      const batch = await this.copyBatch(sourceShardId, copiedRows, batchSize);
      
      // 新しいシャードに分配
      await this.distributeBatch(batch);
      
      copiedRows += batch.length;
      this.progress = (copiedRows / totalRows) * 100;
      
      this.emit('progress', {
        progress: this.progress,
        copiedRows,
        totalRows
      });
    }
    
    this.state = 'finalizing';
    this.finalize();
  }
  
  async finalize() {
    // 最終的な一貫性チェック
    await this.verifyDataIntegrity();
    
    this.state = 'completed';
    this.emit('complete');
  }
  
  async waitForCompletion() {
    return new Promise((resolve) => {
      this.once('complete', resolve);
    });
  }
}

module.exports = {
  PartitionManager,
  Shard,
  RangePartitioner,
  GlobalSecondaryIndex,
  ReshardingOperation
};
```

### Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  # シャード1
  shard1:
    image: postgres:15
    environment:
      POSTGRES_DB: shard1
      POSTGRES_USER: shard_user
      POSTGRES_PASSWORD: shard_pass
    ports:
      - "5001:5432"
    volumes:
      - shard1-data:/var/lib/postgresql/data
      - ./init-scripts/shard1.sql:/docker-entrypoint-initdb.d/init.sql

  # シャード2
  shard2:
    image: postgres:15
    environment:
      POSTGRES_DB: shard2
      POSTGRES_USER: shard_user
      POSTGRES_PASSWORD: shard_pass
    ports:
      - "5002:5432"
    volumes:
      - shard2-data:/var/lib/postgresql/data
      - ./init-scripts/shard2.sql:/docker-entrypoint-initdb.d/init.sql

  # シャード3
  shard3:
    image: postgres:15
    environment:
      POSTGRES_DB: shard3
      POSTGRES_USER: shard_user
      POSTGRES_PASSWORD: shard_pass
    ports:
      - "5003:5432"
    volumes:
      - shard3-data:/var/lib/postgresql/data
      - ./init-scripts/shard3.sql:/docker-entrypoint-initdb.d/init.sql

  # シャード4
  shard4:
    image: postgres:15
    environment:
      POSTGRES_DB: shard4
      POSTGRES_USER: shard_user
      POSTGRES_PASSWORD: shard_pass
    ports:
      - "5004:5432"
    volumes:
      - shard4-data:/var/lib/postgresql/data
      - ./init-scripts/shard4.sql:/docker-entrypoint-initdb.d/init.sql

  # パーティションマネージャー
  partition-manager:
    build: .
    ports:
      - "8080:8080"
    environment:
      SHARDS: "shard1:5001,shard2:5002,shard3:5003,shard4:5004"
      PARTITION_STRATEGY: range-based
      REPLICATION_FACTOR: 2
    depends_on:
      - shard1
      - shard2
      - shard3
      - shard4

  # モニタリング
  shard-monitor:
    build:
      context: .
      dockerfile: Dockerfile.monitor
    ports:
      - "9000:9000"
    environment:
      PARTITION_MANAGER_URL: http://partition-manager:8080

volumes:
  shard1-data:
  shard2-data:
  shard3-data:
  shard4-data:
```

## 実行と検証

### 1. システム起動
```bash
docker-compose up -d

# シャードの健全性確認
./scripts/check-shard-health.sh
```

### 2. データ分散テスト
```bash
# テストデータの投入
npm run test:load-data -- --records=100000

# 分散状況の確認
curl http://localhost:8080/api/distribution | jq
```

### 3. パフォーマンステスト
```bash
# 範囲クエリ
npm run benchmark:range-queries

# 分散JOIN
npm run benchmark:distributed-joins

# グローバルインデックス
npm run benchmark:global-index
```

## 成功基準

- [ ] データの均等分散（偏差15%以内）
- [ ] 範囲クエリの効率的実行（200ms以内）
- [ ] 分散JOINの成功（1秒以内）
- [ ] オンラインリシャーディング（95%可用性）
- [ ] グローバルインデックスの高速検索（50ms以内）

## 運用ガイド

### リシャーディング手順
```bash
# ホットシャードの検出
curl http://localhost:8080/api/hotspots

# リシャーディング計画の作成
curl -X POST http://localhost:8080/api/resharding/plan \
  -d '{"targetShard": "shard1", "splitInto": 2}'

# 実行
curl -X POST http://localhost:8080/api/resharding/execute
```

### データマイグレーション
```bash
# バックアップ
./scripts/backup-shard.sh shard1

# マイグレーション
./scripts/migrate-data.sh --from shard1 --to shard1a,shard1b
```

## トラブルシューティング

### 問題: データスキュー
```bash
# スキューの分析
curl http://localhost:8080/api/analyze/skew

# 再バランシング
curl -X POST http://localhost:8080/api/rebalance
```

### 問題: クロスシャードクエリの遅延
```bash
# クエリプランの確認
curl -X POST http://localhost:8080/api/explain \
  -d '{"query": "..."}'

# 統計情報の更新
curl -X POST http://localhost:8080/api/analyze
```

## 次のステップ

データパーティショニングを確立後、`16_container_orchestration_k8s`でKubernetesによるコンテナオーケストレーションを実装します。

## 学んだこと

- 効果的なデータ分散戦略
- 分散クエリの最適化
- グローバルインデックスの威力
- オンラインリシャーディングの複雑さ

## 参考資料

- [Database Sharding Explained](https://www.mongodb.com/features/database-sharding-explained)
- [Vitess Architecture](https://vitess.io/docs/concepts/architecture/)
- [Amazon DynamoDB Global Tables](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html)
- [Google Spanner Paper](https://research.google/pubs/pub39966/)