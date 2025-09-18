'use server';

import {
  saveLogUseCase,
  batchProcessLogsUseCase,
  type SaveLogDependencies,
  type SaveLogResponse,
  type BatchProcessLogsDependencies,
} from '../application/mod.js';
import type { 
  FeedbackFormData, 
  LogId, 
  BatchProcessingResult 
} from '../domain/mod.js';

/**
 * Create dependencies for the save log use case
 */
function createSaveLogDependencies(): SaveLogDependencies {
  return {
    logger: {
      log: (message: string) => {
        // Direct log to Cloudflare Logs (no KV needed)
        console.log(message);
      },
    },
    idGenerator: {
      generateLogId: () => crypto.randomUUID() as LogId,
    },
    timeService: {
      now: () => new Date(),
      unixTimestamp: () => Date.now(),
    },
  };
}

/**
 * Simplified log-based form submission
 * This is a thin adapter that delegates business logic to the use case
 */
export async function submitAsLog(formData: FormData): Promise<SaveLogResponse> {
  try {
    // Extract form data and convert to domain type
    const feedbackFormData: FeedbackFormData = {
      name: formData.get('name')?.toString() || '',
      email: formData.get('email')?.toString() || '',
      subject: formData.get('subject')?.toString() || '',
      message: formData.get('message')?.toString() || '',
    };

    // Create dependencies for the use case
    const dependencies = createSaveLogDependencies();

    // Call the use case with form data and dependencies
    const result = await saveLogUseCase(feedbackFormData, dependencies);

    return result;

  } catch (error) {
    console.error('Error in submitAsLog server action:', error);
    
    return {
      success: false,
      message: 'Failed to log submission',
    };
  }
}

/**
 * Create dependencies for the batch process logs use case
 */
function createBatchProcessLogsDependencies(): BatchProcessLogsDependencies {
  return {
    logger: {
      log: (message: string) => {
        console.log(message);
      },
    },
    config: {
      provider: 'cloudflare-logpush',
      destination: 'Configured via Cloudflare Dashboard',
    },
  };
}

/**
 * Batch processing is handled by Cloudflare Logpush
 * This is a thin adapter that delegates to the use case
 */
export async function batchProcessLogs(): Promise<BatchProcessingResult> {
  try {
    // Create dependencies for the use case
    const dependencies = createBatchProcessLogsDependencies();

    // Call the use case
    const result = await batchProcessLogsUseCase(dependencies);

    return result;

  } catch (error) {
    console.error('Error in batchProcessLogs server action:', error);
    
    return {
      processed: 0,
      outputKey: 'Error occurred during batch processing',
    };
  }
}