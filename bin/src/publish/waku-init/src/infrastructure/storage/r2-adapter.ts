/**
 * R2 Storage Adapter
 * 
 * Cloudflare R2 storage adapter that implements the StorageAdapter interface.
 * Provides abstraction over R2 bucket operations for persistent storage.
 */

import type { StorageAdapter } from '../../domain/storage/types';

/**
 * R2Adapter implements StorageAdapter using Cloudflare R2 as the storage backend.
 * 
 * This adapter:
 * - Handles JSON stringification automatically
 * - Formats metadata for R2 compatibility (httpMetadata, customMetadata)
 * - Provides a clean abstraction over the R2 bucket API
 */
export class R2Adapter implements StorageAdapter {
  /**
   * Create a new R2Adapter instance
   * 
   * @param bucket - The R2 bucket object from Cloudflare Workers environment
   */
  constructor(private readonly bucket: any) {}

  /**
   * Save data to R2 storage
   * 
   * @param key - Storage path/identifier (R2 object key)
   * @param data - The data to store (will be JSON stringified if not already a string)
   * @param metadata - Optional metadata to store with the data
   */
  async save(
    key: string,
    data: any,
    metadata?: Record<string, any>
  ): Promise<void> {
    // Convert data to string if it's an object
    const dataString = typeof data === 'string' ? data : JSON.stringify(data);
    
    // Format metadata for R2 if provided
    let r2Metadata: any = undefined;
    if (metadata) {
      r2Metadata = this.formatMetadataForR2(metadata);
    }

    // Store in R2 bucket
    await this.bucket.put(key, dataString, r2Metadata);
  }

  /**
   * Format metadata for R2 compatibility
   * 
   * R2 expects metadata in a specific format with httpMetadata and customMetadata.
   * This method handles the conversion from our generic metadata format.
   * 
   * @param metadata - Generic metadata object
   * @returns R2-formatted metadata object
   */
  private formatMetadataForR2(metadata: Record<string, any>): any {
    const httpMetadata: Record<string, string> = {};
    const customMetadata: Record<string, string> = {};

    // Extract known HTTP headers and convert the rest to custom metadata
    for (const [key, value] of Object.entries(metadata)) {
      const stringValue = String(value);
      
      // Map standard metadata to HTTP headers
      switch (key) {
        case 'contentType':
          httpMetadata.contentType = stringValue;
          break;
        case 'contentEncoding':
          httpMetadata.contentEncoding = stringValue;
          break;
        case 'contentLanguage':
          httpMetadata.contentLanguage = stringValue;
          break;
        case 'contentDisposition':
          httpMetadata.contentDisposition = stringValue;
          break;
        case 'cacheControl':
          httpMetadata.cacheControl = stringValue;
          break;
        default:
          // All other metadata goes to custom metadata
          customMetadata[key] = stringValue;
          break;
      }
    }

    // Build the R2 metadata object
    const r2Metadata: any = {};
    
    if (Object.keys(httpMetadata).length > 0) {
      r2Metadata.httpMetadata = httpMetadata;
    }
    
    if (Object.keys(customMetadata).length > 0) {
      r2Metadata.customMetadata = customMetadata;
    }

    return r2Metadata;
  }
}