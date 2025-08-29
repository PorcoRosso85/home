/**
 * Application Layer - Public API
 * 
 * Exports all public use cases for use by the infrastructure layer (server actions).
 * This module serves as the single entry point to the application layer.
 * 
 * Use cases encapsulate business logic and orchestrate domain objects.
 * They accept dependencies as parameters (dependency injection pattern)
 * to maintain testability and decoupling from infrastructure concerns.
 */

// Form Use Cases
export {
  submitFormUseCase,
  type SubmitFormDependencies,
} from './form/submit-form-use-case.js';

// Log Use Cases
export {
  saveLogUseCase,
  type SaveLogDependencies,
  type SaveLogResponse,
} from './log/save-log-use-case.js';

export {
  batchProcessLogsUseCase,
  getBatchProcessingStatusUseCase,
  type BatchProcessLogsDependencies,
} from './log/batch-process-logs-use-case.js';

/**
 * Re-export batch processing use case functions with clearer names
 */
export { 
  batchProcessLogsUseCase as batchProcessLogs,
  getBatchProcessingStatusUseCase as getBatchProcessingStatus,
} from './log/batch-process-logs-use-case.js';