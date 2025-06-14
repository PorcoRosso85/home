/**
 * VersionBatch統合検証Cypherクエリテスト (最小構成)
 */

import { describe, it } from "https://deno.land/std@0.224.0/testing/bdd.ts";
import { assertEquals, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";

describe("VersionBatch統合検証クエリテスト", () => {
  it("正常ケース: 完全なVersionBatch", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      const result = await conn.query(`
        WITH 'v1.0.0' as version_id, 
             ['<project>/srs/auth', '<project>/srs/api'] as location_uris,
             'v0.9.0' as previous_version_id
        WITH version_id, location_uris, previous_version_id,
             CASE 
               WHEN size(trim(version_id)) = 0 THEN 'version_id cannot be empty'
               WHEN size(location_uris) = 0 THEN 'location_uris cannot be empty'
               ELSE null
             END as error
        RETURN {
          is_valid: error IS null,
          version_id: version_id,
          uri_count: size(location_uris)
        } as result
      `);
      const rows = await result.getAll();
      
      assertEquals(rows[0]["result"]["is_valid"], true, "有効なVersionBatch");
      assertEquals(rows[0]["result"]["version_id"], 'v1.0.0');
    } finally {
      await conn.close();
      await db.close();
    }
  });

  it("エラー: 空のversion_id", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      const result = await conn.query(`
        WITH '' as version_id
        WITH size(trim(version_id)) = 0 as is_empty
        RETURN { is_valid: NOT is_empty } as result
      `);
      const rows = await result.getAll();
      
      assertEquals(rows[0]["result"]["is_valid"], false, "空のversion_idは無効");
    } finally {
      await conn.close();
      await db.close();
    }
  });
});