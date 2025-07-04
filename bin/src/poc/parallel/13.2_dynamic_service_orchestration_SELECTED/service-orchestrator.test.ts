import { assertEquals, assertExists, assert } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { 
  ServiceOrchestrator,
  ServiceRegistry,
  HealthChecker,
  DynamicRouter,
  DeploymentController,
  ServiceInfo,
  ServiceEvent,
  HealthStatus,
  RoutingStrategy
} from "./service-orchestrator.ts";

describe("Service Registry", () => {
  let registry: ServiceRegistry;
  
  beforeEach(() => {
    registry = new ServiceRegistry();
  });
  
  it("test_register_new_service_can_be_discovered", async () => {
    const service: ServiceInfo = {
      id: "api-1",
      name: "api",
      host: "localhost",
      port: 3001,
      metadata: { version: "1.0.0" }
    };
    
    await registry.register(service);
    
    const discovered = await registry.discover("api");
    assertEquals(discovered.length, 1);
    assertEquals(discovered[0].id, "api-1");
  });
  
  it("test_deregister_removes_service_from_discovery", async () => {
    const service: ServiceInfo = {
      id: "api-1",
      name: "api",
      host: "localhost",
      port: 3001
    };
    
    await registry.register(service);
    await registry.deregister("api-1");
    
    const discovered = await registry.discover("api");
    assertEquals(discovered.length, 0);
  });
  
  it("test_watch_emits_events_on_service_changes", async () => {
    const events: ServiceEvent[] = [];
    const watcher = registry.watch("api");
    
    // 非同期でイベントを収集
    (async () => {
      for await (const event of watcher) {
        events.push(event);
        if (events.length >= 2) break;
      }
    })();
    
    // サービスを登録・削除
    await registry.register({
      id: "api-1",
      name: "api",
      host: "localhost",
      port: 3001
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    await registry.deregister("api-1");
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    assertEquals(events.length, 2);
    assertEquals(events[0].type, "added");
    assertEquals(events[1].type, "removed");
  });
});

describe("Health Check System", () => {
  let healthChecker: HealthChecker;
  let mockServices: ServiceInfo[];
  
  beforeEach(() => {
    healthChecker = new HealthChecker();
    mockServices = [
      { id: "api-1", name: "api", host: "localhost", port: 3001 },
      { id: "api-2", name: "api", host: "localhost", port: 3002 },
      { id: "api-3", name: "api", host: "localhost", port: 3003 }
    ];
  });
  
  it("test_unhealthy_services_are_excluded", async () => {
    // api-2を不健全にする
    healthChecker.mockHealthStatus("api-2", "unhealthy");
    
    const healthyServices = await healthChecker.getHealthyServices(mockServices);
    assertEquals(healthyServices.length, 2);
    assert(!healthyServices.find((s: ServiceInfo) => s.id === "api-2"));
  });
  
  it("test_circuit_breaker_opens_after_threshold", async () => {
    healthChecker.enableCircuitBreaker(3); // 3回失敗でオープン
    
    // 3回失敗させる
    for (let i = 0; i < 3; i++) {
      await healthChecker.checkHealth(mockServices[0]);
    }
    
    const status = await healthChecker.getCircuitBreakerStatus("api-1");
    assertEquals(status, "open");
  });
  
  it("test_health_check_with_retry", async () => {
    let attempts = 0;
    healthChecker.onHealthCheck = async (service) => {
      attempts++;
      if (attempts < 2) {
        throw new Error("Connection failed");
      }
      return { healthy: true, responseTime: 50 };
    };
    
    const result = await healthChecker.checkHealthWithRetry(mockServices[0], 3);
    assertEquals(result.healthy, true);
    assertEquals(attempts, 2); // 2回目で成功
  });
});

describe("Dynamic Router", () => {
  let router: DynamicRouter;
  let services: ServiceInfo[];
  
  beforeEach(() => {
    router = new DynamicRouter();
    services = [
      { id: "api-1", name: "api", host: "localhost", port: 3001, metadata: { region: "us-east" } },
      { id: "api-2", name: "api", host: "localhost", port: 3002, metadata: { region: "eu-west" } },
      { id: "api-3", name: "api", host: "localhost", port: 3003, metadata: { region: "us-east" } }
    ];
    router.updateTopology(services);
  });
  
  it("test_pluggable_routing_strategies", async () => {
    // Round Robin
    router.setStrategy("round-robin");
    const rr1 = await router.route({ path: "/" });
    const rr2 = await router.route({ path: "/" });
    assert(rr1.id !== rr2.id);
    
    // Custom Strategy
    const customStrategy: RoutingStrategy = {
      name: "prefer-us-east",
      select: async (services, request) => {
        const usEastServers = services.filter(s => s.metadata?.region === "us-east");
        return usEastServers[0] || services[0];
      }
    };
    
    router.setStrategy(customStrategy);
    const custom = await router.route({ path: "/" });
    assertEquals(custom.metadata?.region, "us-east");
  });
  
  it("test_topology_update_affects_routing", async () => {
    router.setStrategy("round-robin");
    
    // 新しいサーバーを追加
    const newService: ServiceInfo = {
      id: "api-4",
      name: "api",
      host: "localhost",
      port: 3004
    };
    
    router.updateTopology([...services, newService]);
    
    // 新しいサーバーも選ばれることを確認
    const selectedIds = new Set<string>();
    for (let i = 0; i < 10; i++) {
      const selected = await router.route({ path: "/" });
      selectedIds.add(selected.id);
    }
    
    assert(selectedIds.has("api-4"));
  });
  
  it("test_geographic_routing", async () => {
    const geoStrategy: RoutingStrategy = {
      name: "geo-routing",
      select: async (services, request) => {
        const userRegion = request.headers?.get("x-region") || "us-east";
        const regionalServers = services.filter(s => s.metadata?.region === userRegion);
        return regionalServers[0] || services[0];
      }
    };
    
    router.setStrategy(geoStrategy);
    
    const euRequest = { path: "/", headers: new Headers({ "x-region": "eu-west" }) };
    const euServer = await router.route(euRequest);
    assertEquals(euServer.metadata?.region, "eu-west");
  });
});

describe("Progressive Deployment", () => {
  let deployment: DeploymentController;
  let orchestrator: ServiceOrchestrator;
  
  beforeEach(() => {
    orchestrator = new ServiceOrchestrator();
    deployment = orchestrator.deployment;
    
    // 既存サービスを登録
    orchestrator.register({
      id: "api-v1",
      name: "api",
      host: "localhost",
      port: 3001,
      metadata: { version: "1.0.0" }
    });
  });
  
  it("test_canary_deployment_splits_traffic", async () => {
    const v2Service: ServiceInfo = {
      id: "api-v2",
      name: "api",
      host: "localhost",
      port: 3002,
      metadata: { version: "2.0.0" }
    };
    
    await deployment.canaryDeploy(v2Service, 20); // 20%トラフィック
    
    // 1000リクエストでトラフィック分割を確認
    const routing = { v1: 0, v2: 0 };
    for (let i = 0; i < 1000; i++) {
      const selected = await orchestrator.route({ path: "/api" });
      const version = selected.metadata?.version;
      if (version === "1.0.0") routing.v1++;
      else if (version === "2.0.0") routing.v2++;
    }
    
    const v2Percentage = (routing.v2 / 1000) * 100;
    assert(v2Percentage >= 15 && v2Percentage <= 25);
  });
  
  it("test_blue_green_switch", async () => {
    const greenService: ServiceInfo = {
      id: "api-green",
      name: "api",
      host: "localhost",
      port: 3002,
      metadata: { version: "2.0.0", deployment: "green" }
    };
    
    await orchestrator.register(greenService);
    
    // Blue(v1)からGreen(v2)へ切り替え
    await deployment.blueGreenSwitch("api-v1", "api-green");
    
    // すべてのトラフィックがGreenへ
    for (let i = 0; i < 10; i++) {
      const selected = await orchestrator.route({ path: "/api" });
      assertEquals(selected.id, "api-green");
    }
  });
  
  it("test_rollback_restores_previous_state", async () => {
    const v2Service: ServiceInfo = {
      id: "api-v2",
      name: "api",
      host: "localhost",
      port: 3002,
      metadata: { version: "2.0.0" }
    };
    
    await deployment.canaryDeploy(v2Service, 50);
    
    // ロールバック
    await deployment.rollback();
    
    // すべてのトラフィックがv1に戻る
    for (let i = 0; i < 10; i++) {
      const selected = await orchestrator.route({ path: "/api" });
      assertEquals(selected.metadata?.version, "1.0.0");
    }
  });
});

describe("Integration - Dynamic Service Discovery", () => {
  it("test_new_container_auto_discovery_and_routing", async () => {
    const orchestrator = new ServiceOrchestrator({
      discoveryInterval: 100 // 100msごとに探索
    });
    
    // 最初は2台
    await orchestrator.register({
      id: "app-1",
      name: "app",
      host: "localhost",
      port: 4001
    });
    await orchestrator.register({
      id: "app-2",
      name: "app",
      host: "localhost",
      port: 4002
    });
    
    const initialCount = (await orchestrator.discover("app")).length;
    assertEquals(initialCount, 2);
    
    // 新しいコンテナが起動（シミュレート）
    setTimeout(() => {
      orchestrator.register({
        id: "app-3",
        name: "app",
        host: "localhost",
        port: 4003
      });
    }, 200);
    
    // 自動発見を待つ
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const finalCount = (await orchestrator.discover("app")).length;
    assertEquals(finalCount, 3);
    
    // ルーティングにも反映されている
    const selectedIds = new Set<string>();
    for (let i = 0; i < 9; i++) {
      const selected = await orchestrator.route({ path: "/" });
      selectedIds.add(selected.id);
    }
    assertEquals(selectedIds.size, 3);
    assert(selectedIds.has("app-3"));
    
    // Clean up
    orchestrator.destroy();
  });
  
  it("test_container_failure_auto_exclusion", async () => {
    const orchestrator = new ServiceOrchestrator({
      healthCheckInterval: 100
    });
    
    // 3台登録
    const services = [
      { id: "app-1", name: "app", host: "localhost", port: 4001 },
      { id: "app-2", name: "app", host: "localhost", port: 4002 },
      { id: "app-3", name: "app", host: "localhost", port: 4003 }
    ];
    
    for (const svc of services) {
      await orchestrator.register(svc);
    }
    
    // app-2を故障させる
    orchestrator.healthChecker.mockHealthStatus("app-2", "unhealthy");
    
    // ヘルスチェックを待つ
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // app-2は選ばれない
    for (let i = 0; i < 20; i++) {
      const selected = await orchestrator.route({ path: "/" });
      assert(selected.id !== "app-2");
    }
    
    // Clean up
    orchestrator.destroy();
  });
});