/**
 * Domain types for S3 operations
 */

// S3 configuration
export interface S3Config {
  endpoint?: string;
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
  bucket: string;
}

// Command types for different S3 operations
export type S3Command = 
  | ListCommand
  | UploadCommand
  | DownloadCommand
  | DeleteCommand
  | InfoCommand
  | HelpCommand;

export interface ListCommand {
  action: 'list';
  prefix?: string;
  maxKeys?: number;
  continuationToken?: string;
}

export interface UploadCommand {
  action: 'upload';
  key: string;
  content: string | Uint8Array;
  contentType?: string;
  metadata?: Record<string, string>;
}

export interface DownloadCommand {
  action: 'download';
  key: string;
  outputPath?: string;
}

export interface DeleteCommand {
  action: 'delete';
  keys: string[];
}

export interface InfoCommand {
  action: 'info';
  key: string;
}

export interface HelpCommand {
  action: 'help';
}

// Result types
export type S3Result = 
  | ListResult
  | UploadResult
  | DownloadResult
  | DeleteResult
  | InfoResult
  | HelpResult
  | ErrorResult;

export interface ListResult {
  type: 'list';
  objects: S3Object[];
  continuationToken?: string;
  isTruncated: boolean;
}

export interface S3Object {
  key: string;
  lastModified: Date;
  size: number;
  etag?: string;
  storageClass?: string;
}

export interface UploadResult {
  type: 'upload';
  key: string;
  etag: string;
  versionId?: string;
}

export interface DownloadResult {
  type: 'download';
  key: string;
  content?: string;
  savedTo?: string;
  contentType?: string;
  metadata?: Record<string, string>;
}

export interface DeleteResult {
  type: 'delete';
  deleted: string[];
  errors: Array<{ key: string; error: string }>;
}

export interface InfoResult {
  type: 'info';
  key: string;
  exists: boolean;
  size?: number;
  lastModified?: Date;
  contentType?: string;
  metadata?: Record<string, string>;
}

export interface HelpResult {
  type: 'help';
  message: string;
  examples: CommandExample[];
}

export interface CommandExample {
  description: string;
  command: Record<string, any>;
}

export interface ErrorResult {
  type: 'error';
  message: string;
  details?: any;
}

// Validation functions

/**
 * Validates S3 object key
 * - Maximum 1024 bytes
 * - No null bytes or control characters
 */
export function validateS3Key(key: string): void {
  // Check byte length (not character length)
  const byteLength = new TextEncoder().encode(key).length;
  if (byteLength > 1024) {
    throw new Error("S3 key exceeds maximum length of 1024 bytes");
  }
  
  // Check for null bytes and control characters
  for (let i = 0; i < key.length; i++) {
    const charCode = key.charCodeAt(i);
    if (charCode === 0 || (charCode >= 0x01 && charCode <= 0x1F)) {
      throw new Error("S3 key contains invalid characters");
    }
  }
}

/**
 * Validates S3 object size
 * - Maximum 5GB for single PUT operation
 * - Must be non-negative
 */
export function validateS3ObjectSize(size: number): void {
  if (size < 0) {
    throw new Error("Object size must be non-negative");
  }
  
  const maxSize = 5 * 1024 * 1024 * 1024; // 5GB
  if (size > maxSize) {
    throw new Error("Object size exceeds S3 limit of 5GB");
  }
}

/**
 * Validates S3 bucket name
 * - 3-63 characters
 * - Only lowercase letters, numbers, and hyphens
 * - Must start and end with letter or number
 * - No consecutive hyphens
 */
export function validateS3BucketName(name: string): void {
  // Check length
  if (name.length < 3 || name.length > 63) {
    throw new Error("Bucket name must be between 3 and 63 characters");
  }
  
  // Check for valid characters (lowercase letters, numbers, hyphens)
  if (!/^[a-z0-9-]+$/.test(name)) {
    throw new Error("Bucket name must contain only lowercase letters, numbers, and hyphens");
  }
  
  // Check start and end characters
  if (!/^[a-z0-9]/.test(name) || !/[a-z0-9]$/.test(name)) {
    throw new Error("Bucket name must start and end with a letter or number");
  }
  
  // Check for consecutive hyphens
  if (name.includes("--")) {
    throw new Error("Bucket name cannot contain consecutive hyphens");
  }
}