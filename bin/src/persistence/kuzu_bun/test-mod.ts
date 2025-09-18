#!/usr/bin/env bun
/**
 * Test mod.ts library interface
 */

import { loadKuzu, createDatabase, createConnection, executeQuery } from './mod';

async function testLibrary() {
  console.log('📚 Testing library interface via mod.ts...');
  
  const kuzu = await loadKuzu();
  console.log('✅ Module loaded');
  
  const db = createDatabase(kuzu);
  console.log('✅ Database created');
  
  const conn = createConnection(kuzu, db);
  console.log('✅ Connection established');
  
  await executeQuery(conn, "CREATE NODE TABLE Test(id INT64, PRIMARY KEY(id))");
  console.log('✅ Schema created');
  
  await executeQuery(conn, "CREATE (:Test {id: 1})");
  const results = await executeQuery(conn, "MATCH (t:Test) RETURN t.id");
  console.log('✅ Query executed:', results);
  
  await conn.close();
  await db.close();
  await kuzu.close();
  console.log('✅ Cleanup complete');
}

testLibrary().catch(console.error);