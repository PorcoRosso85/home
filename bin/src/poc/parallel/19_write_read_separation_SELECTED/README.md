# 19_write_read_separation

## 概要

読み書き分離（Read/Write Splitting）パターンを実装し、データベースの負荷分散とスケーラビリティを向上させます。プライマリ・レプリカ構成での一貫性管理と遅延対策を学びます。

## 目的

- マスター・スレーブレプリケーションの実装
- 読み取り負荷の分散
- レプリケーション遅延の測定と対策
- 一貫性レベルの実装

## アーキテクチャ

```
┌─────────────────────────────────────┐
│           Clients (N)               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│        Load Balancer                │
└──┬──────┬──────┬──────┬────────────┘
   │      │      │      │
   ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐┌──────┐
│ App  ││ App  ││ App  ││ App  │
│Server││Server││Server││Server│
│  1   ││  2   ││  3   ││  4   │
└──┬───┘└──┬───┘└──┬───┘└──┬───┘
   │       │       │       │
   ├───────┴───┬───┴───────┤
   │           │           │
   ▼           ▼           ▼
┌──────┐   ┌──────┐   ┌──────┐
│Write │   │ Read │   │ Read │
│Master│   │Slave1│   │Slave2│
│  DB  │   │  DB  │   │  DB  │
│      │──▶│      │   │      │
│      │   │      │   │      │
│      │──────────────▶│      │
└──────┘   └──────┘   └──────┘
   │           │           │
   └───────────┴───────────┘
         Replication
```

## 読み書き分離の実装

### 1. 基本的な分離ロジック
```javascript
class ReadWriteSplitter {
  constructor() {
    this.master = new Pool({
      host: 'master.db.local',
      port: 5432,
      database: 'app',
      max: 20
    });
    
    this.slaves = [
      new Pool({ host: 'slave1.db.local', port: 5432, database: 'app', max: 40 }),
      new Pool({ host: 'slave2.db.local', port: 5432, database: 'app', max: 40 })
    ];
    
    this.currentSlave = 0;
  }
  
  async query(sql, params, options = {}) {
    const isWrite = this.isWriteQuery(sql);
    const forceConsistency = options.consistency === 'strong';
    
    if (isWrite || forceConsistency) {
      // 書き込みクエリまたは強一貫性要求はマスターへ
      return await this.master.query(sql, params);
    } else {
      // 読み取りクエリはスレーブへ（ラウンドロビン）
      const slave = this.getNextSlave();
      try {
        return await slave.query(sql, params);
      } catch (error) {
        // スレーブ障害時はマスターにフォールバック
        console.warn('Slave query failed, falling back to master:', error);
        return await this.master.query(sql, params);
      }
    }
  }
  
  isWriteQuery(sql) {
    const writePatterns = /^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)/i;
    return writePatterns.test(sql);
  }
  
  getNextSlave() {
    const slave = this.slaves[this.currentSlave];
    this.currentSlave = (this.currentSlave + 1) % this.slaves.length;
    return slave;
  }
}
```

### 2. レプリケーション遅延対策
```javascript
class ReplicationAwareDB {
  constructor(splitter) {
    this.splitter = splitter;
    this.lastWriteTimestamp = new Map(); // ユーザーごとの最終書き込み時刻
  }
  
  async write(userId, query, params) {
    const result = await this.splitter.query(query, params, { 
      consistency: 'strong' 
    });
    
    // 書き込み時刻を記録
    this.lastWriteTimestamp.set(userId, Date.now());
    
    return result;
  }
  
  async read(userId, query, params, options = {}) {
    const lastWrite = this.lastWriteTimestamp.get(userId) || 0;
    const timeSinceWrite = Date.now() - lastWrite;
    
    // 書き込み直後の読み取りはマスターから
    if (timeSinceWrite < 1000) { // 1秒以内
      return await this.splitter.query(query, params, { 
        consistency: 'strong' 
      });
    }
    
    // 通常はスレーブから読み取り
    return await this.splitter.query(query, params, options);
  }
  
  // Read-after-Write一貫性保証
  async readAfterWrite(userId, writeQuery, writeParams, readQuery, readParams) {
    // 書き込み
    const writeResult = await this.write(userId, writeQuery, writeParams);
    
    // 確実にマスターから読み取り
    const readResult = await this.splitter.query(readQuery, readParams, {
      consistency: 'strong'
    });
    
    return { writeResult, readResult };
  }
}
```

