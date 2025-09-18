import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';

describe('KuzuDB with Vitest', () => {
  it('should load kuzu-wasm module', async () => {
    const require = createRequire(import.meta.url || process.cwd());
    const kuzu = require('kuzu-wasm/nodejs');
    
    expect(kuzu).toBeDefined();
    expect(kuzu.Database).toBeDefined();
    expect(kuzu.Connection).toBeDefined();
  });

  it('should create in-memory database and execute queries', async () => {
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
    expect(rows).toHaveLength(1);
    expect(rows[0].name).toBe('Alice');
    
    // Cleanup
    await conn.close();
    await db.close();
  });

  it('should work with refactored functions', async () => {
    const { loadKuzu, createKuzuDatabase, cleanupKuzu } = await import('../mod');
    const { executeQuery } = await import('../mod');
    
    const kuzu = await loadKuzu();
    const { db, conn } = createKuzuDatabase(kuzu);
    
    try {
      await executeQuery(conn, "CREATE NODE TABLE Test(id INT64, PRIMARY KEY(id))");
      await executeQuery(conn, "CREATE (:Test {id: 1})");
      const results = await executeQuery(conn, "MATCH (t:Test) RETURN t.id as id");
      
      expect(results).toHaveLength(1);
      expect(Number(results[0].id)).toBe(1);
    } finally {
      await cleanupKuzu({ conn, db, kuzu });
    }
  });
});