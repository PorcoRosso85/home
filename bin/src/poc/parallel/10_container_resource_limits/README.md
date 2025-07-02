# 10_container_resource_limits

## 概要

単一サーバー内での複数コンテナ運用において、リソース制限の設定と競合管理を検証します。CPU、メモリ、I/Oの公平な分配と、リソース不足時の挙動を理解します。

## 目的

- リソース制限の効果と影響の測定
- ノイジーネイバー問題の実証と対策
- QoS（Quality of Service）の実装
- リソース枯渇時の優雅な劣化

## アーキテクチャ

```
┌─────────────────────────────────┐
│      Host Resources             │
│  CPU: 4 cores (400% total)      │
│  Memory: 8GB                    │
│  Disk I/O: 1000 IOPS            │
└─────────────────────────────────┘
         │
         ├──── Resource Allocation ────
         │
    ┌────┴────┬────────┬────────┬────────┐
    │         │        │        │        │
┌───▼───┐ ┌──▼───┐ ┌─▼────┐ ┌─▼────┐ ┌─▼────┐
│Priority│ │ Med  │ │ Low  │ │Burst │ │Best  │
│  High  │ │      │ │      │ │      │ │Effort│
│        │ │      │ │      │ │      │ │      │
│CPU: 2  │ │CPU: 1│ │CPU:.5│ │CPU: 1│ │CPU: -│
│Mem: 2G │ │Mem:1G│ │Mem:.5│ │Mem:1G│ │Mem:.5│
│IO: 500 │ │IO:300│ │IO:100│ │IO:200│ │IO: - │
└────────┘ └──────┘ └──────┘ └──────┘ └──────┘
    │         │        │        │        │
    └─────────┴────────┴────────┴────────┘
                    │
            [cgroups v2 Control]
```

## 検証項目

### 1. CPU制限と配分
- **CPU shares**: 相対的な優先度
- **CPU quota**: 絶対的な上限
- **CPU sets**: コア割り当て
- **スロットリング**: 制限超過時の挙動

### 2. メモリ管理
- **メモリ上限**: ハード/ソフトリミット
- **OOMキラー**: メモリ枯渇時の挙動
- **スワップ制御**: スワップ使用の制限
- **ページキャッシュ**: 共有と競合

### 3. I/O制御
- **帯域幅制限**: 読み書き速度の上限
- **IOPS制限**: 操作数の制限
- **優先度**: I/Oスケジューラー設定
- **デバイス別制御**: 特定デバイスの制限

### 4. ネットワーク帯域
- **帯域幅制限**: 送受信レート制限
- **パケット制限**: PPS（Packets Per Second）
- **TC（Traffic Control）**: 高度な制御
- **優先度キュー**: QoSの実装

## TDDアプローチ

