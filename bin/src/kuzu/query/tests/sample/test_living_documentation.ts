/**
 * 階層型トレーサビリティモデル - 動く設計書としての一貫性維持テスト
 * 
 * このファイルはドキュメントとコードの乖離をなくし、常に最新の設計情報を維持できることをテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "living_documentation_test_db";

// メイン実行関数
(async () => {
  console.log("===== 動く設計書としての一貫性維持テスト =====");
  
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
    
    // 4. 動く設計書用のデータを作成
    console.log("\n4. 動く設計書用のデータを作成");
    try {
      const createResult = await callNamedDml(conn, "living_documentation_queries.cypher", "create_living_documentation_data", {});
      
      createResult.resetIterator();
      const createRow = createResult.getNextSync();
      console.log(`  動く設計書用データを作成: 要件=${createRow.created_requirements}件, コード=${createRow.created_code}件, テスト=${createRow.created_tests}件, セクション=${createRow.created_sections}件, コンポーネント=${createRow.created_components}件`);
    } catch (err) {
      console.error(`  動く設計書用データの作成に失敗: ${err}`);
    }
    
    // 5. プロジェクトの設計書セクションを取得
    console.log("\n5. プロジェクトの設計書セクションを取得");
    try {
      const sectionsResult = await callNamedDml(conn, "living_documentation_queries.cypher", "get_project_documentation_sections", {
        projectId: 'PROJ-001'
      });
      
      console.log("  プロジェクト「サンプルプロジェクト」の設計書セクション:");
      console.log("  セクションID | タイトル | 説明 | 順序 | 最終更新日");
      console.log("  ------------|----------|------|------|------------");
      
      sectionsResult.resetIterator();
      while (sectionsResult.hasNext()) {
        const row = sectionsResult.getNextSync();
        console.log(`  ${row.section_id} | ${row.section_title} | ${row.section_description} | ${row.section_order} | ${row.last_updated}`);
      }
    } catch (err) {
      console.error(`  プロジェクトの設計書セクション取得に失敗: ${err}`);
    }
    
    // 6. 設計書セクションの詳細と関連コンポーネントを取得
    console.log("\n6. 設計書セクションの詳細と関連コンポーネントを取得");
    try {
      const sectionResult = await callNamedDml(conn, "living_documentation_queries.cypher", "get_section_content", {
        sectionId: 'DOC-SECTION-002'
      });
      
      sectionResult.resetIterator();
      const sectionRow = sectionResult.getNextSync();
      
      console.log(`  セクション: ${sectionRow.section_title} (${sectionRow.section_id})`);
      console.log(`  説明: ${sectionRow.section_description}`);
      console.log(`  最終更新日: ${sectionRow.last_updated}`);
      
      console.log("\n  コンポーネント一覧:");
      if (sectionRow.components && sectionRow.components.length > 0) {
        sectionRow.components.forEach((component: any, index: number) => {
          console.log(`  ${index + 1}. ${component.title} (${component.id}) - タイプ: ${component.content_type}`);
          
          // コンテンツの一部を表示（長い場合は省略）
          if (component.content) {
            const contentPreview = component.content.length > 100 ? component.content.substring(0, 100) + '...' : component.content;
            console.log(`     ${contentPreview}`);
          }
        });
      } else {
        console.log("    (コンポーネントなし)");
      }
    } catch (err) {
      console.error(`  設計書セクションの詳細取得に失敗: ${err}`);
    }
    
    // 7. 特定のセクションが文書化している要件を取得
    console.log("\n7. 特定のセクションが文書化している要件を取得");
    try {
      const reqResult = await callNamedDml(conn, "living_documentation_queries.cypher", "get_section_requirements", {
        sectionId: 'DOC-SECTION-002'
      });
      
      console.log(`  セクション「認証機能」が文書化している要件:`);
      console.log("  要件ID | タイトル | 説明 | 優先度 | 状態 | 実装");
      console.log("  -------|----------|------|--------|------|------");
      
      reqResult.resetIterator();
      while (reqResult.hasNext()) {
        const row = reqResult.getNextSync();
        const implStr = row.implementations && row.implementations.length > 0 ? row.implementations.join(', ') : '(なし)';
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.requirement_description.substring(0, 30)}... | ${row.requirement_priority} | ${row.requirement_status} | ${implStr}`);
      }
    } catch (err) {
      console.error(`  セクションが文書化している要件の取得に失敗: ${err}`);
    }
    
    // 8. 特定のセクションが文書化しているテストを取得
    console.log("\n8. 特定のセクションが文書化しているテストを取得");
    try {
      const verResult = await callNamedDml(conn, "living_documentation_queries.cypher", "get_section_verifications", {
        sectionId: 'DOC-SECTION-002'
      });
      
      console.log(`  セクション「認証機能」が文書化している検証:`);
      console.log("  検証ID | 名前 | 説明 | タイプ | 実装 | 関連要件");
      console.log("  --------|------|------|--------|------|----------");
      
      verResult.resetIterator();
      while (verResult.hasNext()) {
        const row = verResult.getNextSync();
        const implStr = row.implementations && row.implementations.length > 0 ? row.implementations.join(', ') : '(なし)';
        const reqIdsStr = row.requirement_ids && row.requirement_ids.length > 0 ? row.requirement_ids.join(', ') : '(なし)';
        console.log(`  ${row.verification_id} | ${row.verification_name} | ${row.verification_description.substring(0, 30)}... | ${row.verification_type} | ${implStr} | ${reqIdsStr}`);
      }
    } catch (err) {
      console.error(`  セクションが文書化している検証の取得に失敗: ${err}`);
    }
    
    // 9. コードの変更による設計書セクションの特定
    console.log("\n9. コードの変更による設計書セクションの特定");
    try {
      const affectedResult = await callNamedDml(conn, "living_documentation_queries.cypher", "identify_affected_documentation", {
        codeId: 'CODE-DOC-001'
      });
      
      affectedResult.resetIterator();
      const affectedRow = affectedResult.getNextSync();
      
      console.log(`  コード「${affectedRow.code_name} (${affectedRow.code_id})」の変更による影響:`);
      
      console.log("\n  直接参照しているセクション:");
      if (affectedRow.direct_references && affectedRow.direct_references.length > 0) {
        affectedRow.direct_references.forEach((section: any, index: number) => {
          console.log(`    ${index + 1}. ${section.title} (${section.id}) - 理由: ${section.reason}`);
        });
      } else {
        console.log("    (直接参照しているセクションなし)");
      }
      
      console.log("\n  要件を通じて関連するセクション:");
      if (affectedRow.requirement_references && affectedRow.requirement_references.length > 0) {
        affectedRow.requirement_references.forEach((section: any, index: number) => {
          console.log(`    ${index + 1}. ${section.title} (${section.id}) - 理由: ${section.reason}`);
        });
      } else {
        console.log("    (要件を通じて関連するセクションなし)");
      }
      
      console.log("\n  検証を通じて関連するセクション:");
      if (affectedRow.verification_references && affectedRow.verification_references.length > 0) {
        affectedRow.verification_references.forEach((section: any, index: number) => {
          console.log(`    ${index + 1}. ${section.title} (${section.id}) - 理由: ${section.reason}`);
        });
      } else {
        console.log("    (検証を通じて関連するセクションなし)");
      }
    } catch (err) {
      console.error(`  コードの変更による設計書セクションの特定に失敗: ${err}`);
    }
    
    // 10. 要件の変更による設計書セクションの特定
    console.log("\n10. 要件の変更による設計書セクションの特定");
    try {
      const affectedByReqResult = await callNamedDml(conn, "living_documentation_queries.cypher", "identify_affected_sections_by_requirement", {
        requirementId: 'REQ-DOC-001'
      });
      
      affectedByReqResult.resetIterator();
      const reqAffectedRow = affectedByReqResult.getNextSync();
      
      console.log(`  要件「${reqAffectedRow.requirement_title} (${reqAffectedRow.requirement_id})」の変更による影響:`);
      
      console.log("\n  直接文書化しているセクション:");
      if (reqAffectedRow.direct_references && reqAffectedRow.direct_references.length > 0) {
        reqAffectedRow.direct_references.forEach((section: any, index: number) => {
          console.log(`    ${index + 1}. ${section.title} (${section.id}) - 理由: ${section.reason}`);
        });
      } else {
        console.log("    (直接文書化しているセクションなし)");
      }
      
      console.log("\n  検証を通じて関連するセクション:");
      if (reqAffectedRow.verification_references && reqAffectedRow.verification_references.length > 0) {
        reqAffectedRow.verification_references.forEach((section: any, index: number) => {
          console.log(`    ${index + 1}. ${section.title} (${section.id}) - 理由: ${section.reason}`);
        });
      } else {
        console.log("    (検証を通じて関連するセクションなし)");
      }
    } catch (err) {
      console.error(`  要件の変更による設計書セクションの特定に失敗: ${err}`);
    }
    
    // 11. ドキュメントの依存関係を分析
    console.log("\n11. ドキュメントの依存関係を分析");
    try {
      const dependencyResult = await callNamedDml(conn, "living_documentation_queries.cypher", "analyze_documentation_dependencies", {});
      
      console.log("  ドキュメントの依存関係分析:");
      console.log("  セクションID | タイトル | 要件依存数 | 検証依存数 | コード依存数 | 総依存数");
      console.log("  ------------|----------|------------|------------|--------------|--------");
      
      dependencyResult.resetIterator();
      while (dependencyResult.hasNext()) {
        const row = dependencyResult.getNextSync();
        console.log(`  ${row.section_id} | ${row.section_title} | ${row.requirement_dependencies} | ${row.verification_dependencies} | ${row.code_dependencies} | ${row.total_dependencies}`);
      }
    } catch (err) {
      console.error(`  ドキュメントの依存関係分析に失敗: ${err}`);
    }
    
    // 12. 整合性チェック - ドキュメントの更新が必要な要素を特定
    console.log("\n12. 整合性チェック - ドキュメントの更新が必要な要素を特定");
    try {
      const consistencyResult = await callNamedDml(conn, "living_documentation_queries.cypher", "check_documentation_consistency", {});
      
      consistencyResult.resetIterator();
      const consistencyRow = consistencyResult.getNextSync();
      
      console.log("  ドキュメントの整合性チェック結果:");
      
      console.log("\n  文書化されていない要件:");
      if (consistencyRow.undocumented_requirements && consistencyRow.undocumented_requirements.length > 0) {
        consistencyRow.undocumented_requirements.forEach((req: any, index: number) => {
          console.log(`    ${index + 1}. ${req.title} (${req.id})`);
        });
      } else {
        console.log("    (文書化されていない要件なし)");
      }
      
      console.log("\n  文書化されていないテスト:");
      if (consistencyRow.undocumented_verifications && consistencyRow.undocumented_verifications.length > 0) {
        consistencyRow.undocumented_verifications.forEach((ver: any, index: number) => {
          console.log(`    ${index + 1}. ${ver.name} (${ver.id})`);
        });
      } else {
        console.log("    (文書化されていないテストなし)");
      }
      
      console.log("\n  古いドキュメント（最終更新から30日以上経過）:");
      if (consistencyRow.outdated_sections && consistencyRow.outdated_sections.length > 0) {
        consistencyRow.outdated_sections.forEach((section: any, index: number) => {
          console.log(`    ${index + 1}. ${section.title} (${section.id}) - 最終更新日: ${section.last_updated}`);
        });
      } else {
        console.log("    (古いドキュメントなし)");
      }
      
      console.log(`\n  文書化されていないコード数: ${consistencyRow.undocumented_code_count}件`);
    } catch (err) {
      console.error(`  整合性チェックに失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("動く設計書としての一貫性維持テストが完了しました。");
    
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