'use server';

import { getHonoContext } from '../../waku.hono-enhancer';
import { 
  submitFormUseCase,
  type SubmitFormDependencies 
} from '../application/mod.js';
import type { 
  SubmissionResponse, 
  FeedbackFormData, 
  SubmissionId 
} from '../domain/mod.js';

/**
 * Generates a UUID v4 string
 */
function generateUUID(): SubmissionId {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  }) as SubmissionId;
}

/**
 * Create dependencies for the submit form use case
 */
function createSubmitFormDependencies(bucket: any): SubmitFormDependencies {
  return {
    storageService: {
      put: async (key: string, data: string, metadata?: any) => {
        await bucket.put(key, data, metadata);
      },
    },
    idGenerator: {
      generateSubmissionId: () => generateUUID(),
    },
    timeService: {
      now: () => new Date(),
    },
  };
}

/**
 * Server action that accepts form data and stores it as JSON in R2
 * This is a thin adapter that delegates business logic to the use case
 */
export async function submitToR2(formData: FormData): Promise<SubmissionResponse> {
  try {
    // Get Hono context to access Cloudflare bindings
    const ctx = getHonoContext();
    
    if (!ctx) {
      console.error('Failed to get Hono context');
      return {
        success: false,
        message: 'Server configuration error'
      };
    }

    // Access the R2 bucket from Cloudflare environment
    const env = ctx.env as any;
    const bucket = env.DATA_BUCKET;
    
    if (!bucket) {
      console.error('R2 bucket not found in environment');
      return {
        success: false,
        message: 'Storage service not available'
      };
    }

    // Extract form data and convert to domain type
    const feedbackFormData: FeedbackFormData = {
      name: formData.get('name')?.toString() || '',
      email: formData.get('email')?.toString() || '',
      subject: formData.get('subject')?.toString() || '',
      message: formData.get('message')?.toString() || '',
    };

    // Create dependencies for the use case
    const dependencies = createSubmitFormDependencies(bucket);

    // Call the use case with form data and dependencies
    const result = await submitFormUseCase(feedbackFormData, dependencies);

    // Log success for monitoring
    if (result.success && result.filename) {
      console.log(`Successfully stored submission: ${result.filename}`);
    }

    return result;

  } catch (error) {
    console.error('Error in submitToR2 server action:', error);
    
    return {
      success: false,
      message: 'Failed to submit feedback. Please try again.'
    };
  }
}