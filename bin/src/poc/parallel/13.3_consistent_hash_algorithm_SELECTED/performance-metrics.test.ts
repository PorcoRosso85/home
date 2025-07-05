// Performance metrics test - TDD Red Phase
// Following bin/docs conventions

import { assertEquals, assert, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { RaftCluster, ServiceRegistryRaft } from "../raft/mod.ts";
import {
  measureLeaderElection,
  measureFailover,
  measureAvailability,
  measureWritePerformance,
  measureReadPerformance,
  compareWithoutRaft,
  type LeaderElectionResult,
  type FailoverResult,
  type AvailabilityResult,
  type WritePerformanceResult,
  type ComparisonResult
} from "./src/mod.ts";

// Test: Leader election performance measurement
Deno.test("Performance: Leader election time should be measured", async () => {
  const result = await measureLeaderElection(3);
  
  assert(result.ok, "Leader election measurement should succeed");
  if (result.ok) {
    const metrics = result.metrics;
    assert(metrics.electionDuration > 0, "Election duration should be positive");
    assert(metrics.electionDuration < 1000, "Election should complete within 1 second");
    assertEquals(metrics.candidateCount, 3, "Should have 3 candidates");
    assertEquals(metrics.winnerNodeId, "node-1", "Node-1 should become leader");
  }
});

// Test: Failover performance measurement
Deno.test("Performance: Failover time should be measured", async () => {
  // Setup cluster
  const cluster = new RaftCluster();
  await cluster.addNode("node-1", "localhost:5001");
  await cluster.addNode("node-2", "localhost:5002");
  await cluster.addNode("node-3", "localhost:5003");
  await cluster.start();
  
  const registry = new ServiceRegistryRaft(cluster);
  
  // Register some services
  for (let i = 0; i < 5; i++) {
    await registry.register({
      id: `service-${i}`,
      name: "api",
      host: "localhost",
      port: 8080 + i
    });
  }
  
  // Measure failover
  const result = await measureFailover(cluster, registry);
  
  assert(result.ok, "Failover measurement should succeed");
  if (result.ok) {
    const metrics = result.metrics;
    assert(metrics.failoverDuration > 0, "Failover duration should be positive");
    assert(metrics.failoverDuration < 5000, "Failover should complete within 5 seconds");
    assertEquals(metrics.previousLeaderId, "node-1", "Previous leader should be node-1");
    assertEquals(metrics.newLeaderId, "node-2", "New leader should be node-2");
    assertEquals(metrics.affectedServices, 5, "Should affect 5 services");
  }
  
  await cluster.stop();
});

// Test: Service availability during failures
Deno.test("Performance: Service availability should remain high during failures", async () => {
  const cluster = new RaftCluster();
  await cluster.addNode("node-1", "localhost:5001");
  await cluster.addNode("node-2", "localhost:5002");
  await cluster.addNode("node-3", "localhost:5003");
  await cluster.start();
  
  const registry = new ServiceRegistryRaft(cluster);
  
  // Measure availability for 2 seconds with 10% failure rate
  const result = await measureAvailability(cluster, registry, 2000, 0.1);
  
  assert(result.ok, "Availability measurement should succeed");
  if (result.ok) {
    const metrics = result.metrics;
    assert(metrics.totalRequests > 50, "Should have sufficient request samples");
    assert(
      metrics.availabilityPercentage > 95,
      `Availability should be >95%, got ${metrics.availabilityPercentage}%`
    );
    console.log(`Availability: ${metrics.availabilityPercentage.toFixed(2)}%`);
  }
  
  await cluster.stop();
});

// Test: Write performance measurement
Deno.test("Performance: Write latency and throughput should be measured", async () => {
  const cluster = new RaftCluster();
  await cluster.addNode("node-1", "localhost:5001");
  await cluster.addNode("node-2", "localhost:5002");
  await cluster.addNode("node-3", "localhost:5003");
  await cluster.start();
  
  const registry = new ServiceRegistryRaft(cluster);
  
  // Measure 100 write operations
  const result = await measureWritePerformance(cluster, registry, 100);
  
  assert(result.ok, "Write performance measurement should succeed");
  if (result.ok) {
    const metrics = result.metrics;
    assertEquals(metrics.operationCount, 100, "Should complete 100 operations");
    assert(metrics.averageLatency > 0, "Average latency should be positive");
    assert(metrics.throughput > 0, "Throughput should be positive");
    assert(metrics.minLatency <= metrics.averageLatency, "Min should be <= average");
    assert(metrics.maxLatency >= metrics.averageLatency, "Max should be >= average");
    
    console.log(`Write throughput: ${metrics.throughput.toFixed(2)} ops/sec`);
    console.log(`Average latency: ${metrics.averageLatency.toFixed(2)}ms`);
  }
  
  await cluster.stop();
});

// Test: Read performance measurement
Deno.test("Performance: Read latency and cache hit rate should be measured", async () => {
  const cluster = new RaftCluster();
  await cluster.addNode("node-1", "localhost:5001");
  await cluster.addNode("node-2", "localhost:5002");
  await cluster.addNode("node-3", "localhost:5003");
  await cluster.start();
  
  const registry = new ServiceRegistryRaft(cluster);
  
  // Measure 100 read operations
  const result = await measureReadPerformance(registry, 100);
  
  assert(result.ok, "Read performance measurement should succeed");
  if (result.ok) {
    const metrics = result.metrics;
    assertEquals(metrics.operationCount, 100, "Should complete 100 operations");
    assert(metrics.averageLatency > 0, "Average latency should be positive");
    assert(metrics.throughput > 0, "Throughput should be positive");
    assert(metrics.cacheHitRate >= 0 && metrics.cacheHitRate <= 100, 
      "Cache hit rate should be between 0-100%");
    
    console.log(`Read throughput: ${metrics.throughput.toFixed(2)} ops/sec`);
    console.log(`Cache hit rate: ${metrics.cacheHitRate.toFixed(2)}%`);
  }
  
  await cluster.stop();
});

// Test: Performance comparison with and without Raft
Deno.test("Performance: Raft overhead should be measured and acceptable", async () => {
  const result = await compareWithoutRaft(100);
  
  assert(result.ok, "Performance comparison should succeed");
  if (result.ok) {
    const comparison = result.comparison;
    
    assert(comparison.overheadPercentage > 0, 
      "Raft should add some overhead");
    assert(comparison.overheadPercentage < 200, 
      "Overhead should be less than 200%");
    
    console.log(`\nPerformance comparison:`);
    console.log(`Without Raft: ${comparison.withoutRaft.averageLatency.toFixed(2)}ms`);
    console.log(`With Raft: ${comparison.withRaft.averageLatency.toFixed(2)}ms`);
    console.log(`Overhead: ${comparison.overheadPercentage.toFixed(2)}%`);
    console.log(`Analysis: ${comparison.analysis}`);
  }
});

// Test: Error handling for insufficient nodes
Deno.test("Performance: Should handle insufficient nodes error", async () => {
  const result = await measureLeaderElection(2);
  
  assert(!result.ok, "Should fail with insufficient nodes");
  if (!result.ok) {
    assertEquals(result.error.type, "cluster_not_ready");
    assertEquals(result.error.requiredNodes, 3);
    assertEquals(result.error.activeNodes, 2);
  }
});

// Test: Validate measurement accuracy
Deno.test("Performance: Measurements should be statistically valid", async () => {
  const cluster = new RaftCluster();
  await cluster.addNode("node-1", "localhost:5001");
  await cluster.addNode("node-2", "localhost:5002");
  await cluster.addNode("node-3", "localhost:5003");
  await cluster.start();
  
  const registry = new ServiceRegistryRaft(cluster);
  
  // Perform multiple measurements
  const results: WritePerformanceResult[] = [];
  for (let i = 0; i < 5; i++) {
    const result = await measureWritePerformance(cluster, registry, 20);
    if (result.ok) {
      results.push(result);
    }
  }
  
  assertEquals(results.length, 5, "Should complete all measurement rounds");
  
  // Check consistency
  const latencies = results
    .filter(r => r.ok)
    .map(r => r.ok ? r.metrics.averageLatency : 0);
    
  const avgLatency = latencies.reduce((sum, l) => sum + l, 0) / latencies.length;
  const variance = latencies.reduce((sum, l) => sum + Math.pow(l - avgLatency, 2), 0) / latencies.length;
  const stdDev = Math.sqrt(variance);
  
  assert(stdDev < avgLatency * 0.5, 
    "Standard deviation should be less than 50% of average (consistent performance)");
  
  await cluster.stop();
});