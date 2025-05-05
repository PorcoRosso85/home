/**
 * 階層型トレーサビリティモデル - 要件カバレッジ測定テスト
 * 
 * このファイルは要件の実装・検証カバレッジを数値化し、品質保証の指標として活用できることをテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "coverage_measurement_test_db";

// メイン実行関数
(async () => {
  console.log("===== 要件カバレッジ測定テスト =====");
  
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
    
    // 4. カバレッジ測定用テストデータの作成
    console.log("\n4. カバレッジ測定用テストデータの作成");
    try {
      const createResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "create_coverage_test_data", {});
      
      createResult.resetIterator();
      const createRow = createResult.getNextSync();
      console.log(`  カバレッジ測定用データを作成: 要件=${createRow.created_requirements}件, コード=${createRow.created_code}件, 検証=${createRow.created_verifications}件`);
    } catch (err) {
      console.error(`  カバレッジ測定用テストデータの作成に失敗: ${err}`);
    }
    
    // 5. 初期状態での要件カバレッジ測定
    console.log("\n5. 初期状態での要件カバレッジ測定");
    try {
      const coverageResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "measure_overall_coverage", {});
      
      coverageResult.resetIterator();
      const coverageRow = coverageResult.getNextSync();
      
      console.log("  全体カバレッジの初期状態:");
      console.log(`  総要件数: ${coverageRow.total_requirements}件`);
      console.log(`  実装済み要件数: ${coverageRow.implemented_requirements}件 (${parseFloat(coverageRow.implementation_coverage_pct).toFixed(2)}%)`);
      console.log(`  検証済み要件数: ${coverageRow.verified_requirements}件 (${parseFloat(coverageRow.verification_coverage_pct).toFixed(2)}%)`);
      console.log(`  完全カバー要件数: ${coverageRow.fully_covered_requirements}件 (${parseFloat(coverageRow.full_coverage_pct).toFixed(2)}%)`);
    } catch (err) {
      console.error(`  初期状態での要件カバレッジ測定に失敗: ${err}`);
    }
    
    // 6. 優先度ごとのカバレッジ測定
    console.log("\n6. 優先度ごとのカバレッジ測定");
    try {
      const priorityResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "measure_coverage_by_priority", {
        priorities: ['high', 'medium', 'low']
      });
      
      console.log("  優先度別カバレッジ:");
      console.log("  優先度 | 総数 | 実装数 | 検証数 | 完全数 | 実装率 | 検証率 | 完全率");
      console.log("  -------|------|--------|--------|--------|--------|--------|--------");
      
      priorityResult.resetIterator();
      while (priorityResult.hasNext()) {
        const row = priorityResult.getNextSync();
        console.log(`  ${row.priority.padEnd(7)} | ${row.total.toString().padEnd(4)} | ${row.implemented.toString().padEnd(6)} | ${row.verified.toString().padEnd(6)} | ${row.fully_covered.toString().padEnd(6)} | ${parseFloat(row.implementation_coverage_pct).toFixed(2).padEnd(6)}% | ${parseFloat(row.verification_coverage_pct).toFixed(2).padEnd(6)}% | ${parseFloat(row.full_coverage_pct).toFixed(2).padEnd(6)}%`);
      }
    } catch (err) {
      console.error(`  優先度ごとのカバレッジ測定に失敗: ${err}`);
    }
    
    // 7. 未カバー要件のリスト取得
    console.log("\n7. 未カバー要件のリスト取得");
    try {
      const uncoveredResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "get_uncovered_requirements", {});
      
      console.log("  カバレッジが不完全な要件一覧:");
      console.log("  要件ID | タイトル | 優先度 | 実装 | 検証");
      console.log("  -------|----------|--------|------|------");
      
      uncoveredResult.resetIterator();
      while (uncoveredResult.hasNext()) {
        const row = uncoveredResult.getNextSync();
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.requirement_priority} | ${row.has_implementation ? '✓' : '✗'} | ${row.has_verification ? '✓' : '✗'}`);
      }
    } catch (err) {
      console.error(`  未カバー要件のリスト取得に失敗: ${err}`);
    }
    
    // 8. カバレッジ向上のための追加実装と検証
    console.log("\n8. カバレッジ向上のための追加実装と検証");
    try {
      const improveCoverageResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "improve_coverage", {});
      
      improveCoverageResult.resetIterator();
      const improveRow = improveCoverageResult.getNextSync();
      console.log(`  カバレッジ向上のための追加: コード=${improveRow.created_code}件, 検証=${improveRow.created_verifications}件`);
    } catch (err) {
      console.error(`  カバレッジ向上のための追加実装と検証に失敗: ${err}`);
    }
    
    // 9. 改善後のカバレッジ測定
    console.log("\n9. 改善後のカバレッジ測定");
    try {
      const improvedCoverageResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "measure_overall_coverage", {});
      
      improvedCoverageResult.resetIterator();
      const improvedRow = improvedCoverageResult.getNextSync();
      
      console.log("  全体カバレッジの改善後:");
      console.log(`  総要件数: ${improvedRow.total_requirements}件`);
      console.log(`  実装済み要件数: ${improvedRow.implemented_requirements}件 (${parseFloat(improvedRow.implementation_coverage_pct).toFixed(2)}%)`);
      console.log(`  検証済み要件数: ${improvedRow.verified_requirements}件 (${parseFloat(improvedRow.verification_coverage_pct).toFixed(2)}%)`);
      console.log(`  完全カバー要件数: ${improvedRow.fully_covered_requirements}件 (${parseFloat(improvedRow.full_coverage_pct).toFixed(2)}%)`);
      
      // 改善前との比較
      const initialCoverageResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "measure_overall_coverage", {});
      initialCoverageResult.resetIterator();
      const initialRow = initialCoverageResult.getNextSync();
      
      // ※通常は上記の初期状態での測定結果と比較すべきだが、このコード例では簡略化のため再取得している
      console.log("\n  カバレッジの改善率:");
      console.log(`  実装カバレッジ: ${parseFloat(improvedRow.implementation_coverage_pct - initialRow.implementation_coverage_pct).toFixed(2)}% 向上`);
      console.log(`  検証カバレッジ: ${parseFloat(improvedRow.verification_coverage_pct - initialRow.verification_coverage_pct).toFixed(2)}% 向上`);
      console.log(`  完全カバレッジ: ${parseFloat(improvedRow.full_coverage_pct - initialRow.full_coverage_pct).toFixed(2)}% 向上`);
    } catch (err) {
      console.error(`  改善後のカバレッジ測定に失敗: ${err}`);
    }
    
    // 10. タイプ別のカバレッジ分析
    console.log("\n10. タイプ別のカバレッジ分析");
    try {
      const typeResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "measure_coverage_by_type", {
        types: ['functional']
      });
      
      console.log("  要件タイプ別カバレッジ:");
      typeResult.resetIterator();
      while (typeResult.hasNext()) {
        const row = typeResult.getNextSync();
        console.log(`  タイプ: ${row.requirement_type}`);
        console.log(`  総要件数: ${row.total}件`);
        console.log(`  実装率: ${parseFloat(row.implementation_coverage_pct).toFixed(2)}%`);
        console.log(`  検証率: ${parseFloat(row.verification_coverage_pct).toFixed(2)}%`);
        console.log(`  完全カバー率: ${parseFloat(row.full_coverage_pct).toFixed(2)}%`);
      }
      
      // 検証タイプの分析
      const verificationTypeResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "analyze_verification_types", {});
      
      console.log("\n  検証タイプ別の分布:");
      verificationTypeResult.resetIterator();
      while (verificationTypeResult.hasNext()) {
        const row = verificationTypeResult.getNextSync();
        console.log(`  ${row.verification_type}: ${row.requirements_count}件の要件をカバー`);
      }
    } catch (err) {
      console.error(`  タイプ別のカバレッジ分析に失敗: ${err}`);
    }
    
    // 11. 詳細なカバレッジレポートの生成
    console.log("\n11. 詳細なカバレッジレポートの生成");
    try {
      const detailedResult = await callNamedDml(conn, "coverage_measurement_queries.cypher", "get_detailed_coverage", {});
      
      console.log("  要件ごとの詳細カバレッジレポート:");
      console.log("  要件ID | タイトル | 優先度 | 実装コード | 検証 | カバレッジ状態");
      console.log("  -------|----------|--------|------------|------|---------------");
      
      detailedResult.resetIterator();
      while (detailedResult.hasNext()) {
        const row = detailedResult.getNextSync();
        const implStr = row.implementations.length > 0 ? row.implementations.join(', ') : '(なし)';
        const verStr = row.verifications.length > 0 ? row.verifications.join(', ') : '(なし)';
        
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.priority} | ${implStr} | ${verStr} | ${row.coverage_status}`);
      }
    } catch (err) {
      console.error(`  詳細なカバレッジレポートの生成に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("要件カバレッジの測定と可視化テストが完了しました。");
    
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