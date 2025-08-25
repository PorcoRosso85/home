/**
 * Public API for kuzu_node module
 */

// Infrastructure layer exports
export { 
  loadKuzu,
  detectEnvironment,
  createKuzuDatabase,
  cleanupKuzu,
  type KuzuModule,
  type DatabaseConfig
} from './infrastructure';

// Domain layer exports
export { 
  executeQuery,
  executeQueries,
  queryOne,
  createSchema,
  loadData,
  beginTransaction,
  commitTransaction,
  rollbackTransaction,
  type QueryResult,
  type Connection,
  type Database
} from './domain';

// Application layer exports
export { 
  runInMemoryExample,
  runMovieExample,
  runTransactionExample
} from './application';