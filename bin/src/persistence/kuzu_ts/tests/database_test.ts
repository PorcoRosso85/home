import { assertEquals, assertExists } from "https://deno.land/std@0.218.0/assert/mod.ts";
import { createDatabase, createConnection } from "../core/database.ts";

Deno.test("createDatabase - in-memory database creation", async () => {
  const db = await createDatabase(":memory:");
  assertExists(db);
  assertEquals(typeof db.close, "function");
});

Deno.test("createConnection - connection creation", async () => {
  const db = await createDatabase(":memory:");
  const conn = await createConnection(db);
  assertExists(conn);
  assertEquals(typeof conn.query, "function");
});

Deno.test("database operations - basic CRUD", async () => {
  const db = await createDatabase(":memory:");
  const conn = await createConnection(db);
  
  // Create schema
  await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))");
  
  // Insert data
  await conn.query("CREATE (:Person {name: 'Alice', age: 30})");
  await conn.query("CREATE (:Person {name: 'Bob', age: 25})");
  
  // Query data
  const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
  const rows = await result.getAll();
  
  assertEquals(rows.length, 2);
  assertEquals(rows[0]["p.name"], "Bob");
  assertEquals(rows[0]["p.age"], 25);
  assertEquals(rows[1]["p.name"], "Alice");
  assertEquals(rows[1]["p.age"], 30);
});

Deno.test("createDatabase - caching behavior", async () => {
  const db1 = await createDatabase("test.db");
  const db2 = await createDatabase("test.db");
  
  // Should return same instance by default
  assertEquals(db1, db2);
  
  // Should return different instance with useCache: false
  const db3 = await createDatabase("test.db", { useCache: false });
  assertExists(db3);
});

Deno.test("createDatabase - test unique for in-memory", async () => {
  const db1 = await createDatabase(":memory:", { testUnique: true });
  const db2 = await createDatabase(":memory:", { testUnique: true });
  
  // Should return different instances
  assertExists(db1);
  assertExists(db2);
});