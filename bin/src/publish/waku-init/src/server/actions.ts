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
import { createStorageAdapterFromEnv } from '../infrastructure/mod.js';

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
 * Create dependencies for the submit form use case using the new storage adapter system
 */
async function createSubmitFormDependencies(env: any): Promise<SubmitFormDependencies> {
  const storageAdapter = await createStorageAdapterFromEnv(env);
  
  return {
    storageService: {
      put: async (key: string, data: string, metadata?: any) => {
        await storageAdapter.save(key, data, metadata);
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
 * Alternative implementation using R2Adapter (cleaner abstraction):
 * 
 * function createSubmitFormDependenciesWithR2Adapter(bucket: any): SubmitFormDependencies {
 *   const storageAdapter = new R2Adapter(bucket);
 *   
 *   return {
 *     storageService: {
 *       put: async (key: string, data: string, metadata?: any) => {
 *         await storageAdapter.save(key, data, metadata);
 *       },
 *     },
 *     idGenerator: {
 *       generateSubmissionId: () => generateUUID(),
 *     },
 *     timeService: {
 *       now: () => new Date(),
 *     },
 *   };
 * }
 * 
 * Benefits of R2Adapter approach:
 * - Handles JSON stringification automatically
 * - Proper metadata formatting for R2 (httpMetadata/customMetadata)
 * - Implements StorageAdapter interface for testability
 * - Can be easily mocked or replaced with other storage backends
 * - Reusable across different use cases
 */

/**
 * Server action that accepts form data and stores it using the configured storage adapter
 * This is a thin adapter that delegates business logic to the use case
 */
export async function submitForm(formData: FormData): Promise<SubmissionResponse> {
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

    // Access the environment for storage adapter configuration
    const env = ctx.env as any;

    // Extract form data and convert to domain type
    // Note: This handles both FeedbackFormData and ContactFormData by accepting optional subject
    const feedbackFormData = {
      name: formData.get('name')?.toString() || '',
      email: formData.get('email')?.toString() || '',
      subject: formData.get('subject')?.toString() || '', // Optional for feedback forms
      message: formData.get('message')?.toString() || '',
    };

    // Create dependencies for the use case using the new storage adapter system
    const dependencies = await createSubmitFormDependencies(env);

    // Call the use case with form data and dependencies
    const result = await submitFormUseCase(feedbackFormData, dependencies);

    // Log success for monitoring
    if (result.success && result.filename) {
      console.log(`Successfully stored submission: ${result.filename}`);
    }

    return result;

  } catch (error) {
    console.error('Error in submitForm server action:', error);
    
    return {
      success: false,
      message: 'Failed to submit feedback. Please try again.'
    };
  }
}

/**
 * @deprecated Use submitForm instead. This is maintained for backward compatibility.
 * Will be removed in a future version.
 */
export async function submitToR2(formData: FormData): Promise<SubmissionResponse> {
  console.warn('submitToR2 is deprecated. Please use submitForm instead.');
  return submitForm(formData);
}