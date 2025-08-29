import type {
  SubmissionData,
  SubmissionResponse,
  FormValidationResult,
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
 */
function validateFormData(data: FeedbackFormData): FormValidationResult {
  const errors: string[] = [];

  if (!data.name?.trim()) {
    errors.push('Name is required');
  }

  if (!data.email?.trim()) {
    errors.push('Email is required');
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.push('Email format is invalid');
  }

  if (!data.subject?.trim()) {
    errors.push('Subject is required');
  }

  if (!data.message?.trim()) {
    errors.push('Message is required');
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
 */
export async function submitFormUseCase(
  formData: FeedbackFormData,
  dependencies: SubmitFormDependencies
): Promise<SubmissionResponse> {
  try {
    // Validate form data
    const validation = validateFormData(formData);
    if (!validation.isValid) {
      return {
        success: false,
        message: validation.errors.join(', '),
      };
    }

    // Generate submission metadata
    const timestamp = dependencies.timeService.now();
    const submissionId = dependencies.idGenerator.generateSubmissionId();

    // Create submission data
    const submissionData: SubmissionData = {
      name: formData.name.trim(),
      email: formData.email.trim(),
      subject: formData.subject.trim(),
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