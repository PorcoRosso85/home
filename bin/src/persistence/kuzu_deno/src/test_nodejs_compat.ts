import { assertEquals, assertExists } from "https://deno.land/std@0.224.0/assert/mod.ts";

// Node.js互換モードでkuzu-wasmを使用
// Denoはnpm:kuzu-wasm/nodejsパスをサポート
Deno.test("Load kuzu-wasm with Node.js compatibility", async () => {
  // Node.js用のエントリーポイントを明示的に指定
  const kuzu = await import("npm:kuzu-wasm/nodejs");
  
  assertExists(kuzu);
  assertEquals(typeof kuzu, "object");
  
  // Node.js版のAPIを確認
  console.log("Node.js kuzu keys:", Object.keys(kuzu));
  
  // Database クラスの存在確認
  assertExists(kuzu.Database);
  assertEquals(typeof kuzu.Database, "function");
});

Deno.test("Create database with Node.js API", async () => {
  const kuzu = await import("npm:kuzu-wasm/nodejs");
  
  // Node.js版のAPIでデータベース作成
  const db = new kuzu.Database(":memory:");
  assertExists(db);
  
  const conn = new kuzu.Connection(db);
  assertExists(conn);
  
  // 簡単なクエリテスト
  try {
    const result = await conn.query("RETURN 'Hello from Deno!' as message");
    assertExists(result);
    
    const rows = await result.getAllObjects();
    assertEquals(rows.length, 1);
    assertEquals(rows[0].message, "Hello from Deno!");
    
    await result.close();
  } finally {
    await conn.close();
    await db.close();
  }
});