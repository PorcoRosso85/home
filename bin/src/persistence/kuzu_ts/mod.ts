// Main entry point for kuzu_ts module
export { createDatabase, createConnection } from "./core/database.ts";
export type { DatabaseOptions } from "./core/database.ts";

// Configuration and variables
export {
  DEFAULT_DB_MAX_SIZE,
  DEFAULT_CACHE_TTL,
  VALID_QUERY_TYPES,
  QUERY_FILE_EXTENSION,
  DEFAULT_QUERY_DIR,
  getKuzuPath,
  getCacheEnabled,
  getMaxCacheSize,
  getDebugMode,
  getDefaultConfig,
  mergeConfig,
} from "./core/variables.ts";
export type { KuzuConfig, QueryType } from "./core/variables.ts";

// Error types and functions
export type {
  FileOperationError,
  ValidationError,
  NotFoundError,
  KuzuError,
} from "./core/errors.ts";

export {
  createFileOperationError,
  createValidationError,
  createNotFoundError,
  isFileOperationError,
  isValidationError,
  isNotFoundError,
  isKuzuError,
} from "./core/errors.ts";

// Result types and type guards
export type {
  DatabaseResult,
  ConnectionResult,
} from "./core/result_types.ts";

export {
  isDatabase,
  isConnection,
  isFileOperationError,
  isValidationError,
} from "./core/result_types.ts";