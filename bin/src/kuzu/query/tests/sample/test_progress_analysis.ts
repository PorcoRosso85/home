/**
 * 階層型トレーサビリティモデル - 実装・テストの進捗状況分析テスト
 * 
 * このファイルは実装・テストの進捗状況の集計と分析機能をテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "progress_analysis_test_db";

// メイン実行関数
(async () => {
  console.log("===== 実装・テストの進捗状況分析テスト =====");
  
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
    console.log("✓ テストデータ挿入完了");
    
    // 4. プロジェクト要件の作成
    console.log("\n4. プロジェクト要件の作成");
    try {
      const createResult = await callNamedDml(conn, "project_requirements.cypher", "create_project_requirements", {});
      
      createResult.resetIterator();
      const resultRow = createResult.getNextSync();
      console.log(`  プロジェクト要件と関連オブジェクトを作成: ${resultRow.created_nodes}ノード`);
    } catch (err) {
      console.error(`  プロジェクト要件の作成に失敗: ${err}`);
    }
    
    // 5. 要件の進捗状況を集計
    console.log("\n5. 要件の進捗状況を集計");
    try {
      const progressResult = await callNamedDml(conn, "version_queries.cypher", "get_requirement_progress", {});
      
      console.log("  要件の進捗状況:");
      console.log("  ステータス | 数");
      console.log("  ----------|----");
      
      let totalRequirements = 0;
      let completedRequirements = 0;
      
      progressResult.resetIterator();
      while (progressResult.hasNext()) {
        const row = progressResult.getNextSync();
        const status = row.status || 'unknown';
        console.log(`  ${status.padEnd(10)} | ${row.count}`);
        
        totalRequirements += Number(row.count);
        if (status === 'completed') {
          completedRequirements += Number(row.count);
        }
      }
      
      const completionPercentage = (completedRequirements / totalRequirements * 100).toFixed(2);
      console.log(`\n  全体の完了率: ${completionPercentage}% (${completedRequirements}/${totalRequirements})`);
    } catch (err) {
      console.error(`  要件の進捗状況の集計に失敗: ${err}`);
    }
    
    // 6. モジュール別の進捗状況を分析
    console.log("\n6. モジュール別の進捗状況を分析");
    try {
      const moduleResult = await callNamedDml(conn, "version_queries.cypher", "get_module_progress", {
        module_ids: ['auth-module', 'user-module', 'admin-module']
      });
      
      console.log("  モジュール別の進捗状況:");
      console.log("  モジュール | 完了 | 進行中 | 未着手 | 合計 | 完了率");
      console.log("  ----------|------|--------|--------|------|-------");
      
      moduleResult.resetIterator();
      while (moduleResult.hasNext()) {
        const row = moduleResult.getNextSync();
        const module = row.module || 'unknown';
        const completed = Number(row.completed || 0);
        const in_progress = Number(row.in_progress || 0);
        const not_started = Number(row.not_started || 0);
        const total = Number(row.total || 0);
        const completionRate = total > 0 ? ((completed / total) * 100).toFixed(2) : '0.00';
        console.log(`  ${module.padEnd(10)} | ${completed.toString().padEnd(4)} | ${in_progress.toString().padEnd(6)} | ${not_started.toString().padEnd(6)} | ${total.toString().padEnd(4)} | ${completionRate}%`);
      }
    } catch (err) {
      console.error(`  モジュール別の進捗状況の分析に失敗: ${err}`);
    }
    
    // 7. 優先度による進捗状況
    console.log("\n7. 優先度による進捗状況");
    try {
      const priorityResult = await callNamedDml(conn, "version_queries.cypher", "get_priority_progress", {
        priorities: ['high', 'medium', 'low']
      });
      
      console.log("  優先度による進捗状況:");
      console.log("  優先度 | 完了 | 進行中 | 未着手 | 合計 | 完了率");
      console.log("  -------|------|--------|--------|------|-------");
      
      priorityResult.resetIterator();
      while (priorityResult.hasNext()) {
        const row = priorityResult.getNextSync();
        const priority = row.priority || 'unknown';
        const completed = Number(row.completed || 0);
        const in_progress = Number(row.in_progress || 0);
        const not_started = Number(row.not_started || 0);
        const total = Number(row.total || 0);
        const completionRate = total > 0 ? ((completed / total) * 100).toFixed(2) : '0.00';
        console.log(`  ${priority.padEnd(7)} | ${completed.toString().padEnd(4)} | ${in_progress.toString().padEnd(6)} | ${not_started.toString().padEnd(6)} | ${total.toString().padEnd(4)} | ${completionRate}%`);
      }
    } catch (err) {
      console.error(`  優先度による進捗状況の分析に失敗: ${err}`);
    }
    
    // 8. 検証の進捗状況
    console.log("\n8. 検証の進捗状況");
    try {
      const verificationResult = await callNamedDml(conn, "version_queries.cypher", "get_verification_progress", {});
      
      console.log("  検証の進捗状況:");
      console.log("  ステータス | 数");
      console.log("  ----------|----");
      
      let totalVerifications = 0;
      let passedVerifications = 0;
      
      verificationResult.resetIterator();
      while (verificationResult.hasNext()) {
        const row = verificationResult.getNextSync();
        const status = row.status || 'unknown';
        console.log(`  ${status.padEnd(10)} | ${row.count}`);
        
        totalVerifications += Number(row.count);
        if (status === 'passed') {
          passedVerifications += Number(row.count);
        }
      }
      
      const passRate = (passedVerifications / totalVerifications * 100).toFixed(2);
      console.log(`\n  検証完了率: ${passRate}% (${passedVerifications}/${totalVerifications})`);
    } catch (err) {
      console.error(`  検証の進捗状況の分析に失敗: ${err}`);
    }
    
    // 9. コード実装の進捗状況
    console.log("\n9. コード実装の進捗状況");
    try {
      const codeResult = await callNamedDml(conn, "version_queries.cypher", "get_code_progress", {});
      
      console.log("  コード実装の進捗状況:");
      console.log("  ステータス | 数");
      console.log("  ----------|----");
      
      let totalImplementations = 0;
      let completedImplementations = 0;
      
      codeResult.resetIterator();
      while (codeResult.hasNext()) {
        const row = codeResult.getNextSync();
        const status = row.status || 'unknown';
        console.log(`  ${status.padEnd(10)} | ${row.count}`);
        
        totalImplementations += Number(row.count);
        if (status === 'completed') {
          completedImplementations += Number(row.count);
        }
      }
      
      const implementationRate = (completedImplementations / totalImplementations * 100).toFixed(2);
      console.log(`\n  実装完了率: ${implementationRate}% (${completedImplementations}/${totalImplementations})`);
    } catch (err) {
      console.error(`  コード実装の進捗状況の分析に失敗: ${err}`);
    }
    
    // 10. 総合進捗ダッシュボード
    console.log("\n10. 総合進捗ダッシュボード");
    try {
      // 要件の完了率
      const reqResult = await callNamedDml(conn, "version_queries.cypher", "get_requirement_completion_rate", {});
      
      // 検証の完了率
      const verResult = await callNamedDml(conn, "version_queries.cypher", "get_verification_completion_rate", {});
      
      // コード実装の完了率
      const codeResult = await callNamedDml(conn, "version_queries.cypher", "get_code_completion_rate", {});
      
      // トレーサビリティの状況
      const traceResult = await callNamedDml(conn, "version_queries.cypher", "get_traceability_status", {});
      
      console.log("  === プロジェクト総合進捗ダッシュボード ===\n");
      
      reqResult.resetIterator();
      const reqRow = reqResult.getNextSync();
      console.log("  【要件】");
      console.log(`  合計要件数: ${Number(reqRow.total_requirements)}`);
      console.log(`  完了: ${Number(reqRow.completed_requirements)} (${Number(reqRow.requirements_completion_rate).toFixed(2)}%)`);
      console.log(`  進行中: ${Number(reqRow.in_progress_requirements)}`);
      console.log(`  未着手: ${Number(reqRow.not_started_requirements)}\n`);
      
      verResult.resetIterator();
      const verRow = verResult.getNextSync();
      console.log("  【検証】");
      console.log(`  合計検証数: ${Number(verRow.total_verifications)}`);
      console.log(`  合格: ${Number(verRow.passed_verifications)} (${Number(verRow.verification_pass_rate).toFixed(2)}%)`);
      console.log(`  進行中: ${Number(verRow.in_progress_verifications)}`);
      console.log(`  未着手: ${Number(verRow.not_started_verifications)}\n`);
      
      codeResult.resetIterator();
      const codeRow = codeResult.getNextSync();
      console.log("  【コード】");
      console.log(`  合計コード数: ${Number(codeRow.total_code)}`);
      console.log(`  完了: ${Number(codeRow.completed_code)} (${Number(codeRow.code_completion_rate).toFixed(2)}%)`);
      console.log(`  進行中: ${Number(codeRow.in_progress_code)}`);
      console.log(`  未着手: ${Number(codeRow.not_started_code || 0)}\n`);
      
      traceResult.resetIterator();
      const traceRow = traceResult.getNextSync();
      console.log("  【トレーサビリティ】");
      console.log(`  実装がない要件: ${Number(traceRow.requirements_without_code)}`);
      console.log(`  検証がない要件: ${Number(traceRow.requirements_without_verification)}`);
      console.log(`  実装と検証の両方がある要件: ${Number(traceRow.requirements_with_both)} (${Number(traceRow.full_traceability_rate).toFixed(2)}%)\n`);
      
      // 進捗総合評価
      const reqRate = Number(reqRow.requirements_completion_rate || 0);
      const verRate = Number(verRow.verification_pass_rate || 0);
      const codeRate = Number(codeRow.code_completion_rate || 0);
      const traceRate = Number(traceRow.full_traceability_rate || 0);
      
      const weightedProgress = (reqRate * 0.3 + verRate * 0.3 + codeRate * 0.3 + traceRate * 0.1).toFixed(2);
      
      console.log(`  【総合進捗率】: ${weightedProgress}%\n`);
      
      let progressEvaluation = "";
      if (weightedProgress >= 90) {
        progressEvaluation = "優良：プロジェクトはほぼ完了に近い状態です。";
      } else if (weightedProgress >= 70) {
        progressEvaluation = "良好：プロジェクトは順調に進行しています。";
      } else if (weightedProgress >= 50) {
        progressEvaluation = "普通：プロジェクトは進行中ですが、注意が必要です。";
      } else if (weightedProgress >= 30) {
        progressEvaluation = "注意：プロジェクトの進捗が遅れています。対策が必要です。";
      } else {
        progressEvaluation = "危険：プロジェクトの進捗が大幅に遅れています。早急な対策が必要です。";
      }
      
      console.log(`  【進捗評価】: ${progressEvaluation}`);
    } catch (err) {
      console.error(`  総合進捗ダッシュボードの作成に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("実装・テストの進捗状況の集計と分析テストが完了しました。");
    
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