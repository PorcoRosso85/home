/**
 * Multi-Storage Adapter
 * 
 * A storage adapter that saves to multiple storage backends simultaneously.
 * Provides redundancy by ensuring data is persisted across multiple adapters.
 */

import type { StorageAdapter } from '../../domain/storage/types';

/**
 * MultiAdapter implements StorageAdapter by delegating to multiple storage backends.
 * 
 * This adapter:
 * - Saves to all provided adapters simultaneously using Promise.all
 * - Continues operation even if some adapters fail
 * - Logs errors for failed adapters but doesn't throw unless all fail
 * - Returns success if at least one adapter succeeds
 * 
 * Use cases:
 * - Data redundancy across multiple storage systems
 * - Backup to multiple locations
 * - Development/production dual writes
 */
export class MultiAdapter implements StorageAdapter {
  /**
   * Create a new MultiAdapter instance
   * 
   * @param adapters - Array of StorageAdapter instances to write to
   */
  constructor(private readonly adapters: StorageAdapter[]) {
    if (adapters.length === 0) {
      throw new Error('MultiAdapter requires at least one adapter');
    }
  }

  /**
   * Save data to all storage adapters simultaneously
   * 
   * @param key - Storage path/identifier
   * @param data - The data to store
   * @param metadata - Optional metadata to store with the data
   * @throws Error only if all adapters fail
   */
  async save(
    key: string,
    data: any,
    metadata?: Record<string, any>
  ): Promise<void> {
    const timestamp = new Date().toISOString();
    
    // Create save promises for all adapters
    const savePromises = this.adapters.map(async (adapter, index) => {
      try {
        await adapter.save(key, data, metadata);
        return { success: true, adapterIndex: index, error: null };
      } catch (error) {
        // Log the error but don't throw - let other adapters continue
        console.error(
          `[MultiAdapter:${timestamp}] Adapter ${index} failed to save key "${key}":`,
          error
        );
        return { success: false, adapterIndex: index, error };
      }
    });

    // Wait for all save operations to complete (settled, not fulfilled)
    const results = await Promise.allSettled(savePromises);
    
    // Extract the actual results from Promise.allSettled
    const saveResults = results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        // This should rarely happen since we're catching errors in the promises above
        console.error(
          `[MultiAdapter:${timestamp}] Unexpected error with adapter ${index}:`,
          result.reason
        );
        return { success: false, adapterIndex: index, error: result.reason };
      }
    });

    // Count successful and failed operations
    const successfulCount = saveResults.filter(result => result.success).length;
    const failedCount = saveResults.filter(result => !result.success).length;

    // Log operation summary
    if (failedCount > 0) {
      console.warn(
        `[MultiAdapter:${timestamp}] Save to "${key}" completed with ${successfulCount}/${this.adapters.length} adapters successful`
      );
    } else {
      console.log(
        `[MultiAdapter:${timestamp}] Save to "${key}" successful on all ${this.adapters.length} adapters`
      );
    }

    // Throw error only if ALL adapters failed
    if (successfulCount === 0) {
      const errorDetails = saveResults.map((result, index) => 
        `Adapter ${index}: ${result.error?.message || 'Unknown error'}`
      ).join('; ');
      
      throw new Error(
        `MultiAdapter: All ${this.adapters.length} adapters failed to save "${key}". Errors: ${errorDetails}`
      );
    }

    // Success if at least one adapter succeeded
  }

  /**
   * Get the number of configured adapters
   * 
   * @returns Number of adapters this MultiAdapter manages
   */
  getAdapterCount(): number {
    return this.adapters.length;
  }

  /**
   * Get the adapters managed by this MultiAdapter
   * 
   * @returns ReadOnly array of the configured adapters
   */
  getAdapters(): readonly StorageAdapter[] {
    return [...this.adapters];
  }
}