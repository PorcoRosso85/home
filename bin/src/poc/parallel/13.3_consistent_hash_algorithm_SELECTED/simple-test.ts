// Simple test without describe block
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { RaftCluster, ServiceRegistryRaft } from "../raft/mod.ts";

Deno.test("Basic Raft cluster creation and service registration", async () => {
  const cluster = new RaftCluster();
  
  await cluster.addNode("node-1", "localhost:5001");
  await cluster.addNode("node-2", "localhost:5002");
  await cluster.addNode("node-3", "localhost:5003");
  
  await cluster.start();
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const leader = cluster.getLeader();
  assertExists(leader, "Leader should be elected");
  
  const registry = new ServiceRegistryRaft(cluster);
  
  await registry.register({
    id: "test-1",
    name: "api",
    host: "localhost",
    port: 8080
  });
  
  const services = await registry.discover("api");
  assertEquals(services.length, 1);
  assertEquals(services[0].id, "test-1");
  
  await cluster.stop();
});