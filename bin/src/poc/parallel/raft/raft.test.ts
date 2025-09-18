import { assertEquals, assert, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeEach, afterEach } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import {
  RaftNode,
  RaftCluster,
  NodeState,
  ServiceRegistryRaft,
  ServiceInfo
} from "./raft-simple.ts";

describe("Priority 1: Basic Leader Election", () => {
  it("test_three_nodes_elect_one_leader", async () => {
    // 3ノードのクラスターを作成
    const cluster = new RaftCluster();
    
    const node1 = await cluster.addNode("node-1", "localhost:5001");
    const node2 = await cluster.addNode("node-2", "localhost:5002");
    const node3 = await cluster.addNode("node-3", "localhost:5003");
    
    // クラスターを開始
    await cluster.start();
    
    // リーダー選出を待つ（最大5秒）
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // リーダーが1つだけ選出されていることを確認
    const leaders = [node1, node2, node3].filter(n => n.getState() === NodeState.Leader);
    assertEquals(leaders.length, 1, "Exactly one leader should be elected");
    
    // フォロワーが2つあることを確認
    const followers = [node1, node2, node3].filter(n => n.getState() === NodeState.Follower);
    assertEquals(followers.length, 2, "Exactly two followers should exist");
    
    // クリーンアップ
    await cluster.stop();
  });
  
  it("test_leader_failure_triggers_new_election", async () => {
    const cluster = new RaftCluster();
    
    const node1 = await cluster.addNode("node-1", "localhost:5001");
    const node2 = await cluster.addNode("node-2", "localhost:5002");
    const node3 = await cluster.addNode("node-3", "localhost:5003");
    
    await cluster.start();
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 現在のリーダーを特定
    const initialLeader = [node1, node2, node3].find(n => n.getState() === NodeState.Leader);
    assertExists(initialLeader, "Initial leader should exist");
    const initialLeaderId = initialLeader.getId();
    
    // リーダーを停止
    await initialLeader.stop();
    
    // 新しいリーダー選出を待つ
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // 新しいリーダーが選出されていることを確認
    const remainingNodes = [node1, node2, node3].filter(n => n.getId() !== initialLeaderId);
    const newLeaders = remainingNodes.filter(n => n.getState() === NodeState.Leader);
    assertEquals(newLeaders.length, 1, "New leader should be elected");
    
    // 新しいリーダーは違うノード
    assert(newLeaders[0].getId() !== initialLeaderId, "New leader should be different");
    
    await cluster.stop();
  });
});

describe("Priority 2: Service Registry Replication", () => {
  let cluster: RaftCluster;
  let registry: ServiceRegistryRaft;
  
  beforeEach(async () => {
    cluster = new RaftCluster();
    registry = new ServiceRegistryRaft(cluster);
    
    await cluster.addNode("node-1", "localhost:5001");
    await cluster.addNode("node-2", "localhost:5002");
    await cluster.addNode("node-3", "localhost:5003");
    
    await cluster.start();
    await new Promise(resolve => setTimeout(resolve, 2000));
  });
  
  it("test_service_registration_replicated_to_all_nodes", async () => {
    // サービスを登録
    const service: ServiceInfo = {
      id: "api-1",
      name: "api",
      host: "localhost",
      port: 8080,
      metadata: { version: "1.0.0" }
    };
    
    await registry.register(service);
    
    // レプリケーションを待つ
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // すべてのノードから同じサービスが見えることを確認
    const nodes = cluster.getNodes();
    for (const node of nodes) {
      const services = await registry.discoverFrom(node.getId(), "api");
      assertEquals(services.length, 1, `Node ${node.getId()} should see the service`);
      assertEquals(services[0].id, "api-1");
    }
  });
  
  it("test_write_redirects_to_leader", async () => {
    // フォロワーノードを特定
    const follower = cluster.getNodes().find(n => n.getState() === NodeState.Follower);
    assertExists(follower, "Follower should exist");
    
    // フォロワー経由で書き込みを試みる
    const service: ServiceInfo = {
      id: "api-2",
      name: "api",
      host: "localhost",
      port: 8081
    };
    
    const result = await registry.registerViaNode(follower.getId(), service);
    
    // リーダーにリダイレクトされたことを確認
    assert(result.redirected, "Write should be redirected to leader");
    assertEquals(result.leaderId, cluster.getLeader()?.getId());
    
    // サービスが登録されていることを確認
    const services = await registry.discover("api");
    const registered = services.find(s => s.id === "api-2");
    assertExists(registered, "Service should be registered");
  });
  
  afterEach(async () => {
    await cluster.stop();
  });
});

describe("Priority 3: High Availability", () => {
  it("test_cluster_survives_one_node_failure", async () => {
    const cluster = new RaftCluster();
    const registry = new ServiceRegistryRaft(cluster);
    
    // 3ノードクラスター
    await cluster.addNode("node-1", "localhost:5001");
    await cluster.addNode("node-2", "localhost:5002");
    await cluster.addNode("node-3", "localhost:5003");
    
    await cluster.start();
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // サービスを登録
    await registry.register({
      id: "critical-service",
      name: "database",
      host: "localhost",
      port: 5432
    });
    
    // 1ノードを停止
    const nodeToStop = cluster.getNodes()[0];
    await nodeToStop.stop();
    
    // クラスターがまだ機能することを確認
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 新しいサービスを登録できる
    await registry.register({
      id: "new-service",
      name: "cache",
      host: "localhost",
      port: 6379
    });
    
    // 両方のサービスが見える
    const services = await registry.discover("");
    assertEquals(services.length, 2, "Both services should be visible");
    
    // リーダーが存在する
    const leader = cluster.getLeader();
    assertExists(leader, "Leader should exist with 2 nodes");
    
    await cluster.stop();
  });
  
  it("test_majority_required_for_operation", async () => {
    const cluster = new RaftCluster();
    const registry = new ServiceRegistryRaft(cluster);
    
    // 3ノードクラスター
    const node1 = await cluster.addNode("node-1", "localhost:5001");
    const node2 = await cluster.addNode("node-2", "localhost:5002");
    const node3 = await cluster.addNode("node-3", "localhost:5003");
    
    await cluster.start();
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 2ノードを停止（過半数を失う）
    await node2.stop();
    await node3.stop();
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 書き込みが失敗することを確認
    try {
      await registry.register({
        id: "should-fail",
        name: "test",
        host: "localhost",
        port: 9999
      });
      assert(false, "Write should fail without majority");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      assert(errorMessage.includes("no leader") || errorMessage.includes("majority"));
    }
    
    await cluster.stop();
  });
});