### Red Phase (リソース制限の検証テスト)
```javascript
// test/resource-limits.test.js
describe('Container Resource Limits and Contention', () => {
  let containers;
  let monitor;
  
  beforeAll(async () => {
    containers = {
      highPriority: await createContainer('high-priority', {
        cpus: '2.0',
        memory: '2g',
        memorySwap: '2g',
        blkioWeight: 500,
        cpuShares: 1024
      }),
      medium: await createContainer('medium', {
        cpus: '1.0',
        memory: '1g',
        memorySwap: '1g',
        blkioWeight: 300,
        cpuShares: 512
      }),
      low: await createContainer('low', {
        cpus: '0.5',
        memory: '512m',
        memorySwap: '512m',
        blkioWeight: 100,
        cpuShares: 256
      }),
      burst: await createContainer('burst', {
        cpus: '1.0',
        memory: '1g',
        cpuBurst: true, // CPU burst許可
        cpuShares: 512
      }),
      bestEffort: await createContainer('best-effort', {
        // リソース制限なし（ベストエフォート）
        cpuShares: 128
      })
    };
    
    monitor = new ResourceMonitor(containers);
    await monitor.start();
  });

  it('should enforce CPU limits under contention', async () => {
    // 全コンテナでCPU集約的タスクを実行
    const tasks = Object.entries(containers).map(([name, container]) => 
      container.execute('stress-ng --cpu 4 --timeout 30s')
    );
    
    // 実行中のメトリクス収集
    const metrics = await monitor.collectDuring(30000, 1000);
    
    await Promise.all(tasks);
    
    // CPU使用率の分析
    const avgCpuUsage = calculateAverageCpuUsage(metrics);
    
    // 設定された制限に従っているか確認
    expect(avgCpuUsage.highPriority).toBeCloseTo(200, -1); // 200% ± 10%
    expect(avgCpuUsage.medium).toBeCloseTo(100, -1);       // 100% ± 10%
    expect(avgCpuUsage.low).toBeCloseTo(50, -1);           // 50% ± 10%
    
    // shares に基づく相対的な配分
    const totalCpu = Object.values(avgCpuUsage).reduce((a, b) => a + b, 0);
    const relativeUsage = {
      highPriority: avgCpuUsage.highPriority / totalCpu,
      medium: avgCpuUsage.medium / totalCpu,
      low: avgCpuUsage.low / totalCpu
    };
    
    // 高優先度コンテナがより多くのCPUを獲得
    expect(relativeUsage.highPriority).toBeGreaterThan(relativeUsage.medium);
    expect(relativeUsage.medium).toBeGreaterThan(relativeUsage.low);
  });

  it('should handle memory limits and OOM killer', async () => {
    const memoryTests = [
      {
        container: 'low',
        allocate: '600m', // 制限を超える
        expectedResult: 'oom_killed'
      },
      {
        container: 'medium',
        allocate: '900m', // 制限内
        expectedResult: 'success'
      },
      {
        container: 'highPriority',
        allocate: '1800m', // 制限内
        expectedResult: 'success'
      }
    ];
    
    for (const test of memoryTests) {
      console.log(`Testing memory allocation: ${test.container} - ${test.allocate}`);
      
      const result = await containers[test.container].execute(
        `stress-ng --vm 1 --vm-bytes ${test.allocate} --timeout 10s`
      );
      
      if (test.expectedResult === 'oom_killed') {
        expect(result.exitCode).not.toBe(0);
        
        // OOMイベントの確認
        const events = await getContainerEvents(test.container);
        const oomEvent = events.find(e => e.type === 'oom');
        expect(oomEvent).toBeDefined();
      } else {
        expect(result.exitCode).toBe(0);
      }
    }
  });

  it('should demonstrate noisy neighbor problem and mitigation', async () => {
    // ノイジーネイバーをシミュレート
    const noisyTask = containers.bestEffort.execute(
      'stress-ng --cpu 8 --io 4 --vm 2 --vm-bytes 1G --timeout 60s'
    );
    
    // 他のコンテナでレイテンシ感度の高いタスクを実行
    const latencySensitiveTasks = [];
    const latencyResults = {};
    
    for (const [name, container] of Object.entries(containers)) {
      if (name === 'bestEffort') continue;
      
      latencyResults[name] = [];
      
      const task = (async () => {
        for (let i = 0; i < 30; i++) {
          const start = Date.now();
          await container.execute('sleep 0.1 && echo done');
          const latency = Date.now() - start - 100; // 期待値100msを引く
          latencyResults[name].push(latency);
        }
      })();
      
      latencySensitiveTasks.push(task);
    }
    
    await Promise.all([noisyTask, ...latencySensitiveTasks]);
    
    // レイテンシへの影響を分析
    const avgLatencies = {};
    const p99Latencies = {};
    
    for (const [name, latencies] of Object.entries(latencyResults)) {
      avgLatencies[name] = average(latencies);
      p99Latencies[name] = percentile(latencies, 0.99);
    }
    
    // リソース制限がある方が影響を受けにくい
    expect(avgLatencies.highPriority).toBeLessThan(avgLatencies.low);
    expect(p99Latencies.highPriority).toBeLessThan(p99Latencies.low * 0.5);
  });

  it('should test I/O bandwidth limits', async () => {
    // I/O制限の設定
    await containers.highPriority.setIoLimit({
      device: '8:0',
      rbps: 100 * 1024 * 1024,  // 100MB/s read
      wbps: 100 * 1024 * 1024   // 100MB/s write
    });
    
    await containers.low.setIoLimit({
      device: '8:0',
      rbps: 10 * 1024 * 1024,   // 10MB/s read
      wbps: 10 * 1024 * 1024    // 10MB/s write
    });
    
    // 大量のI/Oを発生させる
    const ioTests = [
      {
        container: containers.highPriority,
        name: 'highPriority',
        expectedRate: 100 // MB/s
      },
      {
        container: containers.low,
        name: 'low',
        expectedRate: 10 // MB/s
      }
    ];
    
    for (const test of ioTests) {
      const result = await test.container.execute(
        'dd if=/dev/zero of=/tmp/test bs=1M count=1000 oflag=direct'
      );
      
      const stats = parseIoStats(result.output);
      const actualRate = stats.bytesWritten / stats.duration / 1024 / 1024;
      
      // 制限値の90%以上、110%以下
      expect(actualRate).toBeGreaterThan(test.expectedRate * 0.9);
      expect(actualRate).toBeLessThan(test.expectedRate * 1.1);
    }
  });

  it('should test CPU burst capability', async () => {
    // バーストコンテナとノーマルコンテナの比較
    const workload = 'python3 -c "import time; [sum(range(1000000)) for _ in range(10)]"';
    
    // アイドル期間
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // 同時に負荷を開始
    const [burstResult, normalResult] = await Promise.all([
      containers.burst.execute(workload),
      containers.medium.execute(workload)
    ]);
    
    // バーストコンテナの方が高速に完了
    expect(burstResult.duration).toBeLessThan(normalResult.duration * 0.8);
    
    // CPU使用率の時系列データ
    const cpuMetrics = await monitor.getCpuMetrics(
      burstResult.startTime,
      burstResult.endTime
    );
    
    // バースト期間中は制限を超えて使用
    const burstPeriod = cpuMetrics.burst.filter(m => m.value > 100);
    expect(burstPeriod.length).toBeGreaterThan(0);
  });

  it('should test memory pressure and reclaim', async () => {
    // メモリプレッシャーを段階的に増加
    const pressureStages = [
      { allocate: '50%', expected: 'normal' },
      { allocate: '80%', expected: 'pressure' },
      { allocate: '95%', expected: 'critical' }
    ];
    
    for (const stage of pressureStages) {
      console.log(`Testing memory pressure: ${stage.allocate}`);
      
      // 全コンテナでメモリを割り当て
      const tasks = Object.values(containers).map(container =>
        container.execute(`stress-ng --vm 1 --vm-bytes ${stage.allocate} --timeout 30s`)
      );
      
      // メモリ統計を監視
      const memStats = await monitor.collectMemoryStats(30000);
      
      await Promise.all(tasks);
      
      // プレッシャーレベルの確認
      const pressure = analyzePressure(memStats);
      
      expect(pressure.level).toBe(stage.expected);
      
      if (stage.expected === 'critical') {
        // ページ回収の発生を確認
        expect(pressure.pageReclaims).toBeGreaterThan(1000);
        // スワップ使用（設定されている場合）
        expect(pressure.swapUsage).toBeGreaterThan(0);
      }
    }
  });
});

// ネットワーク帯域制限テスト
describe('Network Bandwidth Control', () => {
  it('should enforce network rate limits', async () => {
    // TC (Traffic Control) 設定
    const networkLimits = [
      { container: 'highPriority', rate: '100mbit' },
      { container: 'medium', rate: '50mbit' },
      { container: 'low', rate: '10mbit' }
    ];
    
    for (const limit of networkLimits) {
      await applyNetworkLimit(limit.container, limit.rate);
    }
    
    // ネットワーク負荷テスト
    const results = await Promise.all(
      networkLimits.map(async (limit) => {
        const container = containers[limit.container];
        const result = await container.execute(
          'iperf3 -c iperf-server -t 10 -J'
        );
        
        const stats = JSON.parse(result.output);
        return {
          container: limit.container,
          expected: parseRate(limit.rate),
          actual: stats.end.sum_sent.bits_per_second
        };
      })
    );
    
    // 制限が適用されているか確認
    for (const result of results) {
      const ratio = result.actual / result.expected;
      expect(ratio).toBeGreaterThan(0.9);
      expect(ratio).toBeLessThan(1.1);
    }
  });
});

// ヘルパー関数
function calculateAverageCpuUsage(metrics) {
  const usage = {};
  
  for (const [container, data] of Object.entries(metrics)) {
    const cpuValues = data.map(m => m.cpu);
    usage[container] = average(cpuValues);
  }
  
  return usage;
}

function analyzePressure(memStats) {
  const latest = memStats[memStats.length - 1];
  const totalMemory = latest.total;
  const usedMemory = latest.used;
  const usagePercent = (usedMemory / totalMemory) * 100;
  
  let level = 'normal';
  if (usagePercent > 90) level = 'critical';
  else if (usagePercent > 75) level = 'pressure';
  
  return {
    level,
    usagePercent,
    pageReclaims: latest.pgmajfault,
    swapUsage: latest.swap_usage || 0
  };
}
```

