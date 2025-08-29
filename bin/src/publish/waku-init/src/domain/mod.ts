/**
 * Domain Layer - Public API
 * 
 * Exports all public domain types for use by other layers.
 * This module serves as the single entry point to the domain layer.
 */

// Log Domain Types
export type {
  LogId,
  Timestamp,
  UnixTimestamp,
  LogType,
  LogVersion,
  LogEntry,
  FormSubmissionLogData,
  FormSubmissionLogEntry,
  LogProcessingResult,
  BatchProcessingResult,
  LogAggregationConfig,
} from './log/types';

// Form Domain Types
export type {
  SubmissionId,
  EmailAddress,
  SubmissionStatus,
  BaseFormData,
  FeedbackFormData,
  ContactFormData,
  SubmissionData,
  SubmissionResponse,
  FormValidationError,
  FormValidationResult,
  SubmissionMetadata,
  FormStorageConfig,
} from './form/types';

// Analytics Domain Types
export type {
  ChartValue,
  HexColor,
  ChartLabel,
  ChartIndex,
  DataPoint,
  DonutChartConfig,
  ChartSegment,
  ChartInteractionState,
  ChartDimensions,
  DataAggregation,
  ChartTheme,
  ChartLegend,
  ChartConfiguration,
  ChartDataValidation,
} from './analytics/types';

/**
 * Re-export Timestamp type with alias to avoid conflicts
 * between log and form domains
 */
export type { Timestamp as FormTimestamp } from './form/types';