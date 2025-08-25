import { test } from "node:test";
import assert from "node:assert/strict";

test("Basic kuzu-wasm loading", async () => {
  const { createRequire } = await import('module');
  const require = createRequire(import.meta.url || process.cwd());
  const kuzu = require('kuzu-wasm/nodejs');
  
  // Create in-memory database
  const db = new kuzu.Database(':memory:', 1 << 28);
  const conn = new kuzu.Connection(db, 4);
  
  // Create schema
  const schemaResult = await conn.query("CREATE NODE TABLE Person(name STRING, PRIMARY KEY(name))");
  await schemaResult.close();
  
  // Insert data
  const insertResult = await conn.query("CREATE (:Person {name: 'Alice'})");
  await insertResult.close();
  
  // Query data
  const queryResult = await conn.query("MATCH (p:Person) RETURN p.name as name");
  const rows = await queryResult.getAllObjects();
  await queryResult.close();
  
  // Verify
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].name, 'Alice');
  
  // Cleanup
  await conn.close();
  await db.close();
  
  console.log('✅ Basic test passed');
});