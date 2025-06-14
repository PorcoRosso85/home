/**
 * SemVer検証Cypherクエリテスト (最小構成)
 */

import { describe, it } from "https://deno.land/std@0.224.0/testing/bdd.ts";
import { assertEquals, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";

describe("SemVer検証クエリテスト", () => {
  it("基本形式: v1.2.3 (正常)", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      const result = await conn.query(`
        WITH 'v1.2.3' as input_version, false as strict_mode
        WITH CASE 
               WHEN starts_with(input_version, 'v') THEN substring(input_version, 2, size(input_version)-1)
               ELSE input_version 
             END as clean_version, strict_mode
        WITH clean_version, strict_mode,
             clean_version =~ '^\\\\d+(\\\\.\\\\d+)*$' as basic_valid
        RETURN {
          is_valid: basic_valid,
          clean_version: clean_version,
          has_v_prefix: starts_with('v1.2.3', 'v')
        } as result
      `);
      const rows = await result.getAll();
      
      assertEquals(rows[0]["result"]["is_valid"], true, "v1.2.3は有効なバージョン");
      assertEquals(rows[0]["result"]["clean_version"], "1.2.3", "vプレフィックスが除去されるべき");
      assertEquals(rows[0]["result"]["has_v_prefix"], true, "vプレフィックス検出");
    } finally {
      await conn.close();
      await db.close();
    }
  });

  it("エラー: 無効文字 (v1.2.a)", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      const result = await conn.query(`
        WITH 'v1.2.a' as input_version
        WITH substring(input_version, 2, size(input_version)-1) as clean_version
        WITH clean_version =~ '^\\\\d+(\\\\.\\\\d+)*$' as basic_valid
        RETURN { is_valid: basic_valid } as result
      `);
      const rows = await result.getAll();
      
      assertEquals(rows[0]["result"]["is_valid"], false, "無効文字は無効");
    } finally {
      await conn.close();
      await db.close();
    }
  });
});