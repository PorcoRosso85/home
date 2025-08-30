/**
 * Storage Domain Types
 * 
 * Defines the storage adapter interface for the domain layer.
 * This follows YAGNI principles - only what's needed now.
 */

/**
 * Metadata for storage operations
 */
export interface StorageMetadata {
  /** Timestamp when the data was stored */
  readonly timestamp?: number;
  /** Content type of the stored data */
  readonly contentType?: string;
  /** Size of the stored data in bytes */
  readonly size?: number;
  /** Any additional metadata as key-value pairs */
  readonly [key: string]: unknown;
}

/**
 * Storage adapter interface for persisting data
 * 
 * This interface abstracts storage operations to allow different
 * storage backends (R2, filesystem, database, etc.)
 */
export interface StorageAdapter {
  /**
   * Save data to storage
   * 
   * @param key - Storage path/identifier
   * @param data - The data to store
   * @param metadata - Optional metadata to store with the data
   * @returns Promise that resolves when save is complete
   */
  save(
    key: string,
    data: any,
    metadata?: Record<string, any>
  ): Promise<void>;
}