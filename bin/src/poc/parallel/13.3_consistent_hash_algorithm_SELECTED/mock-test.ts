// Simplified mock test to verify basic setup
import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { RaftCluster, ServiceRegistryRaft } from "../raft/mod.ts";

describe("POC 13.3: Basic Raft Integration", () => {
  it("should create raft cluster and register service", async () => {
    // Raftクラスターを作成
    const cluster = new RaftCluster();
    
    // 3ノード追加
    await cluster.addNode("node-1", "localhost:5001");
    await cluster.addNode("node-2", "localhost:5002");
    await cluster.addNode("node-3", "localhost:5003");
    
    // クラスター開始
    await cluster.start();
    
    // リーダー選出を待つ
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // レジストリ作成
    const registry = new ServiceRegistryRaft(cluster);
    
    // サービス登録
    await registry.register({
      id: "test-service",
      name: "api",
      host: "localhost",
      port: 8080
    });
    
    // サービスが登録されたことを確認
    const services = await registry.discover("api");
    assertEquals(services.length, 1);
    assertEquals(services[0].id, "test-service");
    
    // クリーンアップ
    await cluster.stop();
  });
});