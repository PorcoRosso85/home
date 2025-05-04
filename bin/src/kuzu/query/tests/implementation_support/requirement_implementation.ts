#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - 要件の実装状況追跡機能テスト
 * 
 * このファイルは「開発・実装支援」ユースケースから
 * 「特定要件の実装状況の追跡」機能をテストします。
 */

import { setupDatabase, closeDatabase } from "../common/database.ts";
import { createSchema, insertSampleData } from "../common/test_data.ts";
import { ImplementationResult, formatImplementationStatus } from "../common/result_formatter.ts";

/**
 * ユースケース2: 要件の実装状況追跡
 * 指定した要件IDの実装状況を追跡する関数
 */
async function trackRequirementImplementation(conn: any, requirementId: string): Promise<ImplementationResult[]> {
  const query = `
    MATCH (r:RequirementEntity)<-[impl:IMPLEMENTS]-(c:CodeEntity)
    WHERE r.id = '${requirementId}'
    OPTIONAL MATCH (c)-[:HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           c.persistent_id as code_id, 
           c.name as code_name,
           c.type as code_type,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as code_location
  `;
  
  const response = await conn.query(query);
  const rows = await response.getAll();
  
  const results: ImplementationResult[] = [];
  for (const row of rows) {
    results.push({
      requirement_id: row.requirement_id || "",
      requirement_title: row.requirement_title || "",
      requirement_type: row.requirement_type || "",
      code_id: row.code_id || "",
      code_name: row.code_name || "",
      code_type: row.code_type || "",
      implementation_type: row.implementation_type || "",
      code_location: row.code_location || ""
    });
  }
  
  return results;
}

/**
 * 要件の実装状況追跡テストを実行する関数
 */
async function runRequirementImplementationTest(): Promise<boolean> {
  console.log("要件の実装状況追跡テスト開始");
  
  // データベースをセットアップ
  const dbName = "requirement_implementation_db";
  const { db, conn } = await setupDatabase(dbName);
  
  try {
    // スキーマとテストデータの準備
    await createSchema(conn);
    await insertSampleData(conn);
    
    // テスト1: 機能要件（REQ-001）の実装状況
    console.log("\n==== テスト1: 機能要件の実装状況 ====\n");
    
    const reqId1 = 'REQ-001';
    console.log(`要件ID '${reqId1}' (ユーザー登録機能) の実装状況を検索中...`);
    const functionalResults = await trackRequirementImplementation(conn, reqId1);
    
    console.log(`検索結果: ${functionalResults.length}件の実装が見つかりました`);
    
    // 結果の検証
    if (functionalResults.length !== 2) {
      console.error(`テスト失敗: REQ-001は2つのコードエンティティによって実装されているはずですが、${functionalResults.length}件見つかりました`);
      return false;
    }
    
    // コードIDの確認
    const codeIds = functionalResults.map(result => result.code_id);
    if (!codeIds.includes('CODE-002') || !codeIds.includes('CODE-005')) {
      console.error(`テスト失敗: REQ-001はCODE-002とCODE-005によって実装されているはずですが、${codeIds.join(', ')}が見つかりました`);
      return false;
    }
    
    // 実装タイプの確認
    const codeById = functionalResults.reduce((acc, result) => {
      acc[result.code_id] = result;
      return acc;
    }, {} as Record<string, ImplementationResult>);
    
    if (codeById['CODE-002'].implementation_type !== 'IMPLEMENTS') {
      console.error(`テスト失敗: CODE-002の実装タイプはIMPLEMENTSであるはずですが、${codeById['CODE-002'].implementation_type}でした`);
      return false;
    }
    
    if (codeById['CODE-005'].implementation_type !== 'TESTS') {
      console.error(`テスト失敗: CODE-005の実装タイプはTESTSであるはずですが、${codeById['CODE-005'].implementation_type}でした`);
      return false;
    }
    
    const formattedFunctionalResults = formatImplementationStatus(functionalResults);
    console.log(formattedFunctionalResults);
    
    // テスト2: セキュリティ要件（REQ-003）の実装状況
    console.log("\n==== テスト2: セキュリティ要件の実装状況 ====\n");
    
    const reqId2 = 'REQ-003';
    console.log(`要件ID '${reqId2}' (パスワードポリシー) の実装状況を検索中...`);
    const securityResults = await trackRequirementImplementation(conn, reqId2);
    
    console.log(`検索結果: ${securityResults.length}件の実装が見つかりました`);
    
    // 結果の検証
    if (securityResults.length !== 1) {
      console.error(`テスト失敗: REQ-003は1つのコードエンティティによって実装されているはずですが、${securityResults.length}件見つかりました`);
      return false;
    }
    
    if (securityResults[0].code_id !== 'CODE-006') {
      console.error(`テスト失敗: REQ-003はCODE-006によって実装されているはずですが、${securityResults[0].code_id}が見つかりました`);
      return false;
    }
    
    if (securityResults[0].implementation_type !== 'IMPLEMENTS') {
      console.error(`テスト失敗: REQ-003の実装タイプはIMPLEMENTSであるはずですが、${securityResults[0].implementation_type}でした`);
      return false;
    }
    
    if (!securityResults[0].code_name.includes('validatePassword')) {
      console.error(`テスト失敗: REQ-003はvalidatePassword関数によって実装されているはずですが、${securityResults[0].code_name}が見つかりました`);
      return false;
    }
    
    const formattedSecurityResults = formatImplementationStatus(securityResults);
    console.log(formattedSecurityResults);
    
    console.log("\n全てのテストが成功しました");
    return true;
  } catch (error: unknown) {
    console.error("テスト実行中にエラーが発生しました:", error);
    return false;
  } finally {
    // データベース接続を閉じる
    await closeDatabase(db, conn);
  }
}

// メイン実行部分
if (import.meta.main) {
  runRequirementImplementationTest()
    .then((success) => {
      if (success) {
        console.log("要件の実装状況追跡テスト成功");
        Deno.exit(0);
      } else {
        console.error("要件の実装状況追跡テスト失敗");
        Deno.exit(1);
      }
    })
    .catch((error) => {
      console.error("予期しないエラー:", error);
      Deno.exit(1);
    });
}

// Deno.testでのテスト定義（外部からのインポート用）
Deno.test({
  name: "要件の実装状況追跡機能",
  fn: async () => {
    try {
      const success = await runRequirementImplementationTest();
      if (!success) {
        throw new Error("要件の実装状況追跡テストが失敗しました");
      }
    } catch (error: unknown) {
      console.error("テスト実行中にエラーが発生しました:", error);
      if (error instanceof Error) {
        console.error("スタックトレース:", error.stack);
      }
      throw error;
    }
  },
  permissions: {
    read: true,
    write: true,
    net: true,
  },
});
