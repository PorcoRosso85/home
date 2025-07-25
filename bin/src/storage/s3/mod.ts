/**
 * S3 Storage Module - LLM-first interface for S3 operations
 * 
 * This module provides a conversational interface for S3 operations,
 * accepting JSON input for various actions like upload, download, list, and delete.
 */

// Re-export main application interface
export { executeS3Command, S3StorageApplication } from './application.ts';

// Re-export domain types
export type { 
  S3Command, 
  S3Result, 
  S3Config
} from './domain.ts';

// Re-export adapter types and factory
export type { 
  StorageAdapter, 
  StorageConfig,
  StorageListOptions,
  StorageListResult,
  StorageUploadOptions,
  StorageUploadResult,
  StorageDownloadOptions,
  StorageDownloadResult,
  StorageDeleteResult,
  StorageInfoResult,
  StorageObject
} from './adapter.ts';
export { createStorageAdapter } from './adapter.ts';

// Re-export provider implementations for direct usage
export { InMemoryStorageAdapter } from './providers/in-memory.ts';
export { FilesystemStorageAdapter } from './providers/filesystem.ts';