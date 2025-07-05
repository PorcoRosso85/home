// Module exports following bin/docs conventions
// All public APIs exported from this single entry point

// Types
export type {
  LeaderElectionMetrics,
  FailoverMetrics,
  ServiceAvailabilityMetrics,
  WritePerformanceMetrics,
  ReadPerformanceMetrics,
  PerformanceComparison,
  LeaderElectionResult,
  FailoverResult,
  AvailabilityResult,
  WritePerformanceResult,
  ReadPerformanceResult,
  ComparisonResult
} from "./types/performance.ts";

// Core functions (pure, no side effects)
export {
  calculateAverage,
  calculateMinMax,
  calculateThroughput,
  calculateAvailability,
  analyzeLeaderElection,
  analyzeFailover,
  analyzeAvailability,
  analyzeWritePerformance,
  analyzeReadPerformance,
  comparePerformance,
  validateMeasurements
} from "./core/performance-analyzer.ts";

// Adapters (handle side effects)
export {
  measureLeaderElection,
  measureFailover,
  measureAvailability,
  measureWritePerformance,
  measureReadPerformance,
  compareWithoutRaft
} from "./adapters/raft-performance-measurer.ts";