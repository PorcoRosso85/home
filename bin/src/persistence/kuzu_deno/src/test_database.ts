import { assertEquals, assertExists } from "https://deno.land/std@0.224.0/assert/mod.ts";

// Step 2.2: 仕様の定義【RED】→【GREEN】
// インメモリデータベース接続をDenoで実現
Deno.test("Create in-memory database", async () => {
  const kuzu = await import("npm:kuzu-wasm");
  const Database = kuzu.default.Database;
  
  // インメモリデータベースを作成
  const db = new Database(":memory:");
  assertExists(db);
  assertEquals(typeof db, "object");
  
  // Connectionを作成
  const conn = new kuzu.default.Connection(db);
  assertExists(conn);
  assertEquals(typeof conn, "object");
  
  // クリーンアップ
  await conn.close();
  await db.close();
});

Deno.test("Execute simple Cypher query", async () => {
  const kuzu = await import("npm:kuzu-wasm");
  const { Database, Connection } = kuzu.default;
  
  const db = new Database(":memory:");
  const conn = new Connection(db);
  
  // スキーマ作成
  const createResult = await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))");
  assertExists(createResult);
  
  // データ挿入
  const insertResult = await conn.query("CREATE (n:Person {name: 'Alice', age: 30})");
  assertExists(insertResult);
  
  // データ検索
  const selectResult = await conn.query("MATCH (n:Person) RETURN n.name, n.age");
  const rows = await selectResult.getAllObjects();
  
  assertEquals(rows.length, 1);
  assertEquals(rows[0]["n.name"], "Alice");
  assertEquals(rows[0]["n.age"], 30);
  
  // クリーンアップ
  await selectResult.close();
  await conn.close();
  await db.close();
});