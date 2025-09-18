/**
 * Storage Adapter Factory
 * 
 * Factory function for creating storage adapters based on environment configuration.
 * Enables environment-based storage configuration without code changes.
 */

import { getEnv } from '../../lib/waku.js';
import type { StorageAdapter } from '../../domain/storage/types.js';
import { R2Adapter } from './r2-adapter.js';
import { LogAdapter } from './log-adapter.js';
import { MultiAdapter } from './multi-adapter.js';

/**
 * Valid storage types for the STORAGE_TYPE environment variable
 */
export type StorageType = 'r2' | 'log' | 'multi';

/**
 * Default storage type when STORAGE_TYPE is not set
 */
const DEFAULT_STORAGE_TYPE: StorageType = 'r2';

/**
 * Options for creating storage adapters
 */
export interface CreateStorageAdapterOptions {
  /** R2 bucket instance - required for R2 and Multi adapters */
  bucket?: any;
  /** Override storage type (defaults to STORAGE_TYPE environment variable) */
  storageType?: StorageType;
}

/**
 * Get the current storage type from environment configuration
 * 
 * @returns The configured storage type, defaults to 'r2' if not set or invalid
 */
export function getStorageType(): StorageType {
  const envStorageType = getEnv('STORAGE_TYPE')?.toLowerCase();
  
  // Validate the environment value
  if (envStorageType === 'r2' || envStorageType === 'log' || envStorageType === 'multi') {
    return envStorageType;
  }
  
  // Log warning for invalid values
  if (envStorageType && envStorageType !== DEFAULT_STORAGE_TYPE.toLowerCase()) {
    console.warn(
      `Invalid STORAGE_TYPE "${envStorageType}". Valid values are: r2, log, multi. ` +
      `Using default: ${DEFAULT_STORAGE_TYPE}`
    );
  }
  
  return DEFAULT_STORAGE_TYPE;
}

/**
 * Create the appropriate storage adapter based on environment configuration
 * 
 * This factory function:
 * - Reads STORAGE_TYPE environment variable ('r2', 'log', 'multi')
 * - For 'r2': returns R2Adapter (requires bucket parameter)
 * - For 'log': returns LogAdapter (no dependencies)
 * - For 'multi': returns MultiAdapter with both R2 and Log adapters
 * - Handles missing R2 bucket gracefully (falls back to LogAdapter)
 * 
 * @param options - Configuration options for the storage adapter
 * @returns Promise resolving to the configured StorageAdapter instance
 * @throws Error if the configuration is invalid and no fallback is possible
 */
export async function createStorageAdapter(
  options: CreateStorageAdapterOptions = {}
): Promise<StorageAdapter> {
  const storageType = options.storageType || getStorageType();
  const { bucket } = options;

  try {
    switch (storageType) {
      case 'log':
        console.warn('[StorageFactory] Creating LogAdapter');
        return new LogAdapter();

      case 'r2':
        if (!bucket) {
          console.warn(
            '[StorageFactory] R2 bucket not available, falling back to LogAdapter'
          );
          return new LogAdapter();
        }
        console.log('[StorageFactory] Creating R2Adapter');
        return new R2Adapter(bucket);

      case 'multi':
        const adapters: StorageAdapter[] = [];
        
        // Always add LogAdapter for multi-storage
        adapters.push(new LogAdapter());
        
        // Add R2Adapter if bucket is available
        if (bucket) {
          adapters.push(new R2Adapter(bucket));
          console.log('[StorageFactory] Creating MultiAdapter with R2 and Log adapters');
        } else {
          console.warn(
            '[StorageFactory] R2 bucket not available for MultiAdapter, using LogAdapter only'
          );
        }
        
        return new MultiAdapter(adapters);

      default:
        // TypeScript should prevent this, but handle it just in case
        throw new Error(`Unknown storage type: ${storageType}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`[StorageFactory] Error creating ${storageType} adapter: ${errorMessage}`);
    
    // Final fallback to LogAdapter if everything else fails
    console.log('[StorageFactory] Falling back to LogAdapter due to error');
    return new LogAdapter();
  }
}

/**
 * Convenience function to create a storage adapter with R2 bucket from environment
 * 
 * This function automatically extracts the R2 bucket from the Cloudflare Workers
 * environment and passes it to createStorageAdapter.
 * 
 * @param env - Cloudflare Workers environment object (should contain DATA_BUCKET)
 * @param options - Additional options for storage adapter creation
 * @returns Promise resolving to the configured StorageAdapter instance
 */
export async function createStorageAdapterFromEnv(
  env: any,
  options: Omit<CreateStorageAdapterOptions, 'bucket'> = {}
): Promise<StorageAdapter> {
  const bucket = env?.DATA_BUCKET;
  
  if (!bucket) {
    console.warn('[StorageFactory] DATA_BUCKET not found in environment');
  }
  
  return createStorageAdapter({
    ...options,
    bucket,
  });
}