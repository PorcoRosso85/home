/**
 * Shared components module
 * 
 * This module exports all shared interfaces, types, errors, and configurations
 * that are used across different KuzuDB implementation strategies (worker, classic, wasm)
 */

// Export all interfaces
export type {
  IDatabase,
  IConnection,
  IQueryResult,
  IDatabaseFactory,
  DatabaseOptions,
} from "./interfaces.ts";

// Export all error types and utilities
export type {
  FileOperationError,
  ValidationError,
  NotFoundError,
  KuzuError,
} from "./errors.ts";

export {
  createFileOperationError,
  createValidationError,
  createNotFoundError,
  isFileOperationError,
  isValidationError,
  isNotFoundError,
  isKuzuError,
} from "./errors.ts";

// Export result types and type guards
export type {
  DatabaseResult,
  ConnectionResult,
} from "./types.ts";

export {
  isDatabase,
  isConnection,
} from "./types.ts";

// Export configuration utilities and types
export type {
  QueryType,
  KuzuConfig,
} from "./config.ts";

export {
  getKuzuPath,
  getCacheEnabled,
  getMaxCacheSize,
  getDebugMode,
  getDefaultConfig,
  mergeConfig,
  DEFAULT_DB_MAX_SIZE,
  DEFAULT_CACHE_TTL,
  VALID_QUERY_TYPES,
  QUERY_FILE_EXTENSION,
  DEFAULT_QUERY_DIR,
} from "./config.ts";

// Export version information
export { KUZU_VERSION } from "./version.ts";