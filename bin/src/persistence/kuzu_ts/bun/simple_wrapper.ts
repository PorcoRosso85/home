/**
 * Simple Bun-compatible wrapper for KuzuDB
 * 
 * This provides a minimal API that directly uses the npm:kuzu package
 * without any Deno-specific dependencies.
 */

import kuzu from "kuzu";

/**
 * Creates a new KuzuDB database instance
 * @param path - Path to the database directory
 * @returns Database instance
 */
export async function createDatabase(path: string) {
  const db = new kuzu.Database(path);
  return db;
}

/**
 * Creates a connection to a KuzuDB database
 * @param database - Database instance
 * @returns Connection instance
 */
export async function createConnection(database: any) {
  const conn = new kuzu.Connection(database);
  return conn;
}

/**
 * Executes a query on the connection
 * @param connection - Connection instance
 * @param query - Query string to execute
 * @returns Query result
 */
export async function executeQuery(connection: any, query: string) {
  // Prepare the statement first
  const preparedStatement = await connection.prepare(query);
  // Execute the prepared statement
  const result = await connection.execute(preparedStatement);
  return result;
}

/**
 * Gets all rows from a query result
 * @param result - Query result
 * @returns Array of row objects
 */
export function getAllRows(result: any): any[] {
  const rows = [];
  while (result.hasNext()) {
    rows.push(result.getNext());
  }
  return rows;
}

// Re-export the kuzu module for direct access if needed
export { kuzu };