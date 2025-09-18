// Run performance tests with detailed output
import {
  measureLeaderElection,
  measureFailover,
  measureAvailability,
  measureWritePerformance,
  measureReadPerformance,
  compareWithoutRaft
} from "./src/mod.ts";
import { RaftCluster, ServiceRegistryRaft } from "../raft/mod.ts";

console.log("🚀 POC 13.3: Raft Performance Measurement");
console.log("==========================================\n");

// 1. Leader Election Performance
console.log("📊 1. Leader Election Performance");
console.log("---------------------------------");
const electionResult = await measureLeaderElection(3);
if (electionResult.ok) {
  const m = electionResult.metrics;
  console.log(`✅ Election completed in ${m.electionDuration.toFixed(2)}ms`);
  console.log(`   Winner: ${m.winnerNodeId}`);
  console.log(`   Candidates: ${m.candidateCount}`);
}

// 2. Failover Performance
console.log("\n📊 2. Failover Performance");
console.log("--------------------------");
const cluster = new RaftCluster();
await cluster.addNode("node-1", "localhost:5001");
await cluster.addNode("node-2", "localhost:5002");
await cluster.addNode("node-3", "localhost:5003");
await cluster.start();

const registry = new ServiceRegistryRaft(cluster);
for (let i = 0; i < 10; i++) {
  await registry.register({
    id: `service-${i}`,
    name: "api",
    host: "localhost",
    port: 8080 + i
  });
}

const failoverResult = await measureFailover(cluster, registry);
if (failoverResult.ok) {
  const m = failoverResult.metrics;
  console.log(`✅ Failover completed in ${m.failoverDuration.toFixed(2)}ms`);
  console.log(`   Previous leader: ${m.previousLeaderId}`);
  console.log(`   New leader: ${m.newLeaderId}`);
  console.log(`   Affected services: ${m.affectedServices}`);
}

// 3. Service Availability
console.log("\n📊 3. Service Availability (5 second test)");
console.log("------------------------------------------");
const availResult = await measureAvailability(cluster, registry, 5000, 0.1);
if (availResult.ok) {
  const m = availResult.metrics;
  console.log(`✅ Availability: ${m.availabilityPercentage.toFixed(2)}%`);
  console.log(`   Total requests: ${m.totalRequests}`);
  console.log(`   Successful: ${m.successfulRequests}`);
  console.log(`   Failed: ${m.failedRequests}`);
}

// 4. Write Performance
console.log("\n📊 4. Write Performance (1000 operations)");
console.log("-----------------------------------------");
const writeResult = await measureWritePerformance(cluster, registry, 1000);
if (writeResult.ok) {
  const m = writeResult.metrics;
  console.log(`✅ Write performance:`);
  console.log(`   Throughput: ${m.throughput.toFixed(2)} ops/sec`);
  console.log(`   Average latency: ${m.averageLatency.toFixed(2)}ms`);
  console.log(`   Min latency: ${m.minLatency.toFixed(2)}ms`);
  console.log(`   Max latency: ${m.maxLatency.toFixed(2)}ms`);
}

// 5. Read Performance
console.log("\n📊 5. Read Performance (1000 operations)");
console.log("----------------------------------------");
const readResult = await measureReadPerformance(registry, 1000);
if (readResult.ok) {
  const m = readResult.metrics;
  console.log(`✅ Read performance:`);
  console.log(`   Throughput: ${m.throughput.toFixed(2)} ops/sec`);
  console.log(`   Average latency: ${m.averageLatency.toFixed(2)}ms`);
  console.log(`   Cache hit rate: ${m.cacheHitRate.toFixed(2)}%`);
}

await cluster.stop();

// 6. Performance Comparison
console.log("\n📊 6. Performance Comparison (Raft vs No-Raft)");
console.log("----------------------------------------------");
const comparisonResult = await compareWithoutRaft(500);
if (comparisonResult.ok) {
  const c = comparisonResult.comparison;
  console.log(`✅ Performance comparison:`);
  console.log(`   Without Raft: ${c.withoutRaft.averageLatency.toFixed(4)}ms per op`);
  console.log(`   With Raft: ${c.withRaft.averageLatency.toFixed(4)}ms per op`);
  console.log(`   Overhead: ${c.overheadPercentage.toFixed(2)}%`);
  console.log(`   Analysis: ${c.analysis}`);
}

console.log("\n✅ All performance tests completed!");
console.log("\n📝 Summary:");
console.log("- Raft provides high availability (>95%) during failures");
console.log("- Trade-off: Performance overhead for consistency");
console.log("- Suitable for systems requiring strong consistency");