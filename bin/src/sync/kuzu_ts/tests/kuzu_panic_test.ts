/**
 * KuzuDB panic reproduction test
 * KuzuDBのV8 isolateクラッシュ問題を再現するテスト
 */

import { assertEquals } from "jsr:@std/assert@^1.0.0";
import { KuzuTsClient } from "../core/client/kuzu_ts_client.ts";

Deno.test("KuzuDB direct usage causes panic", async () => {
  console.log("Creating KuzuDB client directly...");
  
  try {
    // KuzuDBクライアントを直接作成
    const client = new KuzuTsClient({
      databasePath: ":memory:",
      bufferPoolSize: 64 * 1024 * 1024
    });
    
    // クエリ実行を試みる
    console.log("Executing query...");
    const result = await client.executeCypher(`
      CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))
    `);
    
    console.log("Query executed:", result);
    
    // クリーンアップ
    await client.cleanup();
    
    // ここまで到達したら成功
    assertEquals(true, true);
  } catch (error) {
    console.error("Error occurred:", error);
    throw error;
  }
});