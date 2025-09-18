// FIXME the test
/**
 * LocationURI検証テスト（配列インデックス修正版）
 */

import { describe, it } from "https://deno.land/std@0.224.0/testing/bdd.ts";
import { assertEquals, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";

describe("LocationURI検証テスト - 実際の機能検証", () => {
  
  async function executeValidation(conn: any, locationUriData: any) {
    // 配列インデックス修正: STRING_SPLIT結果の正しいインデックス使用
    const result = await conn.query(`
      WITH {id: '${locationUriData.id}'} as data,
           ['file', 'http', 'https', 'requirement', 'test', 'document'] as allowed_schemes,
           ['file', 'requirement', 'test', 'document'] as fragment_required_schemes

      // 基本検証
      WITH data, allowed_schemes, fragment_required_schemes,
           CASE 
             WHEN data.id IS NULL THEN 'id is required and must be a string'
             WHEN size(trim(data.id)) = 0 THEN 'id cannot be empty'
             ELSE null
           END as id_error

      // スキーマ・フラグメント抽出（配列インデックス修正）
      WITH data, allowed_schemes, fragment_required_schemes, id_error,
           CASE WHEN id_error IS NULL AND contains(data.id, ':') 
                THEN STRING_SPLIT(data.id, ':')[0]  // スキーマは最初の要素
                ELSE null 
           END as scheme,
           CASE WHEN id_error IS NULL AND contains(data.id, '#') 
                THEN STRING_SPLIT(data.id, '#')[1]  // フラグメントは2番目の要素
                ELSE '' 
           END as fragment
      // スキーマ検証  
      WITH data, fragment_required_schemes, id_error, scheme, fragment,
           CASE 
             WHEN id_error IS NULL AND scheme IS NOT NULL AND NOT scheme IN allowed_schemes 
               THEN 'Invalid scheme ' + scheme
             ELSE null
           END as scheme_error

      // フラグメント必須チェック
      WITH data, id_error, scheme, fragment, scheme_error,
           CASE 
             WHEN id_error IS NULL AND scheme_error IS NULL AND scheme IN fragment_required_schemes AND fragment = ''
               THEN 'Fragment is required for scheme ' + scheme
             ELSE null
           END as fragment_required_error

      // フラグメントパターン検証
      WITH data, id_error, scheme, fragment, scheme_error, fragment_required_error,
           CASE 
             WHEN id_error IS NULL AND scheme_error IS NULL AND fragment_required_error IS NULL AND fragment <> '' THEN
               CASE 
                 WHEN scheme = 'file' AND NOT fragment =~ '^L\\\\d+(-L\\\\d+)?$' 
                   THEN 'Invalid file fragment. Expected: L10 or L10-L25'
                 WHEN scheme = 'requirement' AND NOT fragment =~ '^REQ-[A-Z0-9]+-\\\\d+$' 
                   THEN 'Invalid requirement fragment. Expected: REQ-AUTH-001'
                 ELSE null
               END
             ELSE null
           END as fragment_pattern_error

      // エラー集約（直接判定）
      WITH id_error, scheme_error, fragment_required_error, fragment_pattern_error
      
      RETURN {
        is_valid: id_error IS NULL AND scheme_error IS NULL AND fragment_required_error IS NULL AND fragment_pattern_error IS NULL,
        id_error: id_error,
        scheme_error: scheme_error,
        fragment_required_error: fragment_required_error,
        fragment_pattern_error: fragment_pattern_error
      } as result
    `);
    
    return result;
  }

  it("必須機能: file スキーマの完全検証", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      // 正常ケース: file with valid fragment
      const validResult = await executeValidation(conn, { id: 'file:///src/auth.js#L10-L25' });
      const valid = await validResult.getAll();
      assertEquals(valid[0]["result"]["is_valid"], true, "有効なfileスキーマ");

      // 異常ケース: file without required fragment  
      const noFragmentResult = await executeValidation(conn, { id: 'file:///src/auth.js' });
      const noFragment = await noFragmentResult.getAll();
      assertEquals(noFragment[0]["result"]["is_valid"], false, "フラグメント必須違反");
      assert(noFragment[0]["result"]["fragment_required_error"] !== null, "フラグメント必須エラー");
      
    } finally {
      await conn.close();
      await db.close();
    }
  });

  it("必須機能: 無効スキーマの検出", async () => {
    const kuzu = await import("npm:kuzu");
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      // 無効スキーマ
      const invalidResult = await executeValidation(conn, { id: 'invalid:///test' });
      const invalid = await invalidResult.getAll();
      assertEquals(invalid[0]["result"]["is_valid"], false, "無効スキーマ検出");
      assert(invalid[0]["result"]["scheme_error"] !== null, "スキーマエラー");

      // 空のID
      const emptyResult = await executeValidation(conn, { id: '' });
      const empty = await emptyResult.getAll();
      assertEquals(empty[0]["result"]["is_valid"], false, "空ID検出");
      assert(empty[0]["result"]["id_error"] !== null, "空IDエラー");
      
    } finally {
      await conn.close();
      await db.close();
    }
  });
});
