/**
 * Public API for kuzu_bun module
 */

// Infrastructure exports
export { loadKuzu } from './infrastructure';
export type { KuzuModule } from './infrastructure';

// Domain exports
export {
  createDatabase,
  createConnection,
  executeQuery
} from './domain';
export type {
  QueryResult,
  Connection,
  Database
} from './domain';

// Application exports
export { runInMemoryExample } from './application';