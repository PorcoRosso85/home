/**
 * Form Domain Types
 * 
 * Pure domain types for form functionality.
 * No dependencies on infrastructure or presentation layers.
 */

/**
 * Unique identifier for form submissions
 */
export type SubmissionId = string;

/**
 * ISO 8601 timestamp string
 */
export type Timestamp = string;

/**
 * Email address string (format validation handled at boundaries)
 */
export type EmailAddress = string;

/**
 * Form submission status
 */
export type SubmissionStatus = 'idle' | 'submitting' | 'success' | 'error';

/**
 * Base interface for all form data
 */
export interface BaseFormData {
  /** Submitter's name */
  name: string;
  /** Submitter's email address */
  email: EmailAddress;
  /** Message content */
  message: string;
}

/**
 * Feedback form specific data
 */
export interface FeedbackFormData extends BaseFormData {
  // Feedback forms don't require subject field
}

/**
 * Contact form specific data
 */
export interface ContactFormData extends BaseFormData {
  /** Subject or inquiry type */
  subject: string;
}

/**
 * Submitted form data with metadata
 */
export interface SubmissionData {
  /** Submission identifier */
  submissionId: SubmissionId;
  /** Submitter's name */
  name: string;
  /** Submitter's email address */
  email: EmailAddress;
  /** Subject (may be empty for feedback forms) */
  subject: string;
  /** Message content */
  message: string;
  /** ISO timestamp when submitted */
  timestamp: Timestamp;
}

/**
 * Form submission response
 */
export interface SubmissionResponse {
  /** Whether submission was successful */
  success: boolean;
  /** Human-readable message */
  message: string;
  /** Generated filename or storage key (optional) */
  filename?: string;
}

/**
 * Form validation error
 */
export interface FormValidationError {
  /** Field name that failed validation */
  field: keyof BaseFormData | 'subject';
  /** Error message */
  message: string;
}

/**
 * Form validation result
 */
export interface FormValidationResult {
  /** Whether validation passed */
  isValid: boolean;
  /** List of validation errors */
  errors: FormValidationError[];
}

/**
 * Form submission metadata
 */
export interface SubmissionMetadata {
  /** Submission identifier */
  submissionId: SubmissionId;
  /** When submission was made */
  submittedAt: Timestamp;
  /** Submitter's name for metadata */
  name: string;
  /** Submitter's email for metadata */
  email: EmailAddress;
  /** Subject for metadata */
  subject: string;
}

/**
 * Storage configuration for form submissions
 */
export interface FormStorageConfig {
  /** Storage path pattern */
  pathPattern: string;
  /** Content type for stored files */
  contentType: 'application/json';
  /** Character encoding */
  encoding: 'utf-8';
  /** Whether to include metadata */
  includeMetadata: boolean;
}