/**
 * 階層型トレーサビリティモデル - 要件文書化テスト
 * 
 * このファイルはテスト名・説明による要件の文書化機能をテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "documentation_test_db";

// メイン実行関数
(async () => {
  console.log("===== 要件文書化テスト =====");
  
  // 初期化
  let db: any, conn: any;
  
  try {
    // 1. データベースセットアップ
    console.log("\n1. データベースセットアップ");
    const result = await setupDatabase(TEST_DB_NAME);
    db = result.db;
    conn = result.conn;
    console.log("✓ データベースセットアップ完了");
    
    // 2. スキーマ定義
    console.log("\n2. スキーマ定義");
    await callDdl(conn, "schema.cypher");
    console.log("✓ スキーマ定義完了");
    
    // 3. テストデータ挿入
    console.log("\n3. テストデータ挿入");
    await callDml(conn, "exclusive_test_data.cypher");
    console.log("✓ テストデータ挿入完了");
    
    // 4. 初期状態の確認
    console.log("\n4. 初期状態の確認");
    console.log("検証メソッド一覧:");
    try {
      const verificationsQuery = `
        MATCH (v:RequirementVerification)
        RETURN v.id, v.name, v.description, v.verification_type;
      `;
      const verificationsResult = await conn.query(verificationsQuery);
      
      verificationsResult.resetIterator();
      let count = 1;
      while (verificationsResult.hasNext()) {
        const row = verificationsResult.getNextSync();
        console.log(`  ${count}. ID: ${row["v.id"]}, 名前: ${row["v.name"]}`);
        console.log(`     説明: ${row["v.description"] || "(説明なし)"}`);
        console.log(`     タイプ: ${row["v.verification_type"] || "(未指定)"}`);
        count++;
      }
    } catch (err) {
      console.error(`  初期状態の確認に失敗: ${err}`);
    }
    
    // 5. 文書化されたテストの作成
    console.log("\n5. 文書化されたテストの作成");
    try {
      const createDocumentedTestsQuery = `
        CREATE (test1:RequirementVerification {
          id: 'TEST-DOC-001',
          name: 'ユーザー登録の正常フローテスト',
          description: 'ユーザー名、メールアドレス、パスワードを入力して新規ユーザーが正常に作成できることを確認する。成功時はユーザーIDが返却され、ユーザー情報がデータベースに保存されること。',
          verification_type: 'functional_test'
        })
        
        CREATE (test2:RequirementVerification {
          id: 'TEST-DOC-002',
          name: 'ユーザー登録の入力検証テスト',
          description: '不正な形式のメールアドレスやパスワード強度が不足している場合、適切なエラーメッセージが表示され、ユーザーが作成されないことを確認する。',
          verification_type: 'functional_test'
        })
        
        CREATE (test3:RequirementVerification {
          id: 'TEST-DOC-003',
          name: 'パスワードポリシー検証テスト',
          description: 'パスワードは8文字以上、アルファベット大文字・小文字・数字・特殊文字をそれぞれ1つ以上含む必要があることを確認する。これらの条件を満たさない場合は適切なエラーメッセージが表示されること。',
          verification_type: 'functional_test'
        })
        
        // テストケースと要件を関連付け
        WITH test1, test2, test3
        MATCH (req1:RequirementEntity {id: 'REQ-001'})  // ユーザー登録機能
        MATCH (req2:RequirementEntity {id: 'REQ-003'})  // パスワードポリシー
        
        CREATE (req1)-[:VERIFIED_BY]->(test1)
        CREATE (req1)-[:VERIFIED_BY]->(test2)
        CREATE (req2)-[:VERIFIED_BY]->(test3)
        
        RETURN test1.id, test2.id, test3.id;
      `;
      
      const createResult = await conn.query(createDocumentedTestsQuery);
      
      createResult.resetIterator();
      const createRow = createResult.getNextSync();
      console.log(`  文書化されたテストケースを作成: ${createRow["test1.id"]}, ${createRow["test2.id"]}, ${createRow["test3.id"]}`);
    } catch (err) {
      console.error(`  文書化されたテストの作成に失敗: ${err}`);
    }
    
    // 6. テスト文書からの要件情報の抽出
    console.log("\n6. テスト文書からの要件情報の抽出");
    try {
      const extractRequirementsQuery = `
        MATCH (v:RequirementVerification)<-[:VERIFIED_BY]-(r:RequirementEntity)
        WHERE v.id IN ['TEST-DOC-001', 'TEST-DOC-002', 'TEST-DOC-003']
        RETURN v.id, v.name, v.description, r.id, r.title;
      `;
      const extractionResult = await conn.query(extractRequirementsQuery);
      
      console.log("\n  テストケースから抽出された要件情報:");
      extractionResult.resetIterator();
      while (extractionResult.hasNext()) {
        const row = extractionResult.getNextSync();
        console.log(`    テスト: ${row["v.id"]} - ${row["v.name"]}`);
        console.log(`    説明: ${row["v.description"]}`);
        console.log(`    検証する要件: ${row["r.title"]} (${row["r.id"]})`);
        console.log();
      }
    } catch (err) {
      console.error(`  テスト文書からの要件情報の抽出に失敗: ${err}`);
    }
    
    // 7. 要件定義からのテストケース一覧生成
    console.log("\n7. 要件定義からのテストケース一覧生成");
    try {
      const testsByRequirementQuery = `
        MATCH (r:RequirementEntity)-[:VERIFIED_BY]->(v:RequirementVerification)
        RETURN r.id, r.title, 
               collect(v.id) AS test_ids, 
               collect(v.name) AS test_names, 
               collect(v.description) AS test_descriptions;
      `;
      const testsByRequirementResult = await conn.query(testsByRequirementQuery);
      
      console.log("\n  要件ごとのテストケース:");
      testsByRequirementResult.resetIterator();
      while (testsByRequirementResult.hasNext()) {
        const row = testsByRequirementResult.getNextSync();
        console.log(`    要件: ${row["r.title"]} (${row["r.id"]})`);
        console.log(`    テストケース数: ${row["test_ids"].length}`);
        
        for (let i = 0; i < row["test_ids"].length; i++) {
          console.log(`      ${i+1}. ${row["test_names"][i]} (${row["test_ids"][i]})`);
          console.log(`         ${row["test_descriptions"][i]}`);
        }
        console.log();
      }
    } catch (err) {
      console.error(`  要件定義からのテストケース一覧生成に失敗: ${err}`);
    }
    
    // 8. テスト実行結果の記録と文書化
    console.log("\n8. テスト実行結果の記録と文書化");
    try {
      // テスト実行結果を記録するためのコードエンティティを作成
      const recordTestResultsQuery = `
        // テスト実装コードを作成
        CREATE (c1:CodeEntity {
          persistent_id: 'TEST-IMPL-001',
          name: 'testUserRegistration',
          type: 'function',
          signature: 'public void testUserRegistration()',
          complexity: 2,
          start_position: 100,
          end_position: 200
        })
        
        CREATE (c2:CodeEntity {
          persistent_id: 'TEST-IMPL-002',
          name: 'testUserRegistrationValidation',
          type: 'function',
          signature: 'public void testUserRegistrationValidation()',
          complexity: 3,
          start_position: 250,
          end_position: 400
        })
        
        CREATE (c3:CodeEntity {
          persistent_id: 'TEST-IMPL-003',
          name: 'testPasswordPolicy',
          type: 'function',
          signature: 'public void testPasswordPolicy()',
          complexity: 2,
          start_position: 450,
          end_position: 550
        })
        
        // テストケースと実装コードを関連付け
        WITH c1, c2, c3
        MATCH (v1:RequirementVerification {id: 'TEST-DOC-001'})
        MATCH (v2:RequirementVerification {id: 'TEST-DOC-002'})
        MATCH (v3:RequirementVerification {id: 'TEST-DOC-003'})
        
        CREATE (v1)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'junit_test'}]->(c1)
        CREATE (v2)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'junit_test'}]->(c2)
        CREATE (v3)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'junit_test'}]->(c3)
        
        RETURN c1.persistent_id, c2.persistent_id, c3.persistent_id;
      `;
      
      const recordResultsResult = await conn.query(recordTestResultsQuery);
      
      recordResultsResult.resetIterator();
      const resultRow = recordResultsResult.getNextSync();
      console.log(`  テスト実装コードを作成: ${resultRow["c1.persistent_id"]}, ${resultRow["c2.persistent_id"]}, ${resultRow["c3.persistent_id"]}`);
      
      // テストケースとその実装、要件の関連を表示
      const testTraceabilityQuery = `
        MATCH (r:RequirementEntity)-[:VERIFIED_BY]->(v:RequirementVerification)-[:VERIFICATION_IS_IMPLEMENTED_BY]->(c:CodeEntity)
        RETURN r.id, r.title, v.id, v.name, c.persistent_id, c.name;
      `;
      
      const traceabilityResult = await conn.query(testTraceabilityQuery);
      
      console.log("\n  テストトレーサビリティチェーン:");
      traceabilityResult.resetIterator();
      let traceCount = 1;
      while (traceabilityResult.hasNext()) {
        const row = traceabilityResult.getNextSync();
        console.log(`    チェーン ${traceCount}:`);
        console.log(`      要件: ${row["r.title"]} (${row["r.id"]})`);
        console.log(`      テスト仕様: ${row["v.name"]} (${row["v.id"]})`);
        console.log(`      テスト実装: ${row["c.name"]} (${row["c.persistent_id"]})`);
        traceCount++;
      }
    } catch (err) {
      console.error(`  テスト実行結果の記録と文書化に失敗: ${err}`);
    }
    
    // 9. 文書化を活用した要件カバレッジの計算
    console.log("\n9. 文書化を活用した要件カバレッジの計算");
    try {
      const coverageQuery = `
        MATCH (r:RequirementEntity)
        WITH count(r) AS total_requirements
        
        MATCH (r:RequirementEntity)-[:VERIFIED_BY]->(v:RequirementVerification)
        WITH total_requirements, count(DISTINCT r) AS verified_requirements
        
        MATCH (r:RequirementEntity)-[:VERIFIED_BY]->(v:RequirementVerification)-[:VERIFICATION_IS_IMPLEMENTED_BY]->(c:CodeEntity)
        WITH total_requirements, verified_requirements, count(DISTINCT r) AS implemented_and_verified
        
        RETURN 
          total_requirements,
          verified_requirements,
          implemented_and_verified,
          1.0 * verified_requirements / total_requirements * 100 AS verification_coverage_pct,
          1.0 * implemented_and_verified / total_requirements * 100 AS implemented_verification_coverage_pct;
      `;
      
      const coverageResult = await conn.query(coverageQuery);
      
      coverageResult.resetIterator();
      const coverageRow = coverageResult.getNextSync();
      
      console.log("  要件カバレッジ分析:");
      console.log(`    総要件数: ${coverageRow["total_requirements"]}`);
      console.log(`    検証方法が定義されている要件数: ${coverageRow["verified_requirements"]}`);
      console.log(`    検証が実装されている要件数: ${coverageRow["implemented_and_verified"]}`);
      console.log(`    検証定義カバレッジ: ${parseFloat(coverageRow["verification_coverage_pct"]).toFixed(2)}%`);
      console.log(`    検証実装カバレッジ: ${parseFloat(coverageRow["implemented_verification_coverage_pct"]).toFixed(2)}%`);
    } catch (err) {
      console.error(`  文書化を活用した要件カバレッジの計算に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("テスト名・説明による要件の文書化テストが完了しました。");
    
  } catch (error) {
    console.error("\n===== テスト失敗 =====");
    console.error("テスト実行中にエラーが発生しました:");
    console.error(error);
  } finally {
    // 常にデータベース接続をクローズする
    if (db && conn) {
      console.log("\nデータベース接続をクローズしています...");
      try {
        await closeDatabase(db, conn);
        console.log("データベース接続のクローズに成功しました");
      } catch (closeError) {
        console.error("データベース接続のクローズ中にエラーが発生しました:", closeError);
      }
    }
  }
})();
