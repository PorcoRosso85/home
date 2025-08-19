/**
 * Internal type definitions for calc_partners application
 * These types are independent of kuzu-wasm and provide a clean abstraction layer
 */

/**
 * Generic query result interface
 * Represents the result of a database query execution
 */
export interface QueryResult {
  /** The result data table */
  table: Table;
  /** Cleanup resources */
  close(): Promise<void>;
}

/**
 * Table interface for query results
 * Provides methods to access and format query result data
 */
export interface Table {
  /** Convert table data to string representation */
  toString(): string;
  /** Get table data as JSON objects array (optional future extension) */
  toArray?(): Record<string, any>[];
  /** Get number of rows (optional future extension) */
  getRowCount?(): number;
  /** Get column names (optional future extension) */
  getColumnNames?(): string[];
}

/**
 * Database interface
 * Represents a database instance and its lifecycle management
 */
export interface Database {
  /** Close the database connection and cleanup resources */
  close(): Promise<void>;
  /** Optional: Get database path or identifier */
  getPath?(): string;
  /** Optional: Check if database is open */
  isOpen?(): boolean;
}

/**
 * Connection interface for database operations
 * Provides methods to execute queries and manage the connection
 */
export interface Connection {
  /** Execute a query and return the result */
  execute(query: string): Promise<QueryResult>;
  /** Close the connection and cleanup resources */
  close(): Promise<void>;
  /** Optional: Check if connection is active */
  isActive?(): boolean;
  /** Optional: Get associated database */
  getDatabase?(): Database;
}

/**
 * Database initialization options
 * Configuration for database setup
 */
export interface DatabaseOptions {
  /** Database path or identifier */
  path?: string;
  /** Read-only mode flag */
  readOnly?: boolean;
  /** Memory allocation settings */
  bufferSize?: number;
  /** Custom configuration options */
  config?: Record<string, any>;
}

/**
 * Connection factory interface
 * Abstracts the creation of database connections
 */
export interface ConnectionFactory {
  /** Create a new database instance */
  createDatabase(options?: DatabaseOptions): Promise<Database>;
  /** Create a connection to the given database */
  createConnection(database: Database): Promise<Connection>;
}