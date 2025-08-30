import type {
  SubmissionData,
  SubmissionResponse,
  FormValidationResult,
  FormValidationError,
  FeedbackFormData,
  SubmissionId,
} from '../../domain/mod.js';

/**
 * Dependencies required by the submit form use case
 */
export interface SubmitFormDependencies {
  /**
   * Storage service for persisting form submissions
   */
  storageService: {
    put: (key: string, data: string, metadata?: Record<string, any>) => Promise<void>;
  };
  /**
   * ID generation service
   */
  idGenerator: {
    generateSubmissionId: () => SubmissionId;
  };
  /**
   * Time service
   */
  timeService: {
    now: () => Date;
  };
}

/**
 * Form validation utilities
 * Handles both FeedbackFormData and ContactFormData by accepting optional subject
 */
function validateFormData(data: FeedbackFormData & { subject?: string }): FormValidationResult {
  const errors: FormValidationError[] = [];

  if (!data.name?.trim()) {
    errors.push({ field: 'name', message: 'Name is required' });
  }

  if (!data.email?.trim()) {
    errors.push({ field: 'email', message: 'Email is required' });
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.push({ field: 'email', message: 'Email format is invalid' });
  }

  // Subject validation is optional - only validate if provided
  // This allows the same function to handle both feedback and contact forms
  if (data.subject !== undefined && !data.subject?.trim()) {
    errors.push({ field: 'subject', message: 'Subject is required' });
  }

  if (!data.message?.trim()) {
    errors.push({ field: 'message', message: 'Message is required' });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Generate storage path for submission data
 */
function generateStoragePath(timestamp: Date, submissionId: SubmissionId): string {
  const year = timestamp.getFullYear();
  const month = (timestamp.getMonth() + 1).toString().padStart(2, '0');
  const day = timestamp.getDate().toString().padStart(2, '0');
  const isoTimestamp = timestamp.toISOString().replace(/[:.]/g, '-').slice(0, -5);
  
  return `submissions/${year}/${month}/${day}/${isoTimestamp}-${submissionId}.json`;
}

/**
 * Submit Form Use Case
 * 
 * Handles the business logic for submitting feedback forms:
 * - Validates form data
 * - Generates submission ID and timestamp
 * - Stores submission data with proper metadata
 * - Returns appropriate response
 * 
 * Works with both FeedbackFormData and ContactFormData by accepting optional subject
 */
export async function submitFormUseCase(
  formData: FeedbackFormData & { subject?: string },
  dependencies: SubmitFormDependencies
): Promise<SubmissionResponse> {
  try {
    // Validate form data
    const validation = validateFormData(formData);
    if (!validation.isValid) {
      return {
        success: false,
        message: validation.errors.map(err => err.message).join(', '),
      };
    }

    // Generate submission metadata
    const timestamp = dependencies.timeService.now();
    const submissionId = dependencies.idGenerator.generateSubmissionId();

    // Create submission data
    const submissionData: SubmissionData = {
      name: formData.name.trim(),
      email: formData.email.trim(),
      subject: (formData.subject || '').trim(), // Default to empty string for feedback forms
      message: formData.message.trim(),
      timestamp: timestamp.toISOString(),
      submissionId,
    };

    // Generate storage path
    const storageKey = generateStoragePath(timestamp, submissionId);

    // Prepare JSON data
    const jsonData = JSON.stringify(submissionData, null, 2);

    // Store in storage service
    await dependencies.storageService.put(storageKey, jsonData, {
      httpMetadata: {
        contentType: 'application/json',
        contentEncoding: 'utf-8',
      },
      customMetadata: {
        submissionId,
        submittedAt: timestamp.toISOString(),
        name: submissionData.name,
        email: submissionData.email,
        subject: submissionData.subject,
      },
    });

    return {
      success: true,
      message: 'Feedback submitted successfully!',
      filename: storageKey,
    };

  } catch (error) {
    console.error('Error in submitFormUseCase:', error);
    
    return {
      success: false,
      message: 'Failed to submit feedback. Please try again.',
    };
  }
}