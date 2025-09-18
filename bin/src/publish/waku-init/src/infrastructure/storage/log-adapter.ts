/**
 * Log-based Storage Adapter
 * 
 * Simple storage adapter that logs all storage operations to the console.
 * Useful for development and debugging purposes.
 */

import type { StorageAdapter } from '../../domain/storage/types';

/**
 * LogAdapter implements StorageAdapter by logging all storage operations
 * to the console instead of actually persisting data.
 * 
 * This is useful for:
 * - Development and debugging
 * - Testing storage workflows
 * - Understanding data flow without actual persistence
 */
export class LogAdapter implements StorageAdapter {
  /**
   * Save data by logging the operation to console
   * 
   * @param key - Storage path/identifier
   * @param data - The data to store
   * @param metadata - Optional metadata to store with the data
   */
  async save(
    key: string,
    data: any,
    metadata?: Record<string, any>
  ): Promise<void> {
    const timestamp = new Date().toISOString();
    const dataString = typeof data === 'string' ? data : JSON.stringify(data);
    const size = new TextEncoder().encode(dataString).length;

    // Log the storage operation with structured format
    // Using console.warn to ensure visibility in wrangler tail
    console.warn(`[STORAGE:${timestamp}] Saving to ${key} (${size} bytes)`);
    
    // Log the actual data on a separate line for debugging
    console.warn('Data:', data);
    
    // Log metadata if provided
    if (metadata) {
      console.warn('Metadata:', metadata);
    }
  }
}