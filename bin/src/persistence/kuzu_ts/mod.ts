// Main entry point for kuzu_ts module
// Re-exports all implementations

// Export shared utilities and types
export * from "./shared/mod.ts";

// Export classic implementation (default)
export {
  createDatabase,
  createConnection,
  type DatabaseOptions as ClassicDatabaseOptions,
} from "./classic/mod.ts";

// Export worker implementation with prefixed names to avoid conflicts
export {
  createDatabase as createDatabaseWorker,
  createConnection as createConnectionWorker,
  terminateWorker,
  WorkerDatabase,
  WorkerConnection,
} from "./worker/mod.ts";