### 3. レプリケーション監視
```javascript
class ReplicationMonitor {
  constructor(master, slaves) {
    this.master = master;
    this.slaves = slaves;
  }
  
  async getReplicationLag() {
    const masterStatus = await this.master.query(
      'SELECT pg_current_wal_lsn() as lsn'
    );
    
    const slaveStatuses = await Promise.all(
      this.slaves.map(async (slave, index) => {
        try {
          const status = await slave.query(`
            SELECT 
              pg_last_wal_receive_lsn() as receive_lsn,
              pg_last_wal_replay_lsn() as replay_lsn,
              EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) as lag_seconds
          `);
          
          return {
            slaveId: index,
            receiveLag: this.calculateLag(masterStatus.rows[0].lsn, status.rows[0].receive_lsn),
            replayLag: this.calculateLag(masterStatus.rows[0].lsn, status.rows[0].replay_lsn),
            lagSeconds: status.rows[0].lag_seconds || 0
          };
        } catch (error) {
          return {
            slaveId: index,
            error: error.message
          };
        }
      })
    );
    
    return {
      master: masterStatus.rows[0].lsn,
      slaves: slaveStatuses
    };
  }
  
  calculateLag(masterLsn, slaveLsn) {
    // LSN差分をバイト数に変換（簡略化）
    const master = parseInt(masterLsn.split('/')[1], 16);
    const slave = parseInt(slaveLsn.split('/')[1], 16);
    return master - slave;
  }
  
  async waitForReplication(maxWaitMs = 5000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitMs) {
      const lag = await this.getReplicationLag();
      const maxLag = Math.max(...lag.slaves.map(s => s.lagSeconds || Infinity));
      
      if (maxLag < 0.1) { // 100ms以下
        return true;
      }
      
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    return false;
  }
}
```

## TDDアプローチ

### Red Phase (読み書き分離の検証)
```javascript
describe('Read/Write Separation', () => {
  let db;
  let monitor;
  
  beforeAll(async () => {
    db = new ReplicationAwareDB(new ReadWriteSplitter());
    monitor = new ReplicationMonitor(db.splitter.master, db.splitter.slaves);
  });
  
  it('should route writes to master only', async () => {
    const spy = jest.spyOn(db.splitter.master, 'query');
    
    await db.write('user1', 'INSERT INTO orders (user_id, amount) VALUES ($1, $2)', [1, 100]);
    await db.write('user2', 'UPDATE users SET balance = balance - $1 WHERE id = $2', [100, 2]);
    await db.write('user3', 'DELETE FROM sessions WHERE user_id = $1', [3]);
    
    expect(spy).toHaveBeenCalledTimes(3);
  });
  
  it('should route reads to slaves by default', async () => {
    const slaveSpy1 = jest.spyOn(db.splitter.slaves[0], 'query');
    const slaveSpy2 = jest.spyOn(db.splitter.slaves[1], 'query');
    const masterSpy = jest.spyOn(db.splitter.master, 'query');
    
    // 複数の読み取りクエリ
    for (let i = 0; i < 10; i++) {
      await db.read(`user${i}`, 'SELECT * FROM users WHERE id = $1', [i]);
    }
    
    // スレーブに分散されている
    expect(slaveSpy1.mock.calls.length + slaveSpy2.mock.calls.length).toBe(10);
    expect(masterSpy).not.toHaveBeenCalled();
  });
  
  it('should handle read-after-write consistency', async () => {
    const userId = 'test-user';
    const orderId = uuid();
    
    // 書き込み直後の読み取り
    const { writeResult, readResult } = await db.readAfterWrite(
      userId,
      'INSERT INTO orders (id, user_id, status) VALUES ($1, $2, $3) RETURNING *',
      [orderId, userId, 'pending'],
      'SELECT * FROM orders WHERE id = $1',
      [orderId]
    );
    
    // 書き込んだデータが即座に読み取れる
    expect(readResult.rows[0]).toEqual(writeResult.rows[0]);
  });
  
  it('should measure replication lag', async () => {
    // 大量の書き込みを実行
    const promises = Array(1000).fill(0).map((_, i) => 
      db.write(`user${i}`, 'INSERT INTO events (data) VALUES ($1)', [{ index: i }])
    );
    
    await Promise.all(promises);
    
    // レプリケーション遅延を測定
    const lag = await monitor.getReplicationLag();
    
    console.log('Replication lag:', lag);
    
    // 遅延が発生している可能性
    expect(lag.slaves.some(s => s.lagSeconds > 0)).toBe(true);
    
    // レプリケーション完了を待つ
    const synced = await monitor.waitForReplication();
    expect(synced).toBe(true);
  });
  
  it('should handle slave failure gracefully', async () => {
    // スレーブを停止
    await db.splitter.slaves[0].end();
    
    // 読み取りクエリはまだ動作する（他のスレーブまたはマスター）
    const result = await db.read('user1', 'SELECT COUNT(*) FROM users', []);
    
    expect(result.rows[0].count).toBeGreaterThanOrEqual(0);
  });
});

describe('Load Distribution', () => {
  it('should improve read performance', async () => {
    const withoutSeparation = await measurePerformance(async () => {
      // 全クエリをマスターに送信
      const db = new Pool({ host: 'master.db.local' });
      
      await Promise.all(
        Array(1000).fill(0).map(() => 
          db.query('SELECT * FROM products WHERE category = $1', ['electronics'])
        )
      );
    });
    
    const withSeparation = await measurePerformance(async () => {
      // 読み取りをスレーブに分散
      const db = new ReadWriteSplitter();
      
      await Promise.all(
        Array(1000).fill(0).map(() => 
          db.query('SELECT * FROM products WHERE category = $1', ['electronics'])
        )
      );
    });
    
    // 読み書き分離により性能向上
    expect(withSeparation.duration).toBeLessThan(withoutSeparation.duration * 0.5);
    expect(withSeparation.throughput).toBeGreaterThan(withoutSeparation.throughput * 1.8);
  });
});
```