### Green Phase (リソース制限の実装)
```javascript
// resource-manager.js
const Docker = require('dockerode');
const si = require('systeminformation');

class ResourceManager {
  constructor() {
    this.docker = new Docker();
    this.containers = new Map();
    this.limits = new Map();
  }
  
  async createContainer(name, resourceLimits) {
    const hostConfig = this.buildHostConfig(resourceLimits);
    
    const container = await this.docker.createContainer({
      name,
      Image: 'resource-test:latest',
      HostConfig: hostConfig,
      Env: [
        `CONTAINER_NAME=${name}`,
        `RESOURCE_LIMITS=${JSON.stringify(resourceLimits)}`
      ]
    });
    
    await container.start();
    
    this.containers.set(name, container);
    this.limits.set(name, resourceLimits);
    
    // リソースモニタリング開始
    this.startMonitoring(name, container);
    
    return new ContainerWrapper(container, this);
  }
  
  buildHostConfig(limits) {
    const config = {
      // CPU制限
      CpuQuota: limits.cpus ? parseInt(limits.cpus * 100000) : undefined,
      CpuPeriod: 100000,
      CpuShares: limits.cpuShares || 1024,
      
      // メモリ制限
      Memory: limits.memory ? this.parseMemory(limits.memory) : undefined,
      MemorySwap: limits.memorySwap ? this.parseMemory(limits.memorySwap) : undefined,
      MemoryReservation: limits.memoryReservation ? this.parseMemory(limits.memoryReservation) : undefined,
      
      // I/O制限
      BlkioWeight: limits.blkioWeight || 500,
      BlkioWeightDevice: limits.blkioWeightDevice || [],
      BlkioDeviceReadBps: limits.blkioReadBps || [],
      BlkioDeviceWriteBps: limits.blkioWriteBps || [],
      
      // その他の制限
      PidsLimit: limits.pidsLimit || 4096,
      Ulimits: limits.ulimits || []
    };
    
    // CPUセット（特定のCPUコアに固定）
    if (limits.cpuset) {
      config.CpusetCpus = limits.cpuset;
    }
    
    // cgroups v2 サポート
    if (this.supportsCgroupsV2()) {
      config.CgroupnsMode = 'private';
      
      // CPU burst設定（cgroups v2のみ）
      if (limits.cpuBurst) {
        config.CpuBurst = true;
      }
    }
    
    return config;
  }
  
  parseMemory(memStr) {
    const units = {
      'b': 1,
      'k': 1024,
      'm': 1024 * 1024,
      'g': 1024 * 1024 * 1024
    };
    
    const match = memStr.match(/^(\d+)([bkmg])?$/i);
    if (!match) throw new Error(`Invalid memory string: ${memStr}`);
    
    const value = parseInt(match[1]);
    const unit = (match[2] || 'b').toLowerCase();
    
    return value * units[unit];
  }
  
  supportsCgroupsV2() {
    // cgroups v2 の検出
    const fs = require('fs');
    try {
      const cgroupfs = fs.readFileSync('/proc/filesystems', 'utf8');
      return cgroupfs.includes('cgroup2');
    } catch (e) {
      return false;
    }
  }
  
  async startMonitoring(name, container) {
    const interval = setInterval(async () => {
      try {
        const stats = await container.stats({ stream: false });
        this.processStats(name, stats);
      } catch (error) {
        console.error(`Failed to get stats for ${name}:`, error);
        clearInterval(interval);
      }
    }, 1000);
    
    container.on('die', () => clearInterval(interval));
  }
  
  processStats(name, stats) {
    const processed = {
      timestamp: Date.now(),
      cpu: this.calculateCpuPercent(stats),
      memory: {
        usage: stats.memory_stats.usage,
        limit: stats.memory_stats.limit,
        percent: (stats.memory_stats.usage / stats.memory_stats.limit) * 100
      },
      io: {
        read: stats.blkio_stats.io_service_bytes_recursive?.find(s => s.op === 'read')?.value || 0,
        write: stats.blkio_stats.io_service_bytes_recursive?.find(s => s.op === 'write')?.value || 0
      },
      network: {
        rx: stats.networks?.eth0?.rx_bytes || 0,
        tx: stats.networks?.eth0?.tx_bytes || 0
      },
      pids: stats.pids_stats?.current || 0
    };
    
    // メトリクスストアに保存
    this.storeMetrics(name, processed);
    
    // 制限違反のチェック
    this.checkViolations(name, processed);
  }
  
  calculateCpuPercent(stats) {
    const cpuDelta = stats.cpu_stats.cpu_usage.total_usage - 
                     stats.precpu_stats.cpu_usage.total_usage;
    const systemDelta = stats.cpu_stats.system_cpu_usage - 
                        stats.precpu_stats.system_cpu_usage;
    
    if (systemDelta > 0 && cpuDelta > 0) {
      const cpuPercent = (cpuDelta / systemDelta) * 
                         stats.cpu_stats.online_cpus * 100;
      return Math.round(cpuPercent * 100) / 100;
    }
    
    return 0;
  }
  
  checkViolations(name, stats) {
    const limits = this.limits.get(name);
    if (!limits) return;
    
    const violations = [];
    
    // CPU制限チェック
    if (limits.cpus && stats.cpu > limits.cpus * 100) {
      violations.push({
        type: 'cpu',
        limit: limits.cpus * 100,
        actual: stats.cpu,
        severity: 'warning'
      });
    }
    
    // メモリ制限チェック
    if (stats.memory.percent > 90) {
      violations.push({
        type: 'memory',
        limit: stats.memory.limit,
        actual: stats.memory.usage,
        severity: stats.memory.percent > 95 ? 'critical' : 'warning'
      });
    }
    
    if (violations.length > 0) {
      this.handleViolations(name, violations);
    }
  }
  
  handleViolations(name, violations) {
    console.log(`Resource violations for ${name}:`, violations);
    
    // 重大な違反の場合はアクションを実行
    const criticalViolations = violations.filter(v => v.severity === 'critical');
    
    if (criticalViolations.length > 0) {
      // アラート送信、スケール調整など
      this.sendAlert(name, criticalViolations);
    }
  }
}

// コンテナラッパー
class ContainerWrapper {
  constructor(container, manager) {
    this.container = container;
    this.manager = manager;
  }
  
  async execute(command) {
    const exec = await this.container.exec({
      Cmd: ['sh', '-c', command],
      AttachStdout: true,
      AttachStderr: true
    });
    
    const stream = await exec.start();
    const output = await this.streamToString(stream);
    const inspectResult = await exec.inspect();
    
    return {
      output,
      exitCode: inspectResult.ExitCode,
      startTime: Date.now(),
      endTime: Date.now(),
      duration: 0 // 実際は計測する
    };
  }
  
  async setIoLimit(limits) {
    // 実行中のコンテナのI/O制限を動的に変更
    const update = {
      BlkioDeviceReadBps: [{
        Path: limits.device,
        Rate: limits.rbps
      }],
      BlkioDeviceWriteBps: [{
        Path: limits.device,
        Rate: limits.wbps
      }]
    };
    
    await this.container.update(update);
  }
  
  streamToString(stream) {
    return new Promise((resolve, reject) => {
      let output = '';
      
      stream.on('data', (chunk) => {
        output += chunk.toString();
      });
      
      stream.on('end', () => {
        resolve(output);
      });
      
      stream.on('error', reject);
    });
  }
}

// TC (Traffic Control) マネージャー
class NetworkController {
  async applyRateLimit(containerName, rate) {
    const container = await this.getContainer(containerName);
    const pid = await this.getContainerPid(container);
    
    // Network namespaceに入って設定
    const commands = [
      `nsenter -t ${pid} -n tc qdisc add dev eth0 root handle 1: htb default 30`,
      `nsenter -t ${pid} -n tc class add dev eth0 parent 1: classid 1:1 htb rate ${rate}`,
      `nsenter -t ${pid} -n tc class add dev eth0 parent 1:1 classid 1:30 htb rate ${rate}`,
      `nsenter -t ${pid} -n tc filter add dev eth0 protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:30`
    ];
    
    for (const cmd of commands) {
      await this.exec(cmd);
    }
  }
  
  async exec(command) {
    const { promisify } = require('util');
    const exec = promisify(require('child_process').exec);
    
    try {
      const { stdout, stderr } = await exec(command);
      if (stderr) console.error('TC stderr:', stderr);
      return stdout;
    } catch (error) {
      console.error('TC error:', error);
      throw error;
    }
  }
}

module.exports = { ResourceManager, NetworkController };
```

