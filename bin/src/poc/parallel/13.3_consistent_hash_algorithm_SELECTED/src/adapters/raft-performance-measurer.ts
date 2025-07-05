// Adapter for measuring Raft performance - handles side effects
// Following bin/docs conventions: side effects isolated to adapters

import { RaftCluster, ServiceRegistryRaft, ServiceInfo } from "../../../raft/mod.ts";
import type {
  LeaderElectionResult,
  FailoverResult,
  AvailabilityResult,
  WritePerformanceResult,
  ReadPerformanceResult,
  ComparisonResult,
  MetricsMeasurement
} from "../types/performance.ts";
import {
  analyzeLeaderElection,
  analyzeFailover,
  analyzeAvailability,
  analyzeWritePerformance,
  analyzeReadPerformance,
  comparePerformance,
  validateMeasurements
} from "../core/performance-analyzer.ts";

// Measure leader election time
export async function measureLeaderElection(
  nodeCount: number
): Promise<LeaderElectionResult> {
  if (nodeCount < 3) {
    return {
      ok: false,
      error: {
        type: "cluster_not_ready",
        reason: "Minimum 3 nodes required for Raft cluster",
        requiredNodes: 3,
        activeNodes: nodeCount
      }
    };
  }

  const cluster = new RaftCluster();
  
  try {
    // Add nodes
    for (let i = 1; i <= nodeCount; i++) {
      await cluster.addNode(`node-${i}`, `localhost:${5000 + i}`);
    }
    
    const electionStartTime = performance.now();
    await cluster.start();
    
    // Wait for leader election
    let leader = cluster.getLeader();
    while (!leader) {
      await new Promise(resolve => setTimeout(resolve, 10));
      leader = cluster.getLeader();
    }
    
    const electionEndTime = performance.now();
    
    const metrics = analyzeLeaderElection(
      electionStartTime,
      electionEndTime,
      nodeCount,
      leader.getId()
    );
    
    await cluster.stop();
    
    return { ok: true, metrics };
  } catch (error) {
    await cluster.stop();
    return {
      ok: false,
      error: {
        type: "cluster_not_ready",
        reason: error instanceof Error ? error.message : "Unknown error",
        requiredNodes: nodeCount,
        activeNodes: 0
      }
    };
  }
}

// Measure failover time
export async function measureFailover(
  cluster: RaftCluster,
  registry: ServiceRegistryRaft
): Promise<FailoverResult> {
  const currentLeader = cluster.getLeader();
  if (!currentLeader) {
    return {
      ok: false,
      error: {
        type: "cluster_not_ready",
        reason: "No leader available",
        requiredNodes: 3,
        activeNodes: cluster.getNodes().length
      }
    };
  }
  
  try {
    // Count services before failure
    const servicesBefore = await registry.discover("");
    const affectedServices = servicesBefore.length;
    
    const previousLeaderId = currentLeader.getId();
    const failureDetectedTime = performance.now();
    
    // Stop current leader
    await currentLeader.stop();
    
    // Wait for new leader
    let newLeader = cluster.getLeader();
    while (!newLeader || newLeader.getId() === previousLeaderId) {
      await new Promise(resolve => setTimeout(resolve, 10));
      newLeader = cluster.getLeader();
    }
    
    const newLeaderElectedTime = performance.now();
    
    const metrics = analyzeFailover(
      failureDetectedTime,
      newLeaderElectedTime,
      previousLeaderId,
      newLeader.getId(),
      affectedServices
    );
    
    return { ok: true, metrics };
  } catch (error) {
    return {
      ok: false,
      error: {
        type: "measurement_error",
        reason: error instanceof Error ? error.message : "Unknown error",
        operation: "failover",
        timestamp: Date.now()
      }
    };
  }
}

