/**
 * VersionState検証Cypherクエリテスト (最小構成)
 */

import { describe, it } from "https://deno.land/std@0.224.0/testing/bdd.ts";
import { assertEquals, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";

describe("VersionState検証クエリテスト", () => {
  it("正常ケース: 完全なVersionState", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      const result = await conn.query(`
        WITH 'v1.0.0' as id, '2025-01-22T10:30:00.000Z' as timestamp
        WITH id, timestamp,
             CASE 
               WHEN size(trim(id)) = 0 THEN 'id cannot be empty'
               WHEN NOT timestamp =~ '^\\\\d{4}-\\\\d{2}-\\\\d{2}T\\\\d{2}:\\\\d{2}:\\\\d{2}(\\\\.\\\\d{3})?Z$' 
                 THEN 'timestamp must be in ISO 8601 format'
               ELSE null
             END as error
        RETURN {
          is_valid: error IS null,
          id: id,
          timestamp: timestamp
        } as result
      `);
      const rows = await result.getAll();
      
      assertEquals(rows[0]["result"]["is_valid"], true, "有効なVersionState");
      assertEquals(rows[0]["result"]["id"], 'v1.0.0', "IDが保持される");
    } finally {
      await conn.close();
      await db.close();
    }
  });

  it("エラー: 無効なISO8601タイムスタンプ", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      const result = await conn.query(`
        WITH '2025-01-22 10:30:00' as timestamp
        WITH timestamp =~ '^\\\\d{4}-\\\\d{2}-\\\\d{2}T\\\\d{2}:\\\\d{2}:\\\\d{2}(\\\\.\\\\d{3})?Z$' as is_valid
        RETURN { is_valid: is_valid } as result
      `);
      const rows = await result.getAll();
      
      assertEquals(rows[0]["result"]["is_valid"], false, "無効なタイムスタンプ形式");
    } finally {
      await conn.close();
      await db.close();
    }
  });
});