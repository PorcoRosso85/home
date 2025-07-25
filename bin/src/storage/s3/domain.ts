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