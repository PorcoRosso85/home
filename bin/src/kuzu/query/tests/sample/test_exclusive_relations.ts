#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - 排他的関係テスト
 * 
 * このファイルは要件と検証の排他的関係をテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "exclusive_relations_test_db";

// メイン実行関数
(async () => {
  console.log("===== 排他的関係テスト =====");
  
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
    console.log("要件一覧:");
    try {
      const requirementsResult = await callNamedDml(conn, "exclusive_relation_queries.cypher", "get_all_requirements", {});
      console.log(`  取得した要件: ${requirementsResult.getNumTuples()}件`);
      for (let i = 0; i < requirementsResult.getNumTuples(); i++) {
        try {
          const row = requirementsResult.getRow(i);
          console.log(`  ${i+1}. ID: ${row[0]}, タイトル: ${row[1]}`);
        } catch (err) {
          console.error(`  行データの取得に失敗: ${err}`);
        }
      }
      
      // 5. 各要件の関連を確認
      console.log("\n5. 各要件の関連確認");
      const reqIds = ['REQ-001', 'REQ-002', 'REQ-003'];
      for (const reqId of reqIds) {
        try {
          const relationResult = await callNamedDml(conn, "exclusive_relation_queries.cypher", "check_requirement_relations", {
            reqId: reqId
          });
          
          console.log(`\n要件 ${reqId} の関連:`);
          // 簡易表示に切り替え
          relationResult.resetIterator();
          while (relationResult.hasNext()) {
            const row = relationResult.getNextSync();
            console.log(JSON.stringify(row));
          }
        } catch (err) {
          console.error(`  要件 ${reqId} の関連確認に失敗: ${err}`);
        }
      }
    } catch (err) {
      console.error(`  要件一覧の取得に失敗: ${err}`);
    }
    
    // 6. 排他的関係テスト
    console.log("\n6. 排他的関係テスト");
    
    // 6.1 未関連付け要件に検証を追加（成功するはず）
    console.log("\n6.1 未関連付け要件に検証を追加（成功するはず）");
    try {
      const addResult1 = await callNamedDml(conn, "exclusive_relation_queries.cypher", "add_exclusive_verification", {
        reqId: "REQ-001",
        verificationId: "TEST-002"
      });
      
      console.log(`  結果行数: ${addResult1.getNumTuples()}`);
      if (addResult1.getNumTuples() > 0) {
        try {
          const row = addResult1.getRow(0);
          console.log(`  ✓ 成功: 要件 ${row[0]} に検証 ${row[1]} を追加しました`);
        } catch (err) {
          console.error(`  行データの取得に失敗: ${err}`);
        }
      } else {
        console.log("  ✗ 失敗: 関係は作成されませんでした");
      }
    } catch (error) {
      console.error(`  エラー: ${error}`);
    }
    
    // 6.2 コード実装済み要件に検証を追加（失敗するはず）
    console.log("\n6.2 コード実装済み要件に検証を追加（失敗するはず）");
    try {
      const addResult2 = await callNamedDml(conn, "exclusive_relation_queries.cypher", "add_exclusive_verification", {
        reqId: "REQ-002", 
        verificationId: "TEST-002"
      });
      
      console.log(`  結果行数: ${addResult2.getNumTuples()}`);
      if (addResult2.getNumTuples() > 0) {
        try {
          const row = addResult2.getRow(0);
          console.log(`  ✗ 予想外の成功: 要件 ${row[0]} に検証 ${row[1]} を追加しました`);
        } catch (err) {
          console.error(`  行データの取得に失敗: ${err}`);
        }
      } else {
        console.log("  ✓ 期待通りの失敗: 既に実装されている要件に検証は追加されませんでした");
      }
    } catch (error) {
      console.error(`  エラー: ${error}`);
    }
    
    // 6.3 検証済み要件に別の検証を追加（失敗するはず）
    console.log("\n6.3 検証済み要件に別の検証を追加（失敗するはず）");
    try {
      const addResult3 = await callNamedDml(conn, "exclusive_relation_queries.cypher", "add_exclusive_verification", {
        reqId: "REQ-003",
        verificationId: "TEST-002"
      });
      
      console.log(`  結果行数: ${addResult3.getNumTuples()}`);
      if (addResult3.getNumTuples() > 0) {
        try {
          const row = addResult3.getRow(0);
          console.log(`  ✗ 予想外の成功: 要件 ${row[0]} に検証 ${row[1]} を追加しました`);
        } catch (err) {
          console.error(`  行データの取得に失敗: ${err}`);
        }
      } else {
        console.log("  ✓ 期待通りの失敗: 既に検証されている要件に別の検証は追加されませんでした");
      }
    } catch (error) {
      console.error(`  エラー: ${error}`);
    }
    
    // 6.4 通常のクエリでは関係の追加が可能か確認（排他制約がないケース）
    console.log("\n6.4 通常のクエリで関係の追加テスト（排他制約なし）");
    try {
      const addResult4 = await callNamedDml(conn, "exclusive_relation_queries.cypher", "add_verification_for_testing", {
        reqId: "REQ-002", // コード実装済み要件に強制的に検証を追加
        verificationId: "TEST-002"
      });
      
      console.log(`  結果行数: ${addResult4.getNumTuples()}`);
      if (addResult4.getNumTuples() > 0) {
        try {
          const row = addResult4.getRow(0);
          console.log(`  ✓ 成功: 排他制約なしのクエリでは要件 ${row[0]} に検証 ${row[1]} を追加できました`);
        } catch (err) {
          console.error(`  行データの取得に失敗: ${err}`);
        }
      } else {
        console.log("  ✗ 失敗: 関係は作成されませんでした");
      }
    } catch (error) {
      console.error(`  エラー: ${error}`);
    }
    
    // 7. 最終状態の確認
    console.log("\n7. 最終状態の確認");
    try {
      const reqIds = ['REQ-001', 'REQ-002', 'REQ-003'];
      for (const reqId of reqIds) {
        try {
          const relationResult = await callNamedDml(conn, "exclusive_relation_queries.cypher", "check_requirement_relations", {
            reqId: reqId
          });
          
          console.log(`\n要件 ${reqId} の最終関連:`);
          // 簡易表示に切り替え
          relationResult.resetIterator();
          while (relationResult.hasNext()) {
            const row = relationResult.getNextSync();
            console.log(JSON.stringify(row));
          }
        } catch (err) {
          console.error(`  要件 ${reqId} の最終関連確認に失敗: ${err}`);
        }
      }
    } catch (err) {
      console.error(`  最終状態の確認に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("要件と検証の排他的関係テストが完了しました。");
    
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
