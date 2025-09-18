#!/usr/bin/env -S deno run --allow-read --allow-write --allow-net --allow-env

// When running via flake, import from the path provided by environment
const kuzuPath = Deno.env.get("KUZU_TS_PATH") || "../../../persistence/kuzu_ts";
const { createDatabase, createConnection } = await import(`${kuzuPath}/mod.ts`);

async function main() {
  console.log("=== KuzuDB TypeScript Sample (via flake) ===\n");
  
  try {
    // Create in-memory database
    const db = await createDatabase(":memory:");
    console.log("✓ Database created");
    
    // Create connection
    const conn = await createConnection(db);
    console.log("✓ Connection created");
    
    // Create schema
    await conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))");
    console.log("✓ Schema created");
    
    // Insert data
    await conn.execute("CREATE (:Person {name: 'Alice', age: 30})");
    await conn.execute("CREATE (:Person {name: 'Bob', age: 25})");
    console.log("✓ Data inserted");
    
    // Query data
    const result = await conn.execute("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
    const rows = await result.getAll();
    
    console.log("\n✓ Query results:");
    for (const row of rows) {
      console.log(`  - ${row["p.name"]}: ${row["p.age"]}`);
    }
    
    console.log("\n✓ Persistence module works!");
    
  } catch (error) {
    console.error("✗ Error:", error);
    Deno.exit(1);
  }
}

if (import.meta.main) {
  await main();
}