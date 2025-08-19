/**
 * Infrastructure Layer - External System Integration
 * 
 * This layer handles all external dependencies and I/O operations.
 * Only this layer should have direct dependencies on external libraries.
 */

// Re-export from kuzu module
export {
  initializeKuzu,
  executeQuery,
  initializeDatabase,
  executeQueryWithConnection,
  type KuzuConnectionInfo
} from './kuzu.js'

// Re-export from cypherLoader
export { loadQuery, type LoadQueryResult } from './cypherLoader.js'

// Re-export types
export type {
  Database,
  Connection,
  QueryResult,
  Table,
  DatabaseOptions,
  ConnectionFactory
} from './types.js'