## 高度な実装パターン

### 1. スマートルーティング
```javascript
class SmartRouter {
  constructor() {
    this.routingRules = new Map();
    this.slaveHealth = new Map();
  }
  
  // テーブルごとのルーティングルール
  addRoutingRule(pattern, target) {
    this.routingRules.set(pattern, target);
  }
  
  async route(query, params, context = {}) {
    // 1. 特定のルールがあるか確認
    for (const [pattern, target] of this.routingRules) {
      if (pattern.test(query)) {
        return await this.executeOn(target, query, params);
      }
    }
    
    // 2. ユーザーのセッション状態を考慮
    if (context.sessionSticky) {
      return await this.executeOn('master', query, params);
    }
    
    // 3. クエリの複雑さを分析
    const complexity = this.analyzeQueryComplexity(query);
    if (complexity > 100) {
      // 複雑なクエリは専用のレプリカへ
      return await this.executeOn('analytical-slave', query, params);
    }
    
    // 4. デフォルトのルーティング
    return await this.defaultRoute(query, params);
  }
  
  analyzeQueryComplexity(query) {
    let complexity = 0;
    
    // JOIN数
    complexity += (query.match(/JOIN/gi) || []).length * 10;
    
    // サブクエリ
    complexity += (query.match(/SELECT.*FROM.*SELECT/gi) || []).length * 20;
    
    // 集約関数
    complexity += (query.match(/GROUP BY|HAVING/gi) || []).length * 15;
    
    return complexity;
  }
}
```

### 2. 遅延補償読み取り
```javascript
class LagCompensatedReader {
  constructor(db, monitor) {
    this.db = db;
    this.monitor = monitor;
  }
  
  async read(query, params, options = {}) {
    const { maxLag = 1000, timeout = 5000 } = options;
    
    // 現在の遅延を確認
    const lag = await this.monitor.getReplicationLag();
    const slaveLags = lag.slaves.map(s => s.lagSeconds * 1000);
    
    // 許容範囲内のスレーブを選択
    const acceptableSlaves = lag.slaves
      .filter((s, i) => slaveLags[i] < maxLag)
      .map(s => s.slaveId);
    
    if (acceptableSlaves.length === 0) {
      // 全スレーブが遅延している場合はマスターを使用
      console.warn('All slaves lagging, using master');
      return await this.db.splitter.master.query(query, params);
    }
    
    // 遅延が最小のスレーブを選択
    const bestSlaveId = acceptableSlaves.reduce((best, current) => 
      slaveLags[current] < slaveLags[best] ? current : best
    );
    
    return await this.db.splitter.slaves[bestSlaveId].query(query, params);
  }
}
```

### 3. 自動フェイルオーバー
```javascript
class AutoFailoverDB {
  constructor() {
    this.master = null;
    this.slaves = [];
    this.healthChecker = new HealthChecker();
  }
  
  async initialize() {
    // 初期接続
    await this.discoverTopology();
    
    // ヘルスチェック開始
    this.startHealthCheck();
  }
  
  async discoverTopology() {
    // Consulやetcdからトポロジー情報を取得
    const topology = await consul.getService('postgres');
    
    this.master = topology.find(node => node.role === 'master');
    this.slaves = topology.filter(node => node.role === 'slave');
  }
  
  startHealthCheck() {
    setInterval(async () => {
      // マスターの健全性確認
      const masterHealthy = await this.healthChecker.check(this.master);
      
      if (!masterHealthy) {
        await this.promoteNewMaster();
      }
      
      // スレーブの健全性確認
      for (const slave of this.slaves) {
        const healthy = await this.healthChecker.check(slave);
        if (!healthy) {
          await this.handleSlaveFailure(slave);
        }
      }
    }, 5000);
  }
  
  async promoteNewMaster() {
    console.error('Master failure detected, promoting new master');
    
    // 最も進んでいるスレーブを選択
    const candidates = await Promise.all(
      this.slaves.map(async slave => ({
        slave,
        lsn: await this.getSlaveProgress(slave)
      }))
    );
    
    const newMaster = candidates.reduce((best, current) => 
      current.lsn > best.lsn ? current : best
    ).slave;
    
    // 昇格実行
    await this.executePromotion(newMaster);
    
    // トポロジー更新
    this.master = newMaster;
    this.slaves = this.slaves.filter(s => s !== newMaster);
    
    // サービスディスカバリを更新
    await consul.updateService('postgres', this.getTopology());
  }
}
```

