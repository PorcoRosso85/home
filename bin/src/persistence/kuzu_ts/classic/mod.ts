// Main entry point for kuzu_ts classic module
export { createDatabase, createConnection } from "./database.ts";
export type { DatabaseOptions } from "./database.ts";

// Version
export { KUZU_VERSION } from "../shared/version.ts";

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
} from "../shared/config.ts";
export type { KuzuConfig, QueryType } from "../shared/config.ts";

// Error types and functions
export type {
  FileOperationError,
  ValidationError,
  NotFoundError,
  KuzuError,
} from "../shared/errors.ts";

export {
  createFileOperationError,
  createValidationError,
  createNotFoundError,
  isFileOperationError,
  isValidationError,
  isNotFoundError,
  isKuzuError,
} from "../shared/errors.ts";

// Result types and type guards
export type {
  DatabaseResult,
  ConnectionResult,
} from "../shared/types.ts";

export {
  isDatabase,
  isConnection,
} from "../shared/types.ts";