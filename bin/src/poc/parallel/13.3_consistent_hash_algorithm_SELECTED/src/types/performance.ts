// Performance measurement types following bin/docs conventions
// No generic Result types, specific success/error types for each operation

export interface MetricsMeasurement {
  timestamp: number;
  duration: number;
  operationType: string;
}

export interface LeaderElectionMetrics {
  electionStartTime: number;
  electionEndTime: number;
  electionDuration: number;
  candidateCount: number;
  winnerNodeId: string;
}

export interface FailoverMetrics {
  failureDetectedTime: number;
  newLeaderElectedTime: number;
  failoverDuration: number;
  previousLeaderId: string;
  newLeaderId: string;
  affectedServices: number;
}

export interface ServiceAvailabilityMetrics {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  availabilityPercentage: number;
  measurementDuration: number;
}

export interface WritePerformanceMetrics {
  operationCount: number;
  totalDuration: number;
  averageLatency: number;
  minLatency: number;
  maxLatency: number;
  throughput: number; // operations per second
}

export interface ReadPerformanceMetrics {
  operationCount: number;
  totalDuration: number;
  averageLatency: number;
  cacheHitRate: number;
  throughput: number;
}

export interface NodeFailureImpact {
  nodeId: string;
  failureTime: number;
  recoveryTime: number;
  lostServices: number;
  redistributedServices: number;
  downtime: number;
}

// Error types for performance measurements
export interface MeasurementError {
  type: "measurement_error";
  reason: string;
  operation: string;
  timestamp: number;
}

export interface ClusterNotReadyError {
  type: "cluster_not_ready";
  reason: string;
  requiredNodes: number;
  activeNodes: number;
}

export interface InsufficientDataError {
  type: "insufficient_data";
  reason: string;
  requiredSamples: number;
  actualSamples: number;
}

// Measurement results following error-as-value pattern
export type LeaderElectionResult = 
  | { ok: true; metrics: LeaderElectionMetrics }
  | { ok: false; error: ClusterNotReadyError };

export type FailoverResult =
  | { ok: true; metrics: FailoverMetrics }
  | { ok: false; error: ClusterNotReadyError | MeasurementError };

export type AvailabilityResult =
  | { ok: true; metrics: ServiceAvailabilityMetrics }
  | { ok: false; error: MeasurementError | InsufficientDataError };

export type WritePerformanceResult =
  | { ok: true; metrics: WritePerformanceMetrics }
  | { ok: false; error: MeasurementError };

export type ReadPerformanceResult =
  | { ok: true; metrics: ReadPerformanceMetrics }
  | { ok: false; error: MeasurementError };

// Performance comparison types
export interface PerformanceComparison {
  withRaft: WritePerformanceMetrics | ReadPerformanceMetrics;
  withoutRaft: WritePerformanceMetrics | ReadPerformanceMetrics;
  overheadPercentage: number;
  analysis: string;
}

export type ComparisonResult =
  | { ok: true; comparison: PerformanceComparison }
  | { ok: false; error: MeasurementError };