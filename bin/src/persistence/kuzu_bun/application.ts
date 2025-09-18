/**
 * Application: Use cases for KuzuDB
 */

import { loadKuzu } from './infrastructure';
import { createDatabase, createConnection, executeQuery } from './domain';

export async function runInMemoryExample() {
  const kuzu = await loadKuzu();
  const db = createDatabase(kuzu);
  const conn = createConnection(kuzu, db);

  // Schema
  await executeQuery(conn, "CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))");
  
  // Data
  await executeQuery(conn, "CREATE (:Person {name: 'Alice', age: 30})");
  await executeQuery(conn, "CREATE (:Person {name: 'Bob', age: 25})");
  
  // Query
  const results = await executeQuery(conn, "MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
  
  // Cleanup
  await conn.close();
  await db.close();
  await kuzu.close();
  
  return results;
}