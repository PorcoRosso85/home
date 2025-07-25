/**
 * Storage Adapter Pattern Implementation
 * Provides a unified interface for multiple storage backends
 * Following the "wall of refactoring" principle - implementation details are hidden
 */

// Storage configuration types
export type StorageConfig = 
  | { type: "auto"; endpoint?: string; region?: string; accessKeyId?: string; secretAccessKey?: string; bucket?: string }
  | { type: "filesystem"; basePath: string }
  | { type: "s3"; endpoint: string; region: string; accessKeyId: string; secretAccessKey: string; bucket: string }
  | { type: "r2"; accountId: string; accessKeyId: string; secretAccessKey: string; bucket: string };

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

// Re-export the factory function from providers
export { createStorageAdapter } from "./providers/factory.ts";