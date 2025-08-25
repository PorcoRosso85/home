/**
 * Minimal example - just enough to work
 */

import { loadKuzu } from './kuzu-loader';

async function main() {
  const kuzu = await loadKuzu();
  const db = new kuzu.Database(':memory:', 1 << 28);
  const conn = new kuzu.Connection(db, 4);

  // Create and query
  await conn.query("CREATE NODE TABLE Person(name STRING, PRIMARY KEY(name))");
  await conn.query("CREATE (:Person {name: 'Alice'})");
  
  const result = await conn.query("MATCH (p:Person) RETURN p.name");
  const rows = await result.getAllObjects();
  console.log(rows);
  
  // Cleanup
  await result.close();
  await conn.close();
  await db.close();
  await kuzu.close();
}

// Run if executed directly (ESM style)
main().catch(console.error);