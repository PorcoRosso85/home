#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - 未実装要件特定機能テスト
 * 
 * このファイルは「開発・実装支援」ユースケースから
 * 「未実装要件の特定」機能をテストします。
 */

import { setupDatabase, closeDatabase } from "../common/database.ts";
import { createSchema, insertSampleData, insertExtendedTestData } from "../common/test_data.ts";
import { UnimplementedResult, formatUnimplementedRequirements } from "../common/result_formatter.ts";

/**
 * 追加機能: 未実装要件の特定
 * 未実装の要件を検索する関数
 */
async function findUnimplementedRequirements(conn: any): Promise<UnimplementedResult[]> {
  const query = `
    MATCH (r:RequirementEntity)
    WHERE NOT EXISTS {
      MATCH (r)<-[:IMPLEMENTS]-(c:CodeEntity)
      WHERE c.type <> 'test'
    }
    RETURN r.id as requirement_id, r.title as title
  `;
  
  const response = await conn.query(query);
  const rows = await response.getAll();
  
  const results: UnimplementedResult[] = [];
  for (const row of rows) {
    results.push({
      requirement_id: row.requirement_id || "",
      title: row.title || ""
    });
  }
  
  return results;
}

/**
 * 未実装要件特定テストを実行する関数
 */
async function runUnimplementedRequirementsTest(): Promise<boolean> {
  console.log("未実装要件特定テスト開始");
  
  // データベースをセットアップ
  const dbName = "unimplemented_requirements_db";
  const { db, conn } = await setupDatabase(dbName);
  
  try {
    // テスト1: 基本データでの未実装要件
    console.log("\n==== テスト1: 基本データでの未実装要件 ====\n");
    
    // スキーマと基本テストデータの準備
    await createSchema(conn);
    await insertSampleData(conn);
    
    console.log("基本データでの未実装要件を検索中...");
    const basicResults = await findUnimplementedRequirements(conn);
    
    console.log(`検索結果: ${basicResults.length}件の未実装要件が見つかりました`);
    
    // 結果の検証 - 基本データではすべての要件が実装されている
    if (basicResults.length !== 0) {
      console.error(`テスト失敗: 基本データではすべての要件が実装されているはずですが、${basicResults.length}件の未実装要件が見つかりました`);
      return false;
    }
    
    const formattedBasicResults = formatUnimplementedRequirements(basicResults);
    console.log(formattedBasicResults);
    
    // テスト2: 拡張データでの未実装要件
    console.log("\n==== テスト2: 拡張データに存在する未実装要件 ====\n");
    
    // 一旦データベースをクリーンアップしてから拡張テストデータを挿入
    await closeDatabase(db, conn);
    const { db: db2, conn: conn2 } = await setupDatabase(dbName);
    
    // スキーマと拡張テストデータの準備
    await createSchema(conn2);
    
    // 要件を追加してから、意図的に一部の要件に実装を与えない
    await conn2.query("CREATE (req5:RequirementEntity {id: 'REQ-005', title: 'データ永続化', description: 'システムはユーザーデータを永続化できること', priority: 'HIGH', requirement_type: 'functional'})");
    await conn2.query("CREATE (req6:RequirementEntity {id: 'REQ-006', title: 'レスポンスタイム', description: 'ユーザー検索のレスポンスタイムは500ms以下であること', priority: 'MEDIUM', requirement_type: 'performance'})");
    await conn2.query("CREATE (req7:RequirementEntity {id: 'REQ-007', title: '設定管理', description: 'システム設定を外部ファイルで管理できること', priority: 'LOW', requirement_type: 'functional'})");
    
    // REQ-005とREQ-007は実装を与えない
    await conn2.query("CREATE (loc8:LocationURI {uri_id: 'loc8', scheme: 'requirement', authority: 'project', path: '/non-functional/performance', fragment: '', query: ''})");
    await conn2.query("MATCH (r:RequirementEntity {id: 'REQ-006'}), (l:LocationURI {uri_id: 'loc8'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)");
    
    await conn2.query("CREATE (code9:CodeEntity {persistent_id: 'CODE-009', name: 'findUserById', type: 'function', signature: 'public User findUserById(Long id)', complexity: 2, start_position: 1350, end_position: 1400})");
    await conn2.query("CREATE (loc6:LocationURI {uri_id: 'loc6', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/repository', fragment: '', query: ''})");
    await conn2.query("MATCH (c:CodeEntity {persistent_id: 'CODE-009'}), (l:LocationURI {uri_id: 'loc6'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
    await conn2.query("MATCH (c:CodeEntity {persistent_id: 'CODE-009'}), (r:RequirementEntity {id: 'REQ-006'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)");
    
    console.log("拡張データでの未実装要件を検索中...");
    const extendedResults = await findUnimplementedRequirements(conn2);
    
    console.log(`検索結果: ${extendedResults.length}件の未実装要件が見つかりました`);
    
    // 結果の検証 - 拡張データでは2つの要件が未実装
    if (extendedResults.length !== 2) {
      console.error(`テスト失敗: 拡張データでは2つの要件が未実装であるはずですが、${extendedResults.length}件見つかりました`);
      return false;
    }
    
    // 未実装要件のIDの確認
    const unimplementedIds = extendedResults.map(result => result.requirement_id);
    if (!unimplementedIds.includes('REQ-005') || !unimplementedIds.includes('REQ-007')) {
      console.error(`テスト失敗: REQ-005とREQ-007が未実装であるはずですが、${unimplementedIds.join(', ')}が見つかりました`);
      return false;
    }
    
    const formattedExtendedResults = formatUnimplementedRequirements(extendedResults);
    console.log(formattedExtendedResults);
    
    // テスト終了
    await closeDatabase(db2, conn2);
    
    console.log("\n全てのテストが成功しました");
    return true;
  } catch (error) {
    console.error("テスト実行中にエラーが発生しました:", error);
    return false;
  } finally {
    // データベース接続を閉じる
    try {
      await closeDatabase(db, conn);
    } catch (error) {
      // 既に閉じている場合は無視
    }
  }
}

// メイン実行部分
if (import.meta.main) {
  runUnimplementedRequirementsTest()
    .then((success) => {
      if (success) {
        console.log("未実装要件特定テスト成功");
        Deno.exit(0);
      } else {
        console.error("未実装要件特定テスト失敗");
        Deno.exit(1);
      }
    })
    .catch((error) => {
      console.error("予期しないエラー:", error);
      Deno.exit(1);
    });
}

// Deno.testでのテスト定義（外部からのインポート用）
Deno.test("未実装要件特定機能", async () => {
  const success = await runUnimplementedRequirementsTest();
  if (!success) {
    throw new Error("未実装要件特定テストが失敗しました");
  }
});
