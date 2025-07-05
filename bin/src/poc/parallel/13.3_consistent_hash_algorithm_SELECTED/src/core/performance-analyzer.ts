// Core performance analysis functions - pure functions without side effects
// Following bin/docs conventions: data and processing separation

import type {
  LeaderElectionMetrics,
  FailoverMetrics,
  ServiceAvailabilityMetrics,
  WritePerformanceMetrics,
  ReadPerformanceMetrics,
  MetricsMeasurement,
  PerformanceComparison
} from "../types/performance.ts";

// Calculate average from array of numbers
export function calculateAverage(values: number[]): number {
  if (values.length === 0) return 0;
  const sum = values.reduce((acc, val) => acc + val, 0);
  return sum / values.length;
}

// Calculate min/max from array of numbers
export function calculateMinMax(values: number[]): { min: number; max: number } {
  if (values.length === 0) return { min: 0, max: 0 };
  return {
    min: Math.min(...values),
    max: Math.max(...values)
  };
}

// Calculate throughput (operations per second)
export function calculateThroughput(operationCount: number, durationMs: number): number {
  if (durationMs === 0) return 0;
  return (operationCount / durationMs) * 1000;
}

// Calculate availability percentage
export function calculateAvailability(
  successfulRequests: number,
  totalRequests: number
): number {
  if (totalRequests === 0) return 0;
  return (successfulRequests / totalRequests) * 100;
}

// Analyze leader election performance
export function analyzeLeaderElection(
  electionStartTime: number,
  electionEndTime: number,
  candidateCount: number,
  winnerNodeId: string
): LeaderElectionMetrics {
  return {
    electionStartTime,
    electionEndTime,
    electionDuration: electionEndTime - electionStartTime,
    candidateCount,
    winnerNodeId
  };
}

// Analyze failover performance
export function analyzeFailover(
  failureDetectedTime: number,
  newLeaderElectedTime: number,
  previousLeaderId: string,
  newLeaderId: string,
  affectedServices: number
): FailoverMetrics {
  return {
    failureDetectedTime,
    newLeaderElectedTime,
    failoverDuration: newLeaderElectedTime - failureDetectedTime,
    previousLeaderId,
    newLeaderId,
    affectedServices
  };
}

// Analyze service availability during failures
export function analyzeAvailability(
  requests: Array<{ success: boolean; timestamp: number }>
): ServiceAvailabilityMetrics {
  const totalRequests = requests.length;
  const successfulRequests = requests.filter(r => r.success).length;
  const failedRequests = totalRequests - successfulRequests;
  
  const startTime = requests[0]?.timestamp || 0;
  const endTime = requests[requests.length - 1]?.timestamp || 0;
  const measurementDuration = endTime - startTime;
  
  return {
    totalRequests,
    successfulRequests,
    failedRequests,
    availabilityPercentage: calculateAvailability(successfulRequests, totalRequests),
    measurementDuration
  };
}

// Analyze write performance
export function analyzeWritePerformance(
  measurements: MetricsMeasurement[]
): WritePerformanceMetrics {
  const latencies = measurements.map(m => m.duration);
  const { min, max } = calculateMinMax(latencies);
  const totalDuration = measurements.reduce((sum, m) => sum + m.duration, 0);
  
  return {
    operationCount: measurements.length,
    totalDuration,
    averageLatency: calculateAverage(latencies),
    minLatency: min,
    maxLatency: max,
    throughput: calculateThroughput(measurements.length, totalDuration)
  };
}

// Analyze read performance
export function analyzeReadPerformance(
  measurements: MetricsMeasurement[],
  cacheHits: number
): ReadPerformanceMetrics {
  const latencies = measurements.map(m => m.duration);
  const totalDuration = measurements.reduce((sum, m) => sum + m.duration, 0);
  
  return {
    operationCount: measurements.length,
    totalDuration,
    averageLatency: calculateAverage(latencies),
    cacheHitRate: measurements.length > 0 ? (cacheHits / measurements.length) * 100 : 0,
    throughput: calculateThroughput(measurements.length, totalDuration)
  };
}

// Compare performance with and without Raft
export function comparePerformance(
  withRaft: WritePerformanceMetrics | ReadPerformanceMetrics,
  withoutRaft: WritePerformanceMetrics | ReadPerformanceMetrics
): PerformanceComparison {
  const overheadPercentage = withoutRaft.averageLatency > 0
    ? ((withRaft.averageLatency / withoutRaft.averageLatency - 1) * 100)
    : 0;
  
  const analysis = analyzeOverhead(overheadPercentage, withRaft, withoutRaft);
  
  return {
    withRaft,
    withoutRaft,
    overheadPercentage,
    analysis
  };
}

// Analyze performance overhead
function analyzeOverhead(
  overheadPercentage: number,
  withRaft: WritePerformanceMetrics | ReadPerformanceMetrics,
  withoutRaft: WritePerformanceMetrics | ReadPerformanceMetrics
): string {
  const analysis: string[] = [];
  
  if (overheadPercentage > 0) {
    analysis.push(`Raft adds ${overheadPercentage.toFixed(2)}% latency overhead`);
  }
  
  const throughputReduction = withoutRaft.throughput > 0
    ? ((1 - withRaft.throughput / withoutRaft.throughput) * 100)
    : 0;
    
  if (throughputReduction > 0) {
    analysis.push(`Throughput reduced by ${throughputReduction.toFixed(2)}%`);
  }
  
  if (overheadPercentage < 50) {
    analysis.push("Overhead is acceptable for high availability benefits");
  } else if (overheadPercentage < 100) {
    analysis.push("Moderate overhead - consider optimization");
  } else {
    analysis.push("High overhead - investigate bottlenecks");
  }
  
  return analysis.join(". ");
}

// Validate measurement data
export function validateMeasurements(
  measurements: MetricsMeasurement[]
): { valid: boolean; reason?: string } {
  if (measurements.length === 0) {
    return { valid: false, reason: "No measurements provided" };
  }
  
  const invalidMeasurements = measurements.filter(
    m => m.duration < 0 || !m.timestamp || !m.operationType
  );
  
  if (invalidMeasurements.length > 0) {
    return { 
      valid: false, 
      reason: `${invalidMeasurements.length} invalid measurements found` 
    };
  }
  
  return { valid: true };
}