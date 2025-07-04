// Step by step test to identify the issue
import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { RaftCluster, ServiceRegistryRaft } from "../raft/mod.ts";

Deno.test("Step 1: Create cluster and check leader", async () => {
  const cluster = new RaftCluster();
  
  console.log("Adding nodes...");
  await cluster.addNode("node-1", "localhost:5001");
  await cluster.addNode("node-2", "localhost:5002");
  await cluster.addNode("node-3", "localhost:5003");
  
  console.log("Starting cluster...");
  await cluster.start();
  
  console.log("Checking for leader immediately...");
  let leader = cluster.getLeader();
  console.log("Leader after start:", leader?.getId());
  
  assertExists(leader, "Leader should exist immediately after start");
  assertEquals(leader.getId(), "node-1");
  
  await cluster.stop();
});

Deno.test("Step 2: Test service registration", async () => {
  const cluster = new RaftCluster();
  
  await cluster.addNode("node-1", "localhost:5001");
  await cluster.addNode("node-2", "localhost:5002");
  await cluster.addNode("node-3", "localhost:5003");
  
  await cluster.start();
  
  const registry = new ServiceRegistryRaft(cluster);
  
  // Register a service
  await registry.register({
    id: "api-1",
    name: "api",
    host: "localhost",
    port: 8080,
    metadata: { version: "1.0.0" }
  });
  
  // Check all nodes see the service
  const nodes = cluster.getNodes();
  for (const node of nodes) {
    const services = await registry.discoverFrom(node.getId(), "api");
    assertEquals(services.length, 1);
    assertEquals(services[0].id, "api-1");
  }
  
  await cluster.stop();
});