# POC 13: Dynamic Service Orchestration

## 🎯 概要

アルゴリズムに依存しない、実践的な分散並列アーキテクチャの基盤を構築。サービスディスカバリー、ヘルスチェック、動的ルーティング、段階的デプロイを統合した運用可能なシステム。

## 🔄 なぜこのPOCが必要か

従来のPOCは特定のアルゴリズム（Consistent Hash等）に焦点を当てていたが、実際の分散システムでは：
- サーバーは動的に増減する
- 障害は必ず発生する
- デプロイは段階的に行う必要がある
- アルゴリズムは要件により変更される

## 📋 実装する機能

### 1. **Service Registry（サービスレジストリ）**
```typescript
// 全サーバーの状態を一元管理
interface ServiceRegistry {
  register(service: ServiceInfo): Promise<void>;
  deregister(serviceId: string): Promise<void>;
  discover(serviceName: string): Promise<ServiceInfo[]>;
  watch(serviceName: string): AsyncIterator<ServiceEvent>;
}
```

### 2. **Health Check System**
```typescript
// 能動的・受動的ヘルスチェック
interface HealthChecker {
  checkHealth(service: ServiceInfo): Promise<HealthStatus>;
  enableCircuitBreaker(threshold: number): void;
  getHealthyServices(): ServiceInfo[];
}
```

### 3. **Dynamic Router**
```typescript
// プラガブルなルーティング戦略
interface DynamicRouter {
  setStrategy(strategy: RoutingStrategy): void;
  route(request: Request): Promise<ServiceInfo>;
  updateTopology(services: ServiceInfo[]): void;
}
```

### 4. **Progressive Deployment**
```typescript
// 段階的なトラフィック移行
interface DeploymentController {
  canaryDeploy(newService: ServiceInfo, percentage: number): void;
  blueGreenSwitch(from: string, to: string): void;
  rollback(): void;
}
```

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────┐
│              Client Requests                 │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│          Envoy Proxy (Entry Point)          │
│  ┌─────────────────────────────────────┐    │
│  │    Dynamic Service Orchestrator     │    │
│  │  ┌─────────────┬─────────────────┐  │    │
│  │  │  Service    │   Health Check  │  │    │
│  │  │  Registry   │     System      │  │    │
│  │  └──────┬──────┴────────┬────────┘  │    │
│  │         │               │           │    │
│  │  ┌──────▼───────────────▼────────┐  │    │
│  │  │      Dynamic Router           │  │    │
│  │  │  ┌──────────┬──────────┐     │  │    │
│  │  │  │Strategy A│Strategy B│ ... │  │    │
│  │  │  └──────────┴──────────┘     │  │    │
│  │  └───────────────────────────────┘  │    │
│  └─────────────────────────────────────┘    │
└────────────────────┬────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Server 1   │ │   Server 2   │ │   Server N   │
│  ┌────────┐  │ │  ┌────────┐  │ │  ┌────────┐  │
│  │ Health │  │ │  │ Health │  │ │  │ Health │  │
│  │Endpoint│  │ │  │Endpoint│  │ │  │Endpoint│  │
│  └────────┘  │ │  └────────┘  │ │  └────────┘  │
│              │ │              │ │              │
│  App Logic   │ │  App Logic   │ │  App Logic   │
└──────────────┘ └──────────────┘ └──────────────┘
        ⬆               ⬆               ⬆
        └───────────────┴───────────────┘
                Service Discovery
```

## 📝 TDDアプローチ

### Red Phase: 動的サービス管理のテスト
```typescript
// test/dynamic-orchestration.test.ts
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { ServiceOrchestrator } from "../src/mod.ts";

