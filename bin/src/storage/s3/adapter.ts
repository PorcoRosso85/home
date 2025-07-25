/**
 * Storage Adapter Pattern Implementation
 * Provides a unified interface for multiple storage backends
 * Following the "wall of refactoring" principle - implementation details are hidden
 */

import { validateS3Key, validateS3ObjectSize, validateS3BucketName } from "./domain.ts";

// Storage configuration types
export type StorageConfig = 
  | { type: "auto"; endpoint?: string; region?: string; accessKeyId?: string; secretAccessKey?: string; bucket?: string }
  | { type: "filesystem"; basePath: string }
  | { type: "s3"; endpoint: string; region: string; accessKeyId: string; secretAccessKey: string; bucket: string };

// Storage operation options
export interface StorageListOptions {
  prefix?: string;
  maxKeys?: number;
  continuationToken?: string;
}

export interface StorageUploadOptions {
  contentType?: string;
  metadata?: Record<string, string>;
}

export interface StorageDownloadOptions {
  outputPath?: string;
}

// Storage object representation
export interface StorageObject {
  key: string;
  lastModified: Date;
  size: number;
  etag?: string;
}

// Storage operation results
export interface StorageListResult {
  objects: StorageObject[];
  continuationToken?: string;
  isTruncated: boolean;
}

export interface StorageUploadResult {
  key: string;
  etag: string;
  versionId?: string;
}

export interface StorageDownloadResult {
  key: string;
  content: Uint8Array;
  contentType?: string;
  metadata?: Record<string, string>;
}

export interface StorageDeleteResult {
  deleted: string[];
  errors: Array<{ key: string; error: string }>;
}

export interface StorageInfoResult {
  key: string;
  exists: boolean;
  size?: number;
  lastModified?: Date;
  contentType?: string;
  metadata?: Record<string, string>;
}

// Main adapter interface - the "wall" that hides implementation details
export interface StorageAdapter {
  // Core storage operations
  list(options?: StorageListOptions): Promise<StorageListResult>;
  upload(key: string, content: string | Uint8Array, options?: StorageUploadOptions): Promise<StorageUploadResult>;
  download(key: string, options?: StorageDownloadOptions): Promise<StorageDownloadResult>;
  delete(keys: string[]): Promise<StorageDeleteResult>;
  info(key: string): Promise<StorageInfoResult>;
  
  // Adapter metadata
  getType(): string;
  isHealthy(): Promise<boolean>;
}

// Simple in-memory adapter for testing
class InMemoryStorageAdapter implements StorageAdapter {
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
    
    return {
      objects: objects.slice(0, options?.maxKeys || 1000),
      isTruncated: false,
      continuationToken: undefined
    };
  }
  
  async upload(key: string, content: string | Uint8Array, options?: StorageUploadOptions): Promise<StorageUploadResult> {
    // Validate key
    validateS3Key(key);
    
    const bytes = typeof content === "string" ? new TextEncoder().encode(content) : content;
    
    // Validate object size
    validateS3ObjectSize(bytes.length);
    
    const etag = `"${crypto.randomUUID()}"`;
    
    this.storage.set(key, {
      content: bytes,
      metadata: {
        lastModified: new Date().toISOString(),
        etag,
        contentType: options?.contentType,
        ...options?.metadata
      }
    });
    
    return { key, etag };
  }
  
  async download(key: string, options?: StorageDownloadOptions): Promise<StorageDownloadResult> {
    // Validate key
    validateS3Key(key);
    
    const item = this.storage.get(key);
    if (!item) {
      throw new Error(`Object not found: ${key}`);
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
        // Validate key
        validateS3Key(key);
        
        if (this.storage.has(key)) {
          this.storage.delete(key);
          deleted.push(key);
        } else {
          errors.push({ key, error: "Not found" });
        }
      } catch (e) {
        errors.push({ key, error: e instanceof Error ? e.message : String(e) });
      }
    }
    
    return { deleted, errors };
  }
  
  async info(key: string): Promise<StorageInfoResult> {
    // Validate key
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
}

// Mock filesystem adapter
class FilesystemStorageAdapter extends InMemoryStorageAdapter {
  override getType(): string {
    return "filesystem";
  }
}

// Mock S3 adapter
class S3StorageAdapter extends InMemoryStorageAdapter {
  constructor(config: { bucket: string }) {
    super();
    // Validate bucket name
    validateS3BucketName(config.bucket);
  }
  
  override getType(): string {
    return "s3";
  }
}

// Mock MinIO adapter
class MinIOStorageAdapter extends InMemoryStorageAdapter {
  constructor(config: { bucket: string }) {
    super();
    // Validate bucket name
    validateS3BucketName(config.bucket);
  }
  
  override getType(): string {
    return "minio";
  }
}

// Factory function to create appropriate adapter
export function createStorageAdapter(config: Partial<StorageConfig> | {}): StorageAdapter {
  // Handle empty config
  if (!config || Object.keys(config).length === 0) {
    return new InMemoryStorageAdapter();
  }
  
  // Type guard for better type inference
  const typedConfig = config as Partial<StorageConfig>;
  
  // Auto-detect or use specified type
  if (!typedConfig.type || typedConfig.type === "auto") {
    // Check if it looks like S3 config
    const s3Config = typedConfig as any;
    if (!s3Config.endpoint) {
      return new InMemoryStorageAdapter();
    }
    // Check for MinIO
    if (s3Config.endpoint.includes("localhost:9000")) {
      return new MinIOStorageAdapter({ bucket: s3Config.bucket || "default-bucket" });
    }
    return new S3StorageAdapter({ bucket: s3Config.bucket || "default-bucket" });
  }
  
  switch (typedConfig.type) {
    case "filesystem":
      return new FilesystemStorageAdapter();
    case "s3":
      const s3Config = typedConfig as any;
      // Even with explicit s3 type, check for MinIO endpoint
      if (s3Config.endpoint && s3Config.endpoint.includes("localhost:9000")) {
        return new MinIOStorageAdapter({ bucket: s3Config.bucket || "default-bucket" });
      }
      return new S3StorageAdapter({ bucket: s3Config.bucket || "default-bucket" });
    default:
      throw new Error(`Unknown storage type: ${(typedConfig as any).type}`);
  }
}