### Docker Compose設定
```yaml
# docker-compose.yml
version: '3.8'

services:
  # 高優先度コンテナ
  high-priority:
    build: .
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    environment:
      CONTAINER_ROLE: high-priority
      STRESS_PROFILE: normal
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
    cap_add:
      - SYS_ADMIN  # cgroups操作用

  # 中優先度コンテナ
  medium:
    build: .
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    environment:
      CONTAINER_ROLE: medium
      STRESS_PROFILE: normal

  # 低優先度コンテナ
  low:
    build: .
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    environment:
      CONTAINER_ROLE: low
      STRESS_PROFILE: normal

  # バースト可能コンテナ
  burst:
    build: .
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    environment:
      CONTAINER_ROLE: burst
      STRESS_PROFILE: burst
      CPU_BURST: "true"

  # ベストエフォートコンテナ（ノイジーネイバー）
  best-effort:
    build: .
    deploy:
      resources:
        limits:
          memory: 512M
        # CPU制限なし
    environment:
      CONTAINER_ROLE: best-effort
      STRESS_PROFILE: noisy

  # モニタリング
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
```

## 実行と分析

### 1. システム起動とベースライン測定
```bash
# 起動
docker-compose up -d

# ベースライン測定
./scripts/measure-baseline.sh
```

