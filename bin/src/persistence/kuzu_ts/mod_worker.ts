/**
 * KuzuDB Worker-based Implementation for Deno
 * 
 * This module provides a stable KuzuDB interface using Worker process isolation.
 * All database operations run in a separate worker thread, preventing any
 * potential crashes from affecting the main application.
 * 
 * @module
 */

// Re-export all Worker-based implementations
export {
  createDatabaseWorker as createDatabase,
  createConnectionWorker as createConnection,
  terminateWorker,
  WorkerDatabase,
  WorkerConnection,
} from "./core/database_worker_client.ts";

// Re-export configuration and types
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

// Re-export error types
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

// Re-export result types
export type {
  DatabaseResult,
  ConnectionResult,
} from "./core/result_types.ts";

export {
  isDatabase,
  isConnection,
} from "./core/result_types.ts";

/**
 * Example usage:
 * 
 * ```typescript
 * import { createDatabase, createConnection, terminateWorker } from "./mod_worker.ts";
 * 
 * // Create an in-memory database
 * const db = await createDatabase(":memory:");
 * const conn = await createConnection(db);
 * 
 * // Execute queries
 * await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))");
 * await conn.query("CREATE (p:Person {name: 'Alice', age: 30})");
 * 
 * const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age");
 * const rows = await result.getAll();
 * 
 * // Clean up
 * await conn.close();
 * await db.close();
 * 
 * // Terminate the worker when done with all operations
 * terminateWorker();
 * ```
 */