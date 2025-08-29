/**
 * Log Domain Types
 * 
 * Pure domain types for logging functionality.
 * No dependencies on infrastructure or presentation layers.
 */

/**
 * Unique identifier for a log entry
 */
export type LogId = string;

/**
 * ISO 8601 timestamp string
 */
export type Timestamp = string;

/**
 * Unix timestamp in milliseconds
 */
export type UnixTimestamp = number;

/**
 * Log entry types supported by the system
 */
export type LogType = 'form_submission' | 'user_action' | 'system_event' | 'error';

/**
 * Version number for log entry schema
 */
export type LogVersion = number;

/**
 * Core log entry structure
 */
export interface LogEntry {
  /** Type of log entry */
  type: LogType;
  /** Schema version for backward compatibility */
  version: LogVersion;
  /** Unix timestamp when log was created */
  timestamp: UnixTimestamp;
  /** Unique identifier for this log entry */
  id: LogId;
  /** Log entry payload data */
  data: unknown;
}

/**
 * Form submission log entry data
 */
export interface FormSubmissionLogData {
  /** Unique submission identifier */
  id: LogId;
  /** Submitter's name */
  name: string;
  /** Submitter's email address */
  email: string;
  /** Form subject or title */
  subject: string;
  /** Form message content */
  message: string;
  /** ISO timestamp when form was submitted */
  submittedAt: Timestamp;
}

/**
 * Strongly-typed form submission log entry
 */
export interface FormSubmissionLogEntry extends Omit<LogEntry, 'data'> {
  type: 'form_submission';
  data: FormSubmissionLogData;
}

/**
 * Log processing result
 */
export interface LogProcessingResult {
  /** Whether processing was successful */
  success: boolean;
  /** Human-readable message */
  message: string;
  /** Log ID that was processed */
  logId?: LogId;
}

/**
 * Batch processing result
 */
export interface BatchProcessingResult {
  /** Number of logs processed */
  processed: number;
  /** Output location or key */
  outputKey: string;
}

/**
 * Log aggregation configuration
 */
export interface LogAggregationConfig {
  /** Batch size for processing */
  batchSize: number;
  /** Time window for aggregation in milliseconds */
  timeWindowMs: number;
  /** Output format */
  outputFormat: 'json' | 'jsonl' | 'csv';
}