/**
 * 階層型トレーサビリティモデル - 依存関係分析テスト
 * 
 * このファイルは依存関係の分析と影響範囲の可視化機能をテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "dependency_analysis_test_db";

// メイン実行関数
(async () => {
  console.log("===== 依存関係分析テスト =====");
  
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
    await callDml(conn, "sample_relationships.cypher");
    console.log("✓ テストデータ挿入完了");
    
    // 4. 依存関係を持つ要件の作成
    console.log("\n4. 依存関係を持つ要件の作成");
    try {
      // テスト用の要件を作成し、依存関係を構築
      const dependenciesResult = await callNamedDml(conn, "dependency_analysis_queries.cypher", "create_dependencies_structure", {});
      
      dependenciesResult.resetIterator();
      const depRow = dependenciesResult.getNextSync();
      console.log(`  依存関係を持つ要件を作成:`);
      console.log(`    親要件: ${depRow["parent.id"]}`);
      console.log(`    子要件: ${depRow["child1.id"]}, ${depRow["child2.id"]}, ${depRow["child3.id"]}`);
      console.log(`    関連要件: ${depRow["related1.id"]}, ${depRow["related2.id"]}`);
    } catch (err) {
      console.error(`  依存関係を持つ要件の作成に失敗: ${err}`);
    }
    
    // 5. 要件から上流依存関係の分析
    console.log("\n5. 要件から上流依存関係の分析");
    try {
      const upstreamResult = await callNamedDml(conn, "dependency_analysis_queries.cypher", "get_upstream_dependencies", {});
      
      console.log(`  要件「REQ-DEP-CHILD1」の上流依存関係:`);
      upstreamResult.resetIterator();
      let count = 1;
      while (upstreamResult.hasNext()) {
        const row = upstreamResult.getNextSync();
        console.log(`    ${count}. ${row["r.title"]} (${row["r.id"]}) -> ${row["dep.title"]} (${row["dep.id"]}), 優先度: ${row["dep.priority"]}`);
        count++;
      }
    } catch (err) {
      console.error(`  要件から上流依存関係の分析に失敗: ${err}`);
    }
    
    // 6. 要件から下流依存関係の分析
    console.log("\n6. 要件から下流依存関係の分析");
    try {
      const downstreamResult = await callNamedDml(conn, "dependency_analysis_queries.cypher", "get_downstream_dependencies", {});
      
      console.log(`  要件「REQ-DEP-PARENT」の下流依存関係:`);
      downstreamResult.resetIterator();
      let count = 1;
      while (downstreamResult.hasNext()) {
        const row = downstreamResult.getNextSync();
        console.log(`    ${count}. ${row["r.title"]} (${row["r.id"]}) <- ${row["dep.title"]} (${row["dep.id"]}), 優先度: ${row["dep.priority"]}`);
        count++;
      }
    } catch (err) {
      console.error(`  要件から下流依存関係の分析に失敗: ${err}`);
    }
    
    // 7. コード実装の依存関係を作成
    console.log("\n7. コード実装の依存関係を作成");
    try {
      const codeDepResult = await callNamedDml(conn, "dependency_analysis_queries.cypher", "create_code_dependencies", {});
      
      codeDepResult.resetIterator();
      const codeRow = codeDepResult.getNextSync();
      console.log(`  コード依存関係を作成:`);
      console.log(`    コンポーネント: ${codeRow["controller.persistent_id"]} -> ${codeRow["service.persistent_id"]} -> ${codeRow["repository.persistent_id"]}`);
    } catch (err) {
      console.error(`  コード実装の依存関係の作成に失敗: ${err}`);
    }
    
    // 8. 変更影響分析：要件変更時の影響範囲
    console.log("\n8. 変更影響分析：要件変更時の影響範囲");
    try {
      const impactResult = await callNamedDml(conn, "dependency_analysis_queries.cypher", "analyze_requirement_impact", {});
      
      impactResult.resetIterator();
      const impactRow = impactResult.getNextSync();
      
      console.log(`  要件「${impactRow["changed_req"]}」が変更された場合の影響分析:`);
      console.log(`    影響を受ける要件: ${impactRow["affected_requirements"].join(', ') || '(なし)'}`);
      console.log(`    直接実装されているコード: ${impactRow["direct_code"].join(', ') || '(なし)'}`);
      console.log(`    下流要件を通じて影響するコード: ${impactRow["requirement_dependent_code"].join(', ') || '(なし)'}`);
      console.log(`    コード依存関係を通じて影響するコード: ${impactRow["code_dependent_code"].join(', ') || '(なし)'}`);
    } catch (err) {
      console.error(`  要件変更時の影響範囲分析に失敗: ${err}`);
    }
    
    // 9. 変更影響分析：コード変更時の影響範囲
    console.log("\n9. 変更影響分析：コード変更時の影響範囲");
    try {
      const codeImpactResult = await callNamedDml(conn, "dependency_analysis_queries.cypher", "analyze_code_impact", {});
      
      codeImpactResult.resetIterator();
      const codeImpactRow = codeImpactResult.getNextSync();
      
      console.log(`  コード「${codeImpactRow["code_name"]} (${codeImpactRow["changed_code"]})」が変更された場合の影響分析:`);
      console.log(`    影響を受ける上流コード: ${codeImpactRow["upstream_code"].join(', ') || '(なし)'}`);
      console.log(`    影響を受ける下流コード: ${codeImpactRow["downstream_code"].join(', ') || '(なし)'}`);
      console.log(`    直接関連する要件: ${codeImpactRow["direct_requirements"].join(', ') || '(なし)'}`);
      console.log(`    間接的に関連する要件: ${codeImpactRow["upstream_requirements"].join(', ') || '(なし)'}`);
    } catch (err) {
      console.error(`  コード変更時の影響範囲分析に失敗: ${err}`);
    }
    
    // 10. 多段階の依存関係分析
    console.log("\n10. 多段階の依存関係分析");
    try {
      // コード間の多段階依存関係を作成
      await callNamedDml(conn, "dependency_analysis_queries.cypher", "create_multi_level_dependencies", {});
      
      // 多段階の依存関係を分析
      const multiLevelResult = await callNamedDml(conn, "dependency_analysis_queries.cypher", "analyze_multi_level_dependencies", {});
      
      multiLevelResult.resetIterator();
      const multiLevelRow = multiLevelResult.getNextSync();
      
      console.log(`  コンポーネント「${multiLevelRow["start_component"]}」の多段階依存関係分析:`);
      console.log(`    依存コンポーネント: ${multiLevelRow["dependent_components"].join(', ')}`);
      console.log(`    依存コンポーネントID: ${multiLevelRow["dependent_component_ids"].join(', ')}`);
      
      // 依存関係の最大深度分析
      const depthResult = await callNamedDml(conn, "dependency_analysis_queries.cypher", "analyze_dependency_depth", {});
      
      depthResult.resetIterator();
      if (depthResult.hasNext()) {
        const depthRow = depthResult.getNextSync();
        console.log(`\n  依存関係の最大深度:`);
        console.log(`    開始コンポーネント: ${depthRow["start_component"]}`);
        console.log(`    終端コンポーネント: ${depthRow["end_component"]}`);
        console.log(`    最大深度: ${depthRow["max_dependency_depth"]}`);
      }
    } catch (err) {
      console.error(`  多段階の依存関係分析に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("依存関係の分析と影響範囲の可視化テストが完了しました。");
    
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
