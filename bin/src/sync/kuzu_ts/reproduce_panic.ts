#!/usr/bin/env -S deno run --allow-all

/**
 * KuzuDB with @kuzu-ts package test
 * パッケージ化されたkuzu_tsモジュールを使用
 */

console.log("=== KuzuDB with @kuzu-ts Package Test ===");
console.log("1. Importing @kuzu-ts modules...");

try {
  const { createDatabase, createConnection } = await import("@kuzu-ts/worker");
  console.log("2. Module imported successfully");
  
  console.log("3. Creating in-memory database via Worker...");
  const db = await createDatabase(":memory:");
  console.log("4. Database created");
  
  console.log("5. Creating connection...");
  const conn = await createConnection(db);
  console.log("6. Connection created");
  
  console.log("7. Executing DDL query...");
  await conn.query(`CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))`);
  console.log("8. DDL executed successfully");
  
  console.log("9. Inserting data...");
  await conn.query(`CREATE (:Person {name: 'Alice', age: 30})`);
  console.log("10. Data inserted");
  
  console.log("✅ All operations completed successfully with @kuzu-ts!");
} catch (error) {
  console.error("❌ Error occurred:", error);
  console.error("Stack trace:", error.stack);
}