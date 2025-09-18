/**
 * Example: Using MultiAdapter for Redundant Storage
 * 
 * This file demonstrates how to integrate MultiAdapter with the existing
 * server actions to provide redundant storage across multiple backends.
 */

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
import { MultiAdapter, R2Adapter, LogAdapter } from '../infrastructure/mod.js';

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
 * Create dependencies with MultiAdapter for redundant storage
 * 
 * This setup saves to both R2 and logs simultaneously:
 * - Primary: R2 for persistent storage
 * - Secondary: LogAdapter for debugging/monitoring
 * - If R2 fails, operation continues with logs
 * - If both fail, operation fails with detailed error
 */
function createMultiStorageDependencies(bucket: any): SubmitFormDependencies {
  // Create individual storage adapters
  const r2Storage = new R2Adapter(bucket);
  const logStorage = new LogAdapter();
  
  // Create multi-adapter for redundancy
  const multiStorage = new MultiAdapter([r2Storage, logStorage]);
  
  return {
    storageService: {
      put: async (key: string, data: string, metadata?: any) => {
        // MultiAdapter handles the redundant saving
        await multiStorage.save(key, data, metadata);
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
 * Alternative: Three-way redundancy example
 * 
 * For critical applications, you might want to save to multiple systems:
 * - R2 for primary storage
 * - LogAdapter for development debugging  
 * - Another R2 bucket for backup (if available)
 */
function createTripleRedundancyDependencies(
  primaryBucket: any, 
  backupBucket?: any
): SubmitFormDependencies {
  const adapters = [
    new R2Adapter(primaryBucket),
    new LogAdapter(),
  ];
  
  // Add backup R2 if available
  if (backupBucket) {
    adapters.push(new R2Adapter(backupBucket));
  }
  
  const multiStorage = new MultiAdapter(adapters);
  
  return {
    storageService: {
      put: async (key: string, data: string, metadata?: any) => {
        await multiStorage.save(key, data, metadata);
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
 * Server action with redundant storage
 * 
 * Same interface as the original submitToR2, but with redundant storage.
 * Falls back gracefully if primary storage (R2) fails.
 */
export async function submitWithRedundancy(formData: FormData): Promise<SubmissionResponse> {
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
      message: formData.get('message')?.toString() || '',
    };

    // Create dependencies with multi-storage support
    const dependencies = createMultiStorageDependencies(bucket);

    // Call the use case with form data and dependencies
    const result = await submitFormUseCase(feedbackFormData, dependencies);

    // Enhanced logging for multi-storage monitoring
    if (result.success && result.filename) {
      console.log(`Successfully stored submission with redundancy: ${result.filename}`);
    }

    return result;

  } catch (error) {
    console.error('Error in submitWithRedundancy server action:', error);
    
    return {
      success: false,
      message: 'Failed to submit feedback. Please try again.'
    };
  }
}

/**
 * Development-only server action that uses only LogAdapter
 * 
 * Useful for testing form workflows without R2 dependency.
 */
export async function submitToLogs(formData: FormData): Promise<SubmissionResponse> {
  try {
    // Extract form data
    const feedbackFormData: FeedbackFormData = {
      name: formData.get('name')?.toString() || '',
      email: formData.get('email')?.toString() || '',
      message: formData.get('message')?.toString() || '',
    };

    // Create log-only dependencies
    const logStorage = new LogAdapter();
    const dependencies: SubmitFormDependencies = {
      storageService: {
        put: async (key: string, data: string, metadata?: any) => {
          await logStorage.save(key, data, metadata);
        },
      },
      idGenerator: {
        generateSubmissionId: () => generateUUID(),
      },
      timeService: {
        now: () => new Date(),
      },
    };

    // Call the use case
    const result = await submitFormUseCase(feedbackFormData, dependencies);

    console.log('Development submission logged:', result.filename);
    return result;

  } catch (error) {
    console.error('Error in submitToLogs:', error);
    
    return {
      success: false,
      message: 'Failed to log submission. Please check console.'
    };
  }
}

/**
 * Usage Examples:
 * 
 * 1. Replace existing submitToR2 with submitWithRedundancy for production
 * 2. Use submitToLogs for development/testing
 * 3. Customize createMultiStorageDependencies for your specific needs
 * 4. Monitor console logs to see which adapters succeed/fail
 * 
 * Benefits:
 * - Data redundancy (saves to multiple places)
 * - Graceful degradation (continues if some storage fails)
 * - Enhanced monitoring (detailed logging of storage operations)
 * - Easy to test (can mix real and mock storage adapters)
 */