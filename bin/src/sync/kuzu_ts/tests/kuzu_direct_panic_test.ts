/**
 * Direct KuzuDB panic reproduction test
 * npm:kuzuを直接使用してV8 isolateクラッシュを再現
 */

import { assertEquals } from "jsr:@std/assert@^1.0.0";

Deno.test("Direct npm:kuzu usage causes panic", async () => {
  console.log("Importing npm:kuzu directly...");
  
  try {
    // npm:kuzuを直接インポート（これがパニックの原因）
    const kuzu = await import("npm:kuzu@0.10.0");
    console.log("KuzuDB module imported:", Object.keys(kuzu));
    
    // データベース作成を試みる
    console.log("Creating database...");
    const db = new kuzu.Database(":memory:");
    console.log("Database created");
    
    // 接続作成を試みる
    console.log("Creating connection...");
    const conn = new kuzu.Connection(db);
    console.log("Connection created");
    
    // クエリ実行を試みる
    console.log("Executing query...");
    const result = await conn.query(`
      CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))
    `);
    console.log("Query executed");
    
    // ここまで到達したら成功
    assertEquals(true, true);
  } catch (error) {
    console.error("Error occurred:", error);
    throw error;
  }
});