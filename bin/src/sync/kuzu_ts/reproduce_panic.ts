#!/usr/bin/env -S deno run --allow-all

/**
 * KuzuDB panic reproduction script
 * 実行すると即座にV8 isolateクラッシュが発生する
 */

console.log("=== KuzuDB Panic Reproduction ===");
console.log("1. Importing npm:kuzu...");

try {
  const kuzu = await import("kuzu");
  console.log("2. Module imported successfully");
  
  console.log("3. Creating in-memory database...");
  const db = new kuzu.Database(":memory:");
  console.log("4. Database created");
  
  console.log("5. Creating connection...");
  const conn = new kuzu.Connection(db);
  console.log("6. Connection created");
  
  console.log("7. Executing DDL query...");
  await conn.query(`CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))`);
  console.log("8. DDL executed successfully");
  
  console.log("9. Inserting data...");
  await conn.query(`CREATE (:Person {name: 'Alice', age: 30})`);
  console.log("10. Data inserted");
  
  console.log("✅ All operations completed without panic!");
} catch (error) {
  console.error("❌ Error occurred:", error);
  console.error("Stack trace:", error.stack);
}