/**
 * Domain: Pure KuzuDB operations
 */

import type { KuzuModule } from './infrastructure';

export type QueryResult = {
  getAllObjects: () => Promise<any[]>;
  close: () => Promise<void>;
};

export type Connection = {
  query: (cypher: string) => Promise<QueryResult>;
  close: () => Promise<void>;
};

export type Database = {
  close: () => Promise<void>;
};

export function createDatabase(kuzu: KuzuModule, path = ':memory:', size = 1 << 28): Database {
  return new kuzu.Database(path, size);
}

export function createConnection(kuzu: KuzuModule, db: Database, threads = 4): Connection {
  return new kuzu.Connection(db, threads);
}

export async function executeQuery(conn: Connection, cypher: string): Promise<any[]> {
  const result = await conn.query(cypher);
  const data = await result.getAllObjects();
  await result.close();
  return data;
}