/**
 * KuzuDB基本クエリテスト
 */

import { describe, it } from "https://deno.land/std@0.224.0/testing/bdd.ts";
import { assertEquals, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";

describe("KuzuDB直接クエリテスト", () => {
  it("インメモリKuzuDBでの基本動作確認", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      await conn.query("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))");
      await conn.query("CREATE (u:User {name: 'Alice', age: 30})");
      
      const result = await conn.query("MATCH (u:User) RETURN u.name, u.age");
      const rows = await result.getAll();
      
      assert(rows.length > 0, "クエリ結果が存在すべき");
    } finally {
      await conn.close();
      await db.close();
    }
  });
});
