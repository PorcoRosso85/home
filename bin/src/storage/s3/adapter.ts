/**
 * Storage Adapter Pattern Implementation
 * Provides a unified interface for multiple storage backends
 * Following the "wall of refactoring" principle - implementation details are hidden
 */

import { S3Client } from "./infrastructure.ts";

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

// In-memory storage adapter implementation
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
    const bytes = typeof content === "string" 
      ? new TextEncoder().encode(content)
      : content;
    
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
      if (this.storage.has(key)) {
        this.storage.delete(key);
        deleted.push(key);
      } else {
        errors.push({ key, error: "Object not found" });
      }
    }
    
    return { deleted, errors };
  }
  
  async info(key: string): Promise<StorageInfoResult> {
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

// Placeholder implementations for other adapters
class FilesystemStorageAdapter implements StorageAdapter {
  constructor(private basePath: string) {}
  
  async list(options?: StorageListOptions): Promise<StorageListResult> {
    // TODO: Implement filesystem listing
    return { objects: [], isTruncated: false };
  }
  
  async upload(key: string, content: string | Uint8Array, options?: StorageUploadOptions): Promise<StorageUploadResult> {
    // TODO: Implement filesystem upload
    return { key, etag: "filesystem-etag" };
  }
  
  async download(key: string, options?: StorageDownloadOptions): Promise<StorageDownloadResult> {
    // TODO: Implement filesystem download
    return { key, content: new Uint8Array() };
  }
  
  async delete(keys: string[]): Promise<StorageDeleteResult> {
    // TODO: Implement filesystem delete
    return { deleted: keys, errors: [] };
  }
  
  async info(key: string): Promise<StorageInfoResult> {
    // TODO: Implement filesystem info
    return { key, exists: false };
  }
  
  getType(): string {
    return "filesystem";
  }
  
  async isHealthy(): Promise<boolean> {
    // TODO: Check if basePath is accessible
    return true;
  }
}

class S3StorageAdapter implements StorageAdapter {
  private s3Client: S3Client;
  
  constructor(private config: Extract<StorageConfig, { type: "s3" }>) {
    // Import and use the existing S3Client
    this.s3Client = new S3Client({
      endpoint: config.endpoint,
      region: config.region,
      accessKeyId: config.accessKeyId,
      secretAccessKey: config.secretAccessKey,
      bucket: config.bucket
    });
  }
  
  async list(options?: StorageListOptions): Promise<StorageListResult> {
    const result = await this.s3Client.listObjects({
      action: 'list',
      prefix: options?.prefix,
      maxKeys: options?.maxKeys,
      continuationToken: options?.continuationToken
    });
    
    return {
      objects: result.objects.map(obj => ({
        key: obj.key,
        lastModified: obj.lastModified,
        size: obj.size,
        etag: obj.etag
      })),
      continuationToken: result.continuationToken,
      isTruncated: result.isTruncated
    };
  }
  
  async upload(key: string, content: string | Uint8Array, options?: StorageUploadOptions): Promise<StorageUploadResult> {
    const result = await this.s3Client.uploadObject({
      action: 'upload',
      key,
      content,
      contentType: options?.contentType,
      metadata: options?.metadata
    });
    
    return {
      key: result.key,
      etag: result.etag,
      versionId: result.versionId
    };
  }
  
  async download(key: string, options?: StorageDownloadOptions): Promise<StorageDownloadResult> {
    const result = await this.s3Client.downloadObject({
      action: 'download',
      key,
      outputPath: options?.outputPath
    });
    
    // Convert content to Uint8Array if it's a string
    const content = result.content 
      ? new TextEncoder().encode(result.content)
      : new Uint8Array();
    
    return {
      key: result.key,
      content,
      contentType: result.contentType,
      metadata: result.metadata
    };
  }
  
  async delete(keys: string[]): Promise<StorageDeleteResult> {
    const result = await this.s3Client.deleteObjects({
      action: 'delete',
      keys
    });
    
    return {
      deleted: result.deleted,
      errors: result.errors
    };
  }
  
  async info(key: string): Promise<StorageInfoResult> {
    const result = await this.s3Client.getObjectInfo({
      action: 'info',
      key
    });
    
    return {
      key: result.key,
      exists: result.exists,
      size: result.size,
      lastModified: result.lastModified,
      contentType: result.contentType,
      metadata: result.metadata
    };
  }
  
  getType(): string {
    // Detect provider based on endpoint
    const endpoint = this.config.endpoint.toLowerCase();
    if (endpoint.includes("amazonaws.com")) return "s3";
    if (endpoint.includes("localhost") || endpoint.includes("127.0.0.1")) return "minio";
    if (endpoint.includes("r2.cloudflarestorage.com")) return "r2";
    if (endpoint.includes("backblazeb2.com")) return "b2";
    return "s3-compatible";
  }
  
  async isHealthy(): Promise<boolean> {
    try {
      // Try to list with a very small limit to check connectivity
      await this.s3Client.listObjects({
        action: 'list',
        maxKeys: 1
      });
      return true;
    } catch (error) {
      return false;
    }
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
    // If endpoint is specified, use S3 adapter
    return new S3StorageAdapter({
      type: "s3",
      endpoint: s3Config.endpoint,
      region: s3Config.region || "us-east-1",
      accessKeyId: s3Config.accessKeyId || "",
      secretAccessKey: s3Config.secretAccessKey || "",
      bucket: s3Config.bucket || ""
    });
  }
  
  switch (typedConfig.type) {
    case "filesystem":
      const fsConfig = typedConfig as { type: "filesystem"; basePath?: string };
      return new FilesystemStorageAdapter(fsConfig.basePath || "/tmp/storage");
    case "s3":
      const s3Config = typedConfig as Partial<Extract<StorageConfig, { type: "s3" }>>;
      return new S3StorageAdapter({
        type: "s3",
        endpoint: s3Config.endpoint || "",
        region: s3Config.region || "us-east-1",
        accessKeyId: s3Config.accessKeyId || "",
        secretAccessKey: s3Config.secretAccessKey || "",
        bucket: s3Config.bucket || ""
      });
    default:
      throw new Error(`Unknown storage type: ${(typedConfig as any).type}`);
  }
}