import type {
  LogId,
  UnixTimestamp,
  FormSubmissionLogEntry,
  FormSubmissionLogData,
  FeedbackFormData,
} from '../../domain/mod.js';

/**
 * Dependencies required by the save log use case
 */
export interface SaveLogDependencies {
  /**
   * Logging service for persisting log entries
   */
  logger: {
    log: (message: string) => void;
  };
  /**
   * ID generation service
   */
  idGenerator: {
    generateLogId: () => LogId;
  };
  /**
   * Time service
   */
  timeService: {
    now: () => Date;
    unixTimestamp: () => UnixTimestamp;
  };
}

/**
 * Response from saving a log entry
 */
export interface SaveLogResponse {
  success: boolean;
  message: string;
  logId?: LogId;
}

/**
 * Create form submission log data from form input
 */
function createFormSubmissionLogData(
  formData: FeedbackFormData,
  logId: LogId,
  timestamp: Date
): FormSubmissionLogData {
  return {
    id: logId,
    name: formData.name || '',
    email: formData.email || '',
    subject: formData.subject || '',
    message: formData.message || '',
    submittedAt: timestamp.toISOString(),
  };
}

/**
 * Create complete log entry for form submission
 */
function createFormSubmissionLogEntry(
  formData: FeedbackFormData,
  dependencies: SaveLogDependencies
): FormSubmissionLogEntry {
  const logId = dependencies.idGenerator.generateLogId();
  const timestamp = dependencies.timeService.now();
  const unixTimestamp = dependencies.timeService.unixTimestamp();

  const logData = createFormSubmissionLogData(formData, logId, timestamp);

  return {
    type: 'form_submission',
    version: 1,
    timestamp: unixTimestamp,
    data: logData,
  };
}

/**
 * Save Log Use Case
 * 
 * Handles the business logic for logging form submissions:
 * - Creates structured log entries
 * - Generates unique log IDs and timestamps
 * - Logs to the configured logging service
 * - Returns appropriate response with log ID
 */
export async function saveLogUseCase(
  formData: FeedbackFormData,
  dependencies: SaveLogDependencies
): Promise<SaveLogResponse> {
  try {
    // Create structured log entry
    const logEntry = createFormSubmissionLogEntry(formData, dependencies);

    // Convert to JSON string for logging
    const logMessage = JSON.stringify(logEntry);

    // Log to the configured logging service
    dependencies.logger.log(logMessage);

    return {
      success: true,
      message: 'Submission logged',
      logId: logEntry.data.id,
    };

  } catch (error) {
    console.error('Error in saveLogUseCase:', error);
    
    return {
      success: false,
      message: 'Failed to log submission',
    };
  }
}