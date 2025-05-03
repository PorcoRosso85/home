#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - コードから要件への逆引き機能テスト
 * 
 * このファイルは「開発・実装支援」ユースケースから
 * 「特定コードの対応要件群の確認（逆引き）」機能をテストします。
 */

import { setupDatabase, closeDatabase } from "../common/database.ts";
import { createSchema, insertSampleData } from "../common/test_data.ts";
import { RequirementResult, formatRequirementsForCode } from "../common/result_formatter.ts";

/**
 * ユースケース1: コードエンティティから要件への逆引き
 * 指定したコードIDに関連する要件を検索する関数
 */
async function findRequirementsForCode(conn: any, codeId: string): Promise<RequirementResult[]> {
  // 直接実装している要件を検索するクエリ
  const query = `
    MATCH (c:CodeEntity)-[impl:IMPLEMENTS]->(r:RequirementEntity)
    WHERE c.persistent_id = '${codeId}'
    OPTIONAL MATCH (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           r.priority as requirement_priority,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as requirement_location,
           'direct' as relation_type
  `;
  
  const response = await conn.query(query);
  const rows = await response.getAll();
  const results: RequirementResult[] = [];
  
  for (const row of rows) {
    results.push({
      requirement_id: row.requirement_id || "",
      requirement_title: row.requirement_title || "",
      requirement_type: row.requirement_type || "",
      requirement_priority: row.requirement_priority || "",
      implementation_type: row.implementation_type || "",
      requirement_location: row.requirement_location || "",
      relation_type: row.relation_type || ""
    });
  }
  
  // 親コードエンティティの場合、子コードが実装している要件も検索
  const queryIndirect = `
    MATCH (parent:CodeEntity)-[:CONTAINS]->(child:CodeEntity)-[impl:IMPLEMENTS]->(r:RequirementEntity)
    WHERE parent.persistent_id = '${codeId}'
    OPTIONAL MATCH (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           r.priority as requirement_priority,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as requirement_location,
           'via_child_' + child.name as relation_type
  `;
  
  const responseIndirect = await conn.query(queryIndirect);
  const rowsIndirect = await responseIndirect.getAll();
  
  for (const row of rowsIndirect) {
    // 重複をチェック（既に直接関係で追加されている要件は除外）
    const isDuplicate = results.some(existing => existing.requirement_id === row.requirement_id);
    
    if (!isDuplicate) {
      results.push({
        requirement_id: row.requirement_id || "",
        requirement_title: row.requirement_title || "",
        requirement_type: row.requirement_type || "",
        requirement_priority: row.requirement_priority || "",
        implementation_type: row.implementation_type || "",
        requirement_location: row.requirement_location || "",
        relation_type: row.relation_type || ""
      });
    }
  }
  
  return results;
}

/**
 * コードから要件への逆引きテストを実行する関数
 */
async function runCodeToRequirementsTest(): Promise<boolean> {
  console.log("コードから要件への逆引きテスト開始");
  
  // データベースをセットアップ
  const dbName = "code_to_requirements_db";
  const { db, conn } = await setupDatabase(dbName);
  
  try {
    // スキーマとテストデータの準備
    await createSchema(conn);
    await insertSampleData(conn);
    
    // テスト1: 単一関数のテスト（validatePassword関数）
    console.log("\n==== テスト1: 特定関数から関連要件の確認 ====\n");
    
    const codeId = 'CODE-006';
    console.log(`コードID '${codeId}' (validatePassword関数) の関連要件を検索中...`);
    const functionResults = await findRequirementsForCode(conn, codeId);
    
    console.log(`検索結果: ${functionResults.length}件の要件が見つかりました`);
    
    // 結果の検証
    if (functionResults.length !== 1) {
      console.error(`テスト失敗: validatePassword関数は1つの要件と関連付けられているはずですが、${functionResults.length}件見つかりました`);
      return false;
    }
    
    if (functionResults[0].requirement_id !== 'REQ-003') {
      console.error(`テスト失敗: validatePassword関数はREQ-003と関連付けられているはずですが、${functionResults[0].requirement_id}が見つかりました`);
      return false;
    }
    
    const formattedFunctionResults = formatRequirementsForCode(functionResults);
    console.log(formattedFunctionResults);
    
    // テスト2: クラス全体のテスト（UserServiceクラス）
    console.log("\n==== テスト2: クラス全体から関連要件の確認 ====\n");
    
    const classId = 'CODE-001';
    console.log(`コードID '${classId}' (UserServiceクラス) の関連要件を検索中...`);
    const classResults = await findRequirementsForCode(conn, classId);
    
    console.log(`検索結果: ${classResults.length}件の要件が見つかりました`);
    
    // 結果の検証
    if (classResults.length !== 4) {
      console.error(`テスト失敗: UserServiceクラスは4つの要件と関連付けられているはずですが、${classResults.length}件見つかりました`);
      return false;
    }
    
    // 高優先度要件の確認
    const highPriorityReqs = classResults.filter(req => req.requirement_priority === 'HIGH');
    if (highPriorityReqs.length !== 2) {
      console.error(`テスト失敗: 高優先度の要件が2つあるはずですが、${highPriorityReqs.length}件見つかりました`);
      return false;
    }
    
    // セキュリティ要件の確認
    const securityReqs = classResults.filter(req => req.requirement_type === 'security');
    if (securityReqs.length !== 2) {
      console.error(`テスト失敗: セキュリティ要件が2つあるはずですが、${securityReqs.length}件見つかりました`);
      return false;
    }
    
    const formattedClassResults = formatRequirementsForCode(classResults);
    console.log(formattedClassResults);
    
    console.log("\n全てのテストが成功しました");
    return true;
  } catch (error) {
    console.error("テスト実行中にエラーが発生しました:", error);
    return false;
  } finally {
    // データベース接続を閉じる
    await closeDatabase(db, conn);
  }
}

// メイン実行部分
if (import.meta.main) {
  runCodeToRequirementsTest()
    .then((success) => {
      if (success) {
        console.log("コードから要件への逆引きテスト成功");
        Deno.exit(0);
      } else {
        console.error("コードから要件への逆引きテスト失敗");
        Deno.exit(1);
      }
    })
    .catch((error) => {
      console.error("予期しないエラー:", error);
      Deno.exit(1);
    });
}

// Deno.testでのテスト定義（外部からのインポート用）
Deno.test("コードから要件への逆引き機能", async () => {
  const success = await runCodeToRequirementsTest();
  if (!success) {
    throw new Error("コードから要件への逆引きテストが失敗しました");
  }
});