describe("Dynamic Service Orchestration", () => {
  let orchestrator: ServiceOrchestrator;
  
  beforeEach(() => {
    orchestrator = new ServiceOrchestrator({
      registryUrl: "memory://", // In-memory for testing
      healthCheckInterval: 1000,
    });
  });

  it("should automatically discover new services", async () => {
    // 新サービスを登録
    const service1 = {
      id: "api-1",
      name: "api",
      host: "localhost",
      port: 3001,
      metadata: { version: "1.0.0" }
    };
    
    await orchestrator.register(service1);
    
    // 自動的に発見される
    const discovered = await orchestrator.discover("api");
    assertEquals(discovered.length, 1);
    assertEquals(discovered[0].id, "api-1");
  });

  it("should remove unhealthy services from routing", async () => {
    // 3つのサービスを登録
    const services = [
      { id: "api-1", name: "api", host: "localhost", port: 3001 },
      { id: "api-2", name: "api", host: "localhost", port: 3002 },
      { id: "api-3", name: "api", host: "localhost", port: 3003 }
    ];
    
    for (const svc of services) {
      await orchestrator.register(svc);
    }
    
    // api-2を不健全にする
    orchestrator.mockHealthStatus("api-2", "unhealthy");
    
    // ヘルスチェック実行
    await orchestrator.runHealthCheck();
    
    // 健全なサービスのみ返される
    const healthy = await orchestrator.getHealthyServices("api");
    assertEquals(healthy.length, 2);
    assert(!healthy.find(s => s.id === "api-2"));
  });

  it("should support canary deployment", async () => {
    // 既存サービス
    const v1 = { id: "api-v1", name: "api", version: "1.0.0", port: 3001 };
    await orchestrator.register(v1);
    
    // 新バージョンをカナリアデプロイ
    const v2 = { id: "api-v2", name: "api", version: "2.0.0", port: 3002 };
    await orchestrator.canaryDeploy(v2, 20); // 20%のトラフィック
    
    // 1000リクエストをルーティング
    const routing = { v1: 0, v2: 0 };
    for (let i = 0; i < 1000; i++) {
      const selected = await orchestrator.route({ path: "/api" });
      routing[selected.version === "1.0.0" ? "v1" : "v2"]++;
    }
    
    // 約20%がv2にルーティングされる
    const v2Percentage = (routing.v2 / 1000) * 100;
    assert(v2Percentage >= 15 && v2Percentage <= 25);
  });

  it("should handle graceful shutdown", async () => {
    const service = { id: "api-1", name: "api", port: 3001 };
    await orchestrator.register(service);
    
    // グレースフルシャットダウン開始
    await orchestrator.beginGracefulShutdown("api-1");
    
    // 新規リクエストは受け付けない
    const services = await orchestrator.discover("api");
    assertEquals(services.length, 0);
    
    // 既存接続は維持（ドレイン）
    const draining = await orchestrator.isDraining("api-1");
    assert(draining);
  });
});

describe("Routing Strategy Flexibility", () => {
  it("should support pluggable routing algorithms", async () => {
    const orchestrator = new ServiceOrchestrator();
    
    // Round Robin
    orchestrator.setRoutingStrategy("round-robin");
    const rr1 = await orchestrator.route({ path: "/" });
    const rr2 = await orchestrator.route({ path: "/" });
    assert(rr1.id !== rr2.id);
    
    // Consistent Hash
    orchestrator.setRoutingStrategy("consistent-hash");
    const ch1 = await orchestrator.route({ path: "/user/123" });
    const ch2 = await orchestrator.route({ path: "/user/123" });
    assertEquals(ch1.id, ch2.id); // 同じユーザーは同じサーバー
    
    // Least Connections
    orchestrator.setRoutingStrategy("least-connections");
    // 実装詳細...
    
    // Custom Strategy
    orchestrator.setRoutingStrategy({
      name: "custom-geo",
      select: async (services, request) => {
        // 地理的に最も近いサーバーを選択
        const userRegion = request.headers.get("x-region");
        return services.find(s => s.metadata.region === userRegion) || services[0];
      }
    });
  });
});
```

## 🚀 実装のポイント

### 1. **疎結合設計**
- サービスディスカバリーは実装を選択可能（etcd, Consul, Redis等）
- ルーティングアルゴリズムはプラガブル
- ヘルスチェックは設定可能

### 2. **障害への耐性**
- Circuit Breaker pattern
- Retry with exponential backoff
- Bulkhead isolation

### 3. **観測可能性**
- メトリクス収集
- 分散トレーシング準備
- ログ集約

### 4. **実運用考慮**
- ゼロダウンタイムデプロイ
- 設定の動的更新
- バックプレッシャー対応

## 📊 期待される成果

1. **柔軟性**: アルゴリズムやストレージを簡単に変更可能
2. **信頼性**: 自動的な障害検出と回復
3. **運用性**: 段階的デプロイとロールバック
4. **拡張性**: 新機能の追加が容易

## 🔗 次のステップ

このPOC 13で構築した基盤の上に：
- POC 13.1: Consistent Hashingの統合
- POC 15: データパーティショニング
- POC 17: キャッシュレイヤー
- POC 19: 読み書き分離

すべてが実運用可能な形で動作します。