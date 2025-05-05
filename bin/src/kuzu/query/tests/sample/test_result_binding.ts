/**
 * 階層型トレーサビリティモデル - テスト実行結果紐付けテスト
 * 
 * このファイルはテスト実行結果と要件の充足状況の紐付けをテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "result_binding_test_db";

// メイン実行関数
(async () => {
  console.log("===== テスト実行結果紐付けテスト =====");
  
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
    await callDml(conn, "sample_data.cypher");
    console.log("✓ 基本テストデータ挿入完了");
    
    // 4. テスト実行結果関連データの作成
    console.log("\n4. テスト実行結果関連データの作成");
    try {
      const createResult = await callNamedDml(conn, "result_binding_queries.cypher", "create_test_result_data", {});
      
      createResult.resetIterator();
      const createRow = createResult.getNextSync();
      console.log(`  テスト関連データを作成: 要件=${createRow.created_requirements}件, テスト=${createRow.created_tests}件, コード=${createRow.created_code}件`);
    } catch (err) {
      console.error(`  テスト実行結果関連データの作成に失敗: ${err}`);
    }
    
    // 5. テスト実行結果の作成
    console.log("\n5. テスト実行結果の作成");
    try {
      const execResult = await callNamedDml(conn, "result_binding_queries.cypher", "create_test_execution_results", {});
      
      execResult.resetIterator();
      const execRow = execResult.getNextSync();
      console.log(`  テスト実行結果を作成: セッション=${execRow.created_sessions}件, 実行結果=${execRow.created_results}件`);
    } catch (err) {
      console.error(`  テスト実行結果の作成に失敗: ${err}`);
    }
    
    // 6. テスト実行結果から要件の充足状況を確認
    console.log("\n6. テスト実行結果から要件の充足状況を確認");
    try {
      const satisfactionResult = await callNamedDml(conn, "result_binding_queries.cypher", "check_requirement_satisfaction", {});
      
      console.log("  要件とテスト実行結果の関連:");
      console.log("  要件ID | 要件タイトル | テストID | テスト名 | 結果ID | テスト状態 | エラーメッセージ");
      console.log("  -------|-------------|----------|----------|--------|------------|---------------");
      
      satisfactionResult.resetIterator();
      while (satisfactionResult.hasNext()) {
        const row = satisfactionResult.getNextSync();
        const errorMsg = row.error_message ? row.error_message.substring(0, 30) + '...' : '(なし)';
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.test_id} | ${row.test_name} | ${row.result_id} | ${row.test_status} | ${errorMsg}`);
      }
    } catch (err) {
      console.error(`  テスト実行結果からの要件充足状況確認に失敗: ${err}`);
    }
    
    // 7. テスト実行セッションの詳細を取得
    console.log("\n7. テスト実行セッションの詳細を取得");
    try {
      const sessionResult = await callNamedDml(conn, "result_binding_queries.cypher", "get_test_session_details", {
        sessionId: 'SESSION-001'
      });
      
      sessionResult.resetIterator();
      const sessionRow = sessionResult.getNextSync();
      
      console.log(`  テスト実行セッション: ${sessionRow.session_id}`);
      console.log(`  タイムスタンプ: ${sessionRow.timestamp}`);
      console.log(`  実行者: ${sessionRow.executor}`);
      console.log(`  環境: ${sessionRow.environment}`);
      console.log(`  ビルドID: ${sessionRow.build_id}`);
      console.log(`  総テスト数: ${sessionRow.total_results}件`);
      console.log(`  成功数: ${sessionRow.passed_count}件`);
      console.log(`  失敗数: ${sessionRow.failed_count}件`);
      console.log(`  セッション成功: ${sessionRow.is_successful ? 'はい' : 'いいえ'}`);
      console.log(`  成功率: ${parseFloat(sessionRow.success_rate_pct).toFixed(2)}%`);
    } catch (err) {
      console.error(`  テスト実行セッションの詳細取得に失敗: ${err}`);
    }
    
    // 8. 要件ごとの充足状況を集計
    console.log("\n8. 要件ごとの充足状況を集計");
    try {
      const summaryResult = await callNamedDml(conn, "result_binding_queries.cypher", "summarize_requirement_satisfaction", {});
      
      console.log("  要件の充足状況集計:");
      console.log("  要件ID | 要件タイトル | 優先度 | 総テスト数 | 成功数 | 失敗数 | 充足状態");
      console.log("  -------|-------------|--------|------------|---------|--------|----------");
      
      summaryResult.resetIterator();
      while (summaryResult.hasNext()) {
        const row = summaryResult.getNextSync();
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.requirement_priority} | ${row.total_verifications} | ${row.passed_verifications} | ${row.failed_verifications} | ${row.satisfaction_status}`);
        
        if (row.failed_test_ids && row.failed_test_ids.length > 0) {
          console.log(`    失敗したテスト: ${row.failed_test_ids.join(', ')}`);
          
          // エラーメッセージがある場合は表示
          if (row.error_messages && row.error_messages.length > 0) {
            row.error_messages.forEach((msg: string, index: number) => {
              if (msg) {
                console.log(`    エラー ${index + 1}: ${msg}`);
              }
            });
          }
        }
      }
    } catch (err) {
      console.error(`  要件ごとの充足状況集計に失敗: ${err}`);
    }
    
    // 9. 特定の期間内のテスト実行結果の履歴を取得
    console.log("\n9. 特定の期間内のテスト実行結果の履歴を取得");
    try {
      const historyResult = await callNamedDml(conn, "result_binding_queries.cypher", "get_test_execution_history", {
        testId: 'TEST-003',
        startDate: '2024-05-01T00:00:00Z',
        endDate: '2024-05-02T00:00:00Z'
      });
      
      console.log(`  テスト「TEST-003」の実行履歴（2024-05-01〜2024-05-02）:`);
      console.log("  テストID | テスト名 | 結果ID | 状態 | 実行時間 | タイムスタンプ | エラーメッセージ");
      console.log("  ---------|----------|--------|------|------------|----------------|---------------");
      
      historyResult.resetIterator();
      while (historyResult.hasNext()) {
        const row = historyResult.getNextSync();
        const errorMsg = row.error_message ? row.error_message.substring(0, 30) + '...' : '(なし)';
        console.log(`  ${row.test_id} | ${row.test_name} | ${row.result_id} | ${row.status} | ${row.execution_time}秒 | ${row.timestamp} | ${errorMsg}`);
      }
    } catch (err) {
      console.error(`  テスト実行結果の履歴取得に失敗: ${err}`);
    }
    
    // 10. 失敗したテストに関連するコードを特定
    console.log("\n10. 失敗したテストに関連するコードを特定");
    try {
      const problematicResult = await callNamedDml(conn, "result_binding_queries.cypher", "identify_problematic_code", {});
      
      console.log("  問題のあるコード特定:");
      console.log("  結果ID | テストID | テスト名 | コードID | コード名 | 影響要件 | エラーメッセージ");
      console.log("  --------|----------|----------|---------|----------|----------|---------------");
      
      problematicResult.resetIterator();
      while (problematicResult.hasNext()) {
        const row = problematicResult.getNextSync();
        const errorMsg = row.error_message ? row.error_message.substring(0, 30) + '...' : '(なし)';
        const affectedReqs = row.affected_requirements && row.affected_requirements.length > 0 ? row.affected_requirements.join(', ') : '(なし)';
        console.log(`  ${row.result_id} | ${row.test_id} | ${row.test_name} | ${row.code_id || '(なし)'} | ${row.code_name || '(なし)'} | ${affectedReqs} | ${errorMsg}`);
      }
    } catch (err) {
      console.error(`  問題のあるコードの特定に失敗: ${err}`);
    }
    
    // 11. テスト失敗に基づく修正優先度の分析
    console.log("\n11. テスト失敗に基づく修正優先度の分析");
    try {
      const priorityResult = await callNamedDml(conn, "result_binding_queries.cypher", "analyze_fix_priorities", {});
      
      console.log("  修正優先度分析:");
      console.log("  要件ID | 要件タイトル | 優先度 | 失敗テスト数 | スコア");
      console.log("  -------|-------------|--------|--------------|-------");
      
      priorityResult.resetIterator();
      while (priorityResult.hasNext()) {
        const row = priorityResult.getNextSync();
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.requirement_priority} | ${row.failed_test_count} | ${row.fix_priority_score}`);
        
        if (row.failed_tests && row.failed_tests.length > 0) {
          console.log(`    失敗したテスト: ${row.failed_tests.join(', ')}`);
        }
      }
    } catch (err) {
      console.error(`  修正優先度の分析に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("テスト実行結果と要件の充足状況の紐付けテストが完了しました。");
    
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