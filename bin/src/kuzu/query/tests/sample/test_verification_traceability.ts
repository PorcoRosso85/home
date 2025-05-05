/**
 * 階層型トレーサビリティモデル - 検証トレーサビリティテスト
 * 
 * このファイルは要件から検証方法（テスト）への双方向トレーサビリティをテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "verification_traceability_test_db";

// メイン実行関数
(async () => {
  console.log("===== 検証トレーサビリティテスト =====");
  
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
    console.log("要件と検証の初期状態:");
    try {
      const requirementsResult = await callNamedDml(conn, "exclusive_relation_queries.cypher", "get_all_requirements", {});
      console.log(`  取得した要件: ${requirementsResult.getNumTuples()}件`);
      
      // 現代的なアクセス方法に修正
      requirementsResult.resetIterator();
      let count = 1;
      while (requirementsResult.hasNext()) {
        try {
          const row = requirementsResult.getNextSync();
          console.log(`  ${count}. ID: ${row["r.id"]}, タイトル: ${row["r.title"]}`);
          count++;
        } catch (err) {
          console.error(`  行データの取得に失敗: ${err}`);
        }
      }
      
      // 検証一覧を表示
      const verificationsResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "get_all_verifications", {});
      
      console.log("\n検証一覧:");
      verificationsResult.resetIterator();
      count = 1;
      while (verificationsResult.hasNext()) {
        const row = verificationsResult.getNextSync();
        console.log(`  ${count}. ID: ${row["v.id"]}, 名前: ${row["v.name"]}, タイプ: ${row["v.verification_type"]}`);
        count++;
      }
    } catch (err) {
      console.error(`  初期状態の確認に失敗: ${err}`);
    }
    
    // 5. 双方向トレーサビリティテスト（要件から検証）
    console.log("\n5. 双方向トレーサビリティテスト（要件から検証）");
    try {
      // 追加の要件と検証を作成
      const createResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "create_req_and_verification", {});
      
      createResult.resetIterator();
      const createRow = createResult.getNextSync();
      console.log(`  要件「${createRow["r.id"]}」を検証「${createRow["v1.id"]}」と「${createRow["v2.id"]}」に関連付けました`);
      
      // 要件から検証を取得するクエリ
      const reqToVerificationResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "get_verifications_for_requirement", {});
      
      console.log("\n  要件からの検証トレーサビリティ:");
      reqToVerificationResult.resetIterator();
      const reqRow = reqToVerificationResult.getNextSync();
      console.log(`    要件: ${reqRow["r.title"]} (${reqRow["r.id"]})`);
      console.log(`    検証: ${reqRow["verification_names"].join(', ')} (${reqRow["verification_ids"].join(', ')})`);
    } catch (err) {
      console.error(`  双方向トレーサビリティテスト（要件から検証）に失敗: ${err}`);
    }
    
    // 6. 双方向トレーサビリティテスト（検証から要件）
    console.log("\n6. 双方向トレーサビリティテスト（検証から要件）");
    try {
      // 検証から要件を取得するクエリ
      const verificationToReqResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "get_requirements_for_verification", {});
      
      console.log("\n  検証からの要件トレーサビリティ:");
      verificationToReqResult.resetIterator();
      const verRow = verificationToReqResult.getNextSync();
      console.log(`    検証: ${verRow["v.name"]} (${verRow["v.id"]})`);
      console.log(`    要件: ${verRow["requirement_titles"].join(', ')} (${verRow["requirement_ids"].join(', ')})`);
    } catch (err) {
      console.error(`  双方向トレーサビリティテスト（検証から要件）に失敗: ${err}`);
    }
    
    // 7. 検証カバレッジの確認（未検証の要件を検出）
    console.log("\n7. 検証カバレッジの確認（未検証の要件を検出）");
    try {
      // 追加の未検証要件を作成
      const createUnverifiedResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "create_unverified_requirement", {});
      
      createUnverifiedResult.resetIterator();
      const unverifiedRow = createUnverifiedResult.getNextSync();
      console.log(`  未検証の要件を作成: ${unverifiedRow["r.title"]} (${unverifiedRow["r.id"]})`);
      
      // 未検証の要件を検出するクエリ
      const unverifiedReqResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "find_unverified_requirements", {});
      
      console.log("\n  未検証の要件一覧:");
      unverifiedReqResult.resetIterator();
      let count = 1;
      while (unverifiedReqResult.hasNext()) {
        const row = unverifiedReqResult.getNextSync();
        console.log(`    ${count}. ${row["r.title"]} (${row["r.id"]}) - 優先度: ${row["r.priority"]}`);
        count++;
      }
    } catch (err) {
      console.error(`  検証カバレッジの確認に失敗: ${err}`);
    }
    
    // 8. 検証方法の実装コードへのトレーサビリティ
    console.log("\n8. 検証方法の実装コードへのトレーサビリティ");
    try {
      // 検証の実装コードを作成
      const createVerificationCodeResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "create_verification_code", {});
      
      createVerificationCodeResult.resetIterator();
      const codeRow = createVerificationCodeResult.getNextSync();
      console.log(`  検証「${codeRow["v.id"]}」を実装コード「${codeRow["c.persistent_id"]}」に関連付けました`);
      
      // トレーサビリティチェーン（要件→検証→コード）を取得するクエリ
      const traceabilityChainResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "get_traceability_chain", {});
      
      console.log("\n  トレーサビリティチェーン（要件→検証→コード）:");
      traceabilityChainResult.resetIterator();
      let count = 1;
      while (traceabilityChainResult.hasNext()) {
        const row = traceabilityChainResult.getNextSync();
        console.log(`    チェーン ${count}:`);
        console.log(`      要件: ${row["r.title"]} (${row["r.id"]})`);
        console.log(`      検証: ${row["v.name"]} (${row["v.id"]})`);
        console.log(`      コード: ${row["c.name"]} (${row["c.persistent_id"]})`);
        count++;
      }
    } catch (err) {
      console.error(`  検証方法の実装コードへのトレーサビリティテストに失敗: ${err}`);
    }
    
    // 9. 実装が欠けている検証の検出
    console.log("\n9. 実装が欠けている検証の検出");
    try {
      // 実装が欠けている検証を検出するクエリ
      const unimplementedVerificationResult = await callNamedDml(conn, "verification_traceability_queries.cypher", "find_unimplemented_verifications", {});
      
      console.log("\n  実装が欠けている検証一覧:");
      unimplementedVerificationResult.resetIterator();
      let count = 1;
      while (unimplementedVerificationResult.hasNext()) {
        const row = unimplementedVerificationResult.getNextSync();
        console.log(`    ${count}. ${row["v.name"]} (${row["v.id"]}) - タイプ: ${row["v.verification_type"]}`);
        count++;
      }
    } catch (err) {
      console.error(`  実装が欠けている検証の検出に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("要件から検証方法への双方向トレーサビリティテストが完了しました。");
    
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
