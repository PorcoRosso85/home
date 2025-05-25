/**
 * LocationURI検証Cypherクエリテスト (最小構成)
 */

import { describe, it } from "https://deno.land/std@0.224.0/testing/bdd.ts";
import { assertEquals, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";

describe("LocationURI検証クエリテスト", () => {
  it("正常ケース: プロジェクト形式URI", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      const result = await conn.query(`
        WITH '<myproject>/srs/authentication/user-validation' as uri
        WITH uri =~ '^<[a-zA-Z0-9_-]+>/srs/.+$' as is_valid
        RETURN { is_valid: is_valid, uri: uri } as result
      `);
      const rows = await result.getAll();
      
      assertEquals(rows[0]["result"]["is_valid"], true, "有効なLocationURI");
      assertEquals(rows[0]["result"]["uri"], '<myproject>/srs/authentication/user-validation');
    } finally {
      await conn.close();
      await db.close();
    }
  });

  it("エラー: 無効なプロジェクト形式", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      const result = await conn.query(`
        WITH 'project/api/test' as uri
        WITH uri =~ '^<[a-zA-Z0-9_-]+>/srs/.+$' as is_valid
        RETURN { is_valid: is_valid } as result
      `);
      const rows = await result.getAll();
      
      assertEquals(rows[0]["result"]["is_valid"], false, "プロジェクト形式違反");
    } finally {
      await conn.close();
      await db.close();
    }
  });
});