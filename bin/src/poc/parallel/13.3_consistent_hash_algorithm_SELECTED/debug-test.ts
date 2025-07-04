// Debug test to understand leader election
import { RaftCluster } from "../raft/mod.ts";

const cluster = new RaftCluster();

console.log("1. Adding nodes...");
await cluster.addNode("node-1", "localhost:5001");
await cluster.addNode("node-2", "localhost:5002");
await cluster.addNode("node-3", "localhost:5003");

console.log("2. Before start - Leader:", cluster.getLeader()?.getId());

console.log("3. Starting cluster...");
await cluster.start();

console.log("4. After start - Leader:", cluster.getLeader()?.getId());

// Check all nodes
console.log("5. All nodes state:");
for (const node of cluster.getNodes()) {
  console.log(`   ${node.getId()}: ${node.getState()}`);
}

await cluster.stop();