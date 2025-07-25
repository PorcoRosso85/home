/**
 * In-memory storage adapter implementation
 * Provides a memory-based storage backend for testing and development
 */

import type { 
  StorageAdapter, 
  StorageListOptions, 
  StorageListResult,
  StorageUploadOptions,
  StorageUploadResult,
  StorageDownloadOptions,
  StorageDownloadResult,
  StorageDeleteResult,
  StorageInfoResult,
  StorageObject
} from "../adapter.ts";
import { validateS3Key, validateS3ObjectSize } from "../domain.ts";

export class InMemoryStorageAdapter implements StorageAdapter {
  private storage: Map<string, { content: Uint8Array; metadata: Record<string, any> }> = new Map();
  
  async list(options?: StorageListOptions): Promise<StorageListResult> {
    const objects: StorageObject[] = [];
    const prefix = options?.prefix || "";
    
    for (const [key, value] of this.storage.entries()) {
      if (key.startsWith(prefix)) {
        objects.push({
          key,
          lastModified: new Date(value.metadata.lastModified),
          size: value.content.length,
          etag: value.metadata.etag
        });
      }
    }
    
    // Sort objects by key (S3-like behavior)
    objects.sort((a, b) => a.key.localeCompare(b.key));
    
    // Simple pagination
    const maxKeys = options?.maxKeys || 1000;
    const truncated = objects.length > maxKeys;
    
    return {
      objects: objects.slice(0, maxKeys),
      isTruncated: truncated,
      continuationToken: truncated ? String(maxKeys) : undefined
    };
  }
  
  async upload(key: string, content: string | Uint8Array, options?: StorageUploadOptions): Promise<StorageUploadResult> {
    // Validate key before upload
    validateS3Key(key);
    
    const bytes = typeof content === "string" 
      ? new TextEncoder().encode(content)
      : content;
    
    // Validate object size
    validateS3ObjectSize(bytes.length);
    
    const etag = `"${await this.generateEtag(bytes)}"`;
    
    this.storage.set(key, {
      content: bytes,
      metadata: {
        etag,
        lastModified: new Date().toISOString(),
        contentType: options?.contentType,
        ...options?.metadata
      }
    });
    
    return { key, etag };
  }
  
  async download(key: string, options?: StorageDownloadOptions): Promise<StorageDownloadResult> {
    // Validate key before download
    validateS3Key(key);
    
    const item = this.storage.get(key);
    if (!item) {
      throw new Error(`Object not found: ${key}`);
    }
    
    // If outputPath is specified, save to file
    if (options?.outputPath) {
      await Deno.writeFile(options.outputPath, item.content);
    }
    
    return {
      key,
      content: item.content,
      contentType: item.metadata.contentType,
      metadata: item.metadata
    };
  }
  
  async delete(keys: string[]): Promise<StorageDeleteResult> {
    const deleted: string[] = [];
    const errors: Array<{ key: string; error: string }> = [];
    
    for (const key of keys) {
      try {
        // Validate key before attempting delete
        validateS3Key(key);
        
        if (this.storage.has(key)) {
          this.storage.delete(key);
          deleted.push(key);
        } else {
          errors.push({ key, error: "Object not found" });
        }
      } catch (error) {
        errors.push({ key, error: error instanceof Error ? error.message : String(error) });
      }
    }
    
    return { deleted, errors };
  }
  
  async info(key: string): Promise<StorageInfoResult> {
    // Validate key before getting info
    validateS3Key(key);
    
    const item = this.storage.get(key);
    
    if (!item) {
      return { key, exists: false };
    }
    
    return {
      key,
      exists: true,
      size: item.content.length,
      lastModified: new Date(item.metadata.lastModified),
      contentType: item.metadata.contentType,
      metadata: item.metadata
    };
  }
  
  getType(): string {
    return "in-memory";
  }
  
  async isHealthy(): Promise<boolean> {
    return true;
  }
  
  private async generateEtag(content: Uint8Array): Promise<string> {
    // Simple hash for etag generation
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      hash = ((hash << 5) - hash) + content[i];
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
  }
}