// Measure service availability during failures
export async function measureAvailability(
  cluster: RaftCluster,
  registry: ServiceRegistryRaft,
  durationMs: number,
  failureRate: number = 0.1
): Promise<AvailabilityResult> {
  const requests: Array<{ success: boolean; timestamp: number }> = [];
  const startTime = Date.now();
  
  try {
    // Register test services
    for (let i = 0; i < 5; i++) {
      await registry.register({
        id: `test-service-${i}`,
        name: "api",
        host: "localhost",
        port: 8080 + i
      });
    }
    
    // Run availability test
    while (Date.now() - startTime < durationMs) {
      // Random node failures
      if (Math.random() < failureRate) {
        const nodes = cluster.getNodes().filter((n: any) => !n.isStopped());
        if (nodes.length > 1) {
          const randomNode = nodes[Math.floor(Math.random() * nodes.length)];
          await randomNode.stop();
        }
      }
      
      // Try to discover services
      const timestamp = Date.now();
      try {
        const services = await registry.discover("api");
        requests.push({ success: services.length > 0, timestamp });
      } catch {
        requests.push({ success: false, timestamp });
      }
      
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    if (requests.length < 10) {
      return {
        ok: false,
        error: {
          type: "insufficient_data",
          reason: "Not enough samples collected",
          requiredSamples: 10,
          actualSamples: requests.length
        }
      };
    }
    
    const metrics = analyzeAvailability(requests);
    return { ok: true, metrics };
  } catch (error) {
    return {
      ok: false,
      error: {
        type: "measurement_error",
        reason: error instanceof Error ? error.message : "Unknown error",
        operation: "availability",
        timestamp: Date.now()
      }
    };
  }
}

// Measure write performance
export async function measureWritePerformance(
  cluster: RaftCluster,
  registry: ServiceRegistryRaft,
  operationCount: number
): Promise<WritePerformanceResult> {
  const measurements: MetricsMeasurement[] = [];
  
  try {
    for (let i = 0; i < operationCount; i++) {
      const service: ServiceInfo = {
        id: `perf-test-${i}`,
        name: "api",
        host: "localhost",
        port: 9000 + i,
        metadata: { test: true }
      };
      
      const startTime = performance.now();
      await registry.register(service);
      const endTime = performance.now();
      
      measurements.push({
        timestamp: Date.now(),
        duration: endTime - startTime,
        operationType: "write"
      });
    }
    
    const validation = validateMeasurements(measurements);
    if (!validation.valid) {
      return {
        ok: false,
        error: {
          type: "measurement_error",
          reason: validation.reason || "Invalid measurements",
          operation: "write",
          timestamp: Date.now()
        }
      };
    }
    
    const metrics = analyzeWritePerformance(measurements);
    return { ok: true, metrics };
  } catch (error) {
    return {
      ok: false,
      error: {
        type: "measurement_error",
        reason: error instanceof Error ? error.message : "Unknown error",
        operation: "write",
        timestamp: Date.now()
      }
    };
  }
}

// Measure read performance
export async function measureReadPerformance(
  registry: ServiceRegistryRaft,
  operationCount: number
): Promise<ReadPerformanceResult> {
  const measurements: MetricsMeasurement[] = [];
  let cacheHits = 0;
  
  try {
    // Prepare test data
    await registry.register({
      id: "read-test",
      name: "api",
      host: "localhost",
      port: 8080
    });
    
    for (let i = 0; i < operationCount; i++) {
      const startTime = performance.now();
      const services = await registry.discover("api");
      const endTime = performance.now();
      
      measurements.push({
        timestamp: Date.now(),
        duration: endTime - startTime,
        operationType: "read"
      });
      
      // Simulate cache hit detection
      if (endTime - startTime < 1) {
        cacheHits++;
      }
    }
    
    const validation = validateMeasurements(measurements);
    if (!validation.valid) {
      return {
        ok: false,
        error: {
          type: "measurement_error",
          reason: validation.reason || "Invalid measurements",
          operation: "read",
          timestamp: Date.now()
        }
      };
    }
    
    const metrics = analyzeReadPerformance(measurements, cacheHits);
    return { ok: true, metrics };
  } catch (error) {
    return {
      ok: false,
      error: {
        type: "measurement_error",
        reason: error instanceof Error ? error.message : "Unknown error",
        operation: "read",
        timestamp: Date.now()
      }
    };
  }
}

// Compare performance with and without Raft
export async function compareWithoutRaft(
  operationCount: number
): Promise<ComparisonResult> {
  try {
    // Measure without Raft (simple Map)
    const simpleRegistry = new Map<string, ServiceInfo>();
    const withoutRaftMeasurements: MetricsMeasurement[] = [];
    
    for (let i = 0; i < operationCount; i++) {
      const service: ServiceInfo = {
        id: `simple-${i}`,
        name: "api",
        host: "localhost",
        port: 7000 + i
      };
      
      const startTime = performance.now();
      simpleRegistry.set(service.id, service);
      const endTime = performance.now();
      
      withoutRaftMeasurements.push({
        timestamp: Date.now(),
        duration: endTime - startTime,
        operationType: "write"
      });
    }
    
    // Measure with Raft
    const cluster = new RaftCluster();
    await cluster.addNode("node-1", "localhost:5001");
    await cluster.addNode("node-2", "localhost:5002");
    await cluster.addNode("node-3", "localhost:5003");
    await cluster.start();
    
    const registry = new ServiceRegistryRaft(cluster);
    const withRaftResult = await measureWritePerformance(cluster, registry, operationCount);
    
    await cluster.stop();
    
    if (!withRaftResult.ok) {
      return { ok: false, error: withRaftResult.error };
    }
    
    const withoutRaftMetrics = analyzeWritePerformance(withoutRaftMeasurements);
    const comparison = comparePerformance(withRaftResult.metrics, withoutRaftMetrics);
    
    return { ok: true, comparison };
  } catch (error) {
    return {
      ok: false,
      error: {
        type: "measurement_error",
        reason: error instanceof Error ? error.message : "Unknown error",
        operation: "comparison",
        timestamp: Date.now()
      }
    };
  }
}