import { assertEquals, assert, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { RaftCluster, ServiceRegistryRaft, ServiceInfo, NodeState } from "../raft/mod.ts";

// POC 13.3: Raft + Dynamic Service Orchestration Integration Tests

Deno.test("High Availability: Orchestrator with Raft consensus", async () => {
  // Raftクラスターの作成
  const raftCluster = new RaftCluster();
  
  // 3つのオーケストレーターノード
  await raftCluster.addNode("orchestrator-1", "localhost:7001");
  await raftCluster.addNode("orchestrator-2", "localhost:7002");
  await raftCluster.addNode("orchestrator-3", "localhost:7003");
  
  await raftCluster.start();
  
  // Raftベースのサービスレジストリ
  const registry = new ServiceRegistryRaft(raftCluster);
  
  // サービス登録
  const service1: ServiceInfo = {
    id: "api-1",
    name: "api",
    host: "localhost",
    port: 8080,
    metadata: { version: "1.0.0" }
  };
  
  await registry.register(service1);
  
  // 全ノードから同じサービスが見える
  const nodes = raftCluster.getNodes();
  for (const node of nodes) {
    const services = await registry.discoverFrom(node.getId(), "api");
    assertEquals(services.length, 1);
    assertEquals(services[0].id, "api-1");
  }
  
  await raftCluster.stop();
});

Deno.test("High Availability: Leader failover", async () => {
  const raftCluster = new RaftCluster();
  const registry = new ServiceRegistryRaft(raftCluster);
  
  // 3つのオーケストレーター
  await raftCluster.addNode("orchestrator-1", "localhost:7001");
  await raftCluster.addNode("orchestrator-2", "localhost:7002");
  await raftCluster.addNode("orchestrator-3", "localhost:7003");
  
  await raftCluster.start();
  
  // 複数のサービスを登録
  const services = [
    { id: "api-1", name: "api", host: "localhost", port: 8080 },
    { id: "api-2", name: "api", host: "localhost", port: 8081 },
    { id: "db-1", name: "database", host: "localhost", port: 5432 }
  ];
  
  for (const service of services) {
    await registry.register(service);
  }
  
  // 現在のリーダーを特定
  const initialLeader = raftCluster.getLeader();
  assertExists(initialLeader);
  const initialLeaderId = initialLeader.getId();
  
  // リーダーを停止
  await initialLeader.stop();
  
  // 新しいリーダーが選出された
  const newLeader = raftCluster.getLeader();
  assertExists(newLeader);
  assert(newLeader.getId() !== initialLeaderId);
  
  // サービスはまだ利用可能
  const discoveredServices = await registry.discover("");
  assertEquals(discoveredServices.length, 3);
  
  // 新しいサービスも登録可能
  await registry.register({
    id: "cache-1",
    name: "cache",
    host: "localhost",
    port: 6379
  });
  
  await raftCluster.stop();
});

Deno.test("Distributed Service Discovery", async () => {
  const raftCluster = new RaftCluster();
  const registry = new ServiceRegistryRaft(raftCluster);
  
  // 複数のオーケストレーターノード
  const orchestrators = [];
  for (let i = 1; i <= 3; i++) {
    const node = await raftCluster.addNode(
      `orchestrator-${i}`,
      `localhost:700${i}`
    );
    orchestrators.push(node);
  }
  
  await raftCluster.start();
  
  // 各オーケストレーターから異なるサービスを登録
  const registrations = [
    { nodeId: "orchestrator-1", service: { id: "svc-1", name: "web", host: "10.0.0.1", port: 80 } },
    { nodeId: "orchestrator-2", service: { id: "svc-2", name: "api", host: "10.0.0.2", port: 8080 } },
    { nodeId: "orchestrator-3", service: { id: "svc-3", name: "db", host: "10.0.0.3", port: 5432 } }
  ];
  
  // 各ノード経由で登録（フォロワーでもリダイレクトされる）
  for (const reg of registrations) {
    const result = await registry.registerViaNode(reg.nodeId, reg.service);
    // フォロワーからの場合はリダイレクト
    if (raftCluster.getNode(reg.nodeId)?.getState() !== NodeState.Leader) {
      assert(result.redirected);
    }
  }
  
  // 全てのサービスが全ノードから見える
  for (const orchestrator of orchestrators) {
    const allServices = await registry.discoverFrom(orchestrator.getId(), "");
    assertEquals(allServices.length, 3);
    
    // 特定のサービスタイプの検索
    const webServices = await registry.discoverFrom(orchestrator.getId(), "web");
    assertEquals(webServices.length, 1);
    assertEquals(webServices[0].id, "svc-1");
  }
  
  await raftCluster.stop();
});

Deno.test("Fault Tolerant Routing", async () => {
  const raftCluster = new RaftCluster();
  const registry = new ServiceRegistryRaft(raftCluster);
  
  // オーケストレーターのセットアップ
  await raftCluster.addNode("orchestrator-1", "localhost:7001");
  await raftCluster.addNode("orchestrator-2", "localhost:7002");
  await raftCluster.addNode("orchestrator-3", "localhost:7003");
  
  await raftCluster.start();
  
  // 複数のバックエンドサービスを登録
  const backends = [
    { id: "backend-1", name: "api", host: "localhost", port: 8001, metadata: { weight: 1 } },
    { id: "backend-2", name: "api", host: "localhost", port: 8002, metadata: { weight: 2 } },
    { id: "backend-3", name: "api", host: "localhost", port: 8003, metadata: { weight: 1 } }
  ];
  
  for (const backend of backends) {
    await registry.register(backend);
  }
  
  // ルーティングをシミュレート
  const routingRequests = 100;
  const routingResults: Record<string, number> = {};
  
  for (let i = 0; i < routingRequests; i++) {
    // ランダムなオーケストレーターを選択
    const nodes = raftCluster.getNodes();
    const randomNode = nodes[Math.floor(Math.random() * nodes.length)];
    const services = await registry.discoverFrom(randomNode.getId(), "api");
    
    // 重み付けルーティング
    const selected = selectWeightedService(services);
    routingResults[selected.id] = (routingResults[selected.id] || 0) + 1;
  }
  
  // 重みに応じた分散を確認
  console.log("Routing distribution:", routingResults);
  assert(routingResults["backend-2"] > routingResults["backend-1"]);
  assert(routingResults["backend-2"] > routingResults["backend-3"]);
  
  // 1つのオーケストレーターを停止
  const nodeToStop = raftCluster.getNodes()[0];
  await nodeToStop.stop();
  
  // ルーティングが継続することを確認
  const postFailureResults: Record<string, number> = {};
  
  for (let i = 0; i < 50; i++) {
    // 残りのノードからランダムに選択
    const activeNodes = raftCluster.getNodes().filter(n => !n.isStopped());
    const randomNode = activeNodes[Math.floor(Math.random() * activeNodes.length)];
    
    const services = await registry.discoverFrom(randomNode.getId(), "api");
    assertEquals(services.length, 3); // 全サービスがまだ見える
    
    const selected = selectWeightedService(services);
    postFailureResults[selected.id] = (postFailureResults[selected.id] || 0) + 1;
  }
  
  // 障害後もルーティングが機能
  assert(Object.keys(postFailureResults).length === 3);
  
  await raftCluster.stop();
});

Deno.test("Coordinated Deployment", async () => {
  const raftCluster = new RaftCluster();
  const registry = new ServiceRegistryRaft(raftCluster);
  
  // オーケストレータークラスター
  await raftCluster.addNode("orchestrator-1", "localhost:7001");
  await raftCluster.addNode("orchestrator-2", "localhost:7002");
  await raftCluster.addNode("orchestrator-3", "localhost:7003");
  
  await raftCluster.start();
  
  // 現在のバージョン（安定版）
  const stableServices = [
    { id: "api-v1-1", name: "api", host: "localhost", port: 8001, metadata: { version: "1.0", canary: false } },
    { id: "api-v1-2", name: "api", host: "localhost", port: 8002, metadata: { version: "1.0", canary: false } },
    { id: "api-v1-3", name: "api", host: "localhost", port: 8003, metadata: { version: "1.0", canary: false } }
  ];
  
  for (const service of stableServices) {
    await registry.register(service);
  }
  
  // カナリーデプロイメント開始（10%のトラフィック）
  const canaryService = {
    id: "api-v2-1",
    name: "api",
    host: "localhost",
    port: 8004,
    metadata: { version: "2.0", canary: true, trafficPercentage: 10 }
  };
  
  await registry.register(canaryService);
  
  // トラフィック分散をシミュレート
  const totalRequests = 1000;
  const versionCount: Record<string, number> = { "1.0": 0, "2.0": 0 };
  
  for (let i = 0; i < totalRequests; i++) {
    const services = await registry.discover("api");
    const selected = selectCanaryAwareService(services, 10);
    versionCount[selected.metadata.version]++;
  }
  
  // カナリーが約10%のトラフィックを受けることを確認
  const canaryPercentage = (versionCount["2.0"] / totalRequests) * 100;
  console.log(`Canary traffic: ${canaryPercentage}%`);
  assert(canaryPercentage > 5 && canaryPercentage < 15);
  
  await raftCluster.stop();
});

// ヘルパー関数：重み付けサービス選択
function selectWeightedService(services: any[]): any {
  const totalWeight = services.reduce((sum, s) => sum + (s.metadata?.weight || 1), 0);
  let random = Math.random() * totalWeight;
  
  for (const service of services) {
    const weight = service.metadata?.weight || 1;
    random -= weight;
    if (random <= 0) {
      return service;
    }
  }
  
  return services[0];
}

// ヘルパー関数：カナリー考慮のサービス選択
function selectCanaryAwareService(services: any[], canaryPercentage: number): any {
  const canaryServices = services.filter(s => s.metadata?.canary);
  const stableServices = services.filter(s => !s.metadata?.canary);
  
  if (Math.random() * 100 < canaryPercentage && canaryServices.length > 0) {
    return canaryServices[Math.floor(Math.random() * canaryServices.length)];
  } else if (stableServices.length > 0) {
    return stableServices[Math.floor(Math.random() * stableServices.length)];
  }
  
  return services[0];
}