### 2. リソース競合テスト
```bash
# CPU競合
npm run test:cpu-contention

# メモリ競合
npm run test:memory-contention

# I/O競合
npm run test:io-contention
```

### 3. 監視とメトリクス
```bash
# cAdvisorダッシュボード
open http://localhost:8080

# リアルタイムモニタリング
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

## 成功基準

- [ ] CPU制限が±10%の精度で適用
- [ ] メモリ制限によるOOMの適切な動作
- [ ] I/O制限による帯域幅制御
- [ ] ノイジーネイバーの影響を最小化
- [ ] リソース不足時の優雅な劣化

## ベストプラクティス

### 1. CPU制限
```yaml
# 推奨設定
deploy:
  resources:
    limits:
      cpus: '2.0'      # ハード制限
    reservations:
      cpus: '1.0'      # 最小保証
```

### 2. メモリ制限
```yaml
# OOM回避設定
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

### 3. I/O優先度
```yaml
# ブロックI/O重み
blkio_config:
  weight: 500  # 10-1000
```

## トラブルシューティング

### 問題: CPU throttling が頻発
```bash
# throttling 確認
docker exec <container> cat /sys/fs/cgroup/cpu/cpu.stat | grep throttled

# 対策: CPU制限を緩和またはburst有効化
```

### 問題: メモリ不足でOOM
```bash
# OOMイベント確認
dmesg | grep -i "killed process"

# 対策: メモリ制限を増やすか、アプリケーション最適化
```

## 次のステップ

リソース管理の基礎を理解後、`11_dual_servers_manual_split`で複数サーバーへの展開を開始します。

## 学んだこと

- リソース制限の重要性と効果
- cgroups による細かな制御
- ノイジーネイバー問題の実際
- QoS実装の実践的アプローチ

## 参考資料

- [Docker Resource Constraints](https://docs.docker.com/config/containers/resource_constraints/)
- [Control Groups v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)
- [Linux Traffic Control](https://tldp.org/HOWTO/Traffic-Control-HOWTO/)
- [Container Performance Tuning](https://www.brendangregg.com/perf.html)