/**
 * URI制約検証DQLクエリテスト
 */

import { describe, it } from "https://deno.land/std@0.224.0/testing/bdd.ts";
import { assertEquals, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";

describe("URI制約検証DQLクエリテスト", () => {
  it("有効なURIパターンのマッチング", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      await conn.query("CREATE NODE TABLE uri(path STRING, PRIMARY KEY (path))");
      await conn.query("CREATE (u:uri {path: '<myproject>/srs/auth'})");
      await conn.query("CREATE (u:uri {path: '<test-proj>/srs/requirements/performance'})");
      await conn.query("CREATE (u:uri {path: '<proj_123>/srs/a/b/c/deep/path'})");
      
      const result = await conn.query(`
        MATCH (u:uri)
        WHERE u.path =~ '^<[^>]+>/srs/.+$'
        RETURN u.path ORDER BY u.path
      `);
      const rows = await result.getAll();
      
      assertEquals(rows.length, 3, "有効なURIは3件存在すべき");
      assertEquals(rows[0]["u.path"], "<myproject>/srs/auth");
      assertEquals(rows[1]["u.path"], "<proj_123>/srs/a/b/c/deep/path");
      assertEquals(rows[2]["u.path"], "<test-proj>/srs/requirements/performance");
    } finally {
      await conn.close();
      await db.close();
    }
  });

  it("無効なURIパターンの検出", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      await conn.query("CREATE NODE TABLE uri(path STRING, PRIMARY KEY (path))");
      await conn.query("CREATE (u:uri {path: 'myproject/srs/test'})");
      await conn.query("CREATE (u:uri {path: '<project>/api/test'})");
      await conn.query("CREATE (u:uri {path: '<>/srs/test'})");
      
      const result = await conn.query(`
        MATCH (u:uri)
        WHERE NOT u.path =~ '^<[^>]+>/srs/.+$'
        RETURN u.path ORDER BY u.path
      `);
      const rows = await result.getAll();
      
      assertEquals(rows.length, 3, "無効なURIは3件存在すべき");
      assertEquals(rows[0]["u.path"], "<>/srs/test");
      assertEquals(rows[1]["u.path"], "<project>/api/test");
      assertEquals(rows[2]["u.path"], "myproject/srs/test");
    } finally {
      await conn.close();
      await db.close();
    }
  });
});