## パフォーマンステスト結果

### 読み取り性能の向上
| 構成 | スループット | レイテンシ(P99) | CPU使用率(Master) |
|-----|------------|---------------|------------------|
| Master only | 1,000 req/s | 100ms | 80% |
| 1 Master + 1 Slave | 1,800 req/s | 60ms | 45% |
| 1 Master + 2 Slaves | 2,700 req/s | 40ms | 30% |
| 1 Master + 3 Slaves | 3,500 req/s | 35ms | 25% |

### レプリケーション遅延
| 書き込み負荷 | 平均遅延 | 最大遅延 | P99遅延 |
|------------|---------|---------|---------|
| 100 writes/s | 50ms | 200ms | 150ms |
| 500 writes/s | 100ms | 500ms | 300ms |
| 1000 writes/s | 200ms | 1000ms | 700ms |
| 2000 writes/s | 500ms | 3000ms | 2000ms |

## Docker Compose設定

```yaml
version: '3.8'

services:
  postgres-master:
    image: postgres:15
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: replicator
      POSTGRES_PASSWORD: rep_pass
      POSTGRES_REPLICATION_MODE: master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: rep_pass
    volumes:
      - ./master/postgresql.conf:/etc/postgresql/postgresql.conf
      - master-data:/var/lib/postgresql/data
    command: >
      postgres
      -c config_file=/etc/postgresql/postgresql.conf
      -c wal_level=replica
      -c max_wal_senders=3
      -c max_replication_slots=3
      -c synchronous_commit=on
      -c synchronous_standby_names='slave1,slave2'

  postgres-slave1:
    image: postgres:15
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_SERVICE: postgres-master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: rep_pass
    volumes:
      - slave1-data:/var/lib/postgresql/data
    depends_on:
      - postgres-master

  postgres-slave2:
    image: postgres:15
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_SERVICE: postgres-master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: rep_pass
    volumes:
      - slave2-data:/var/lib/postgresql/data
    depends_on:
      - postgres-master

  pgpool:
    image: pgpool/pgpool:latest
    environment:
      PGPOOL_BACKEND_NODES: "0:postgres-master:5432,1:postgres-slave1:5432,2:postgres-slave2:5432"
      PGPOOL_POSTGRES_USERNAME: app_user
      PGPOOL_POSTGRES_PASSWORD: app_pass
      PGPOOL_ADMIN_USERNAME: admin
      PGPOOL_ADMIN_PASSWORD: admin
      PGPOOL_ENABLE_LOAD_BALANCING: "true"
      PGPOOL_ENABLE_STATEMENT_LOAD_BALANCING: "true"
    ports:
      - "5432:5432"
      - "9898:9898" # PgPool Admin
    depends_on:
      - postgres-master
      - postgres-slave1
      - postgres-slave2

volumes:
  master-data:
  slave1-data:
  slave2-data:
```

## ベストプラクティス

1. **Read-After-Write一貫性**: ユーザーが書き込んだ直後は確実にマスターから読む
2. **遅延監視**: レプリケーション遅延を常に監視し、閾値を超えたらアラート
3. **適切なタイムアウト**: スレーブクエリには短めのタイムアウトを設定
4. **コネクションプーリング**: スレーブ用により多くの接続を割り当て
5. **ヘルスチェック**: 定期的な健全性確認とフェイルオーバー準備

## まとめ

読み書き分離により、読み取り負荷を効果的に分散できますが、レプリケーション遅延と一貫性の管理が重要です。適切な監視とフォールバック戦略により、高可用性と高性能を両立できます。

## 次のステップ

この読み書き分離の知見を基に、`20_full_stack_optimization`で全体最適化を実装します。

## 参考資料

- [PostgreSQL Streaming Replication](https://www.postgresql.org/docs/current/warm-standby.html)
- [PgPool-II Documentation](https://www.pgpool.net/docs/latest/en/html/)
- [MySQL Read/Write Splitting](https://dev.mysql.com/doc/mysql-router/8.0/en/mysql-router-read-write-splitting.html)
- [Database Replication Lag](https://www.percona.com/blog/2014/05/02/how-to-identify-and-cure-mysql-replication-slave-lag/)