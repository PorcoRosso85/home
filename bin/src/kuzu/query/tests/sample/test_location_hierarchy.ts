/**
 * 階層型トレーサビリティモデル - LocationURI階層構造テスト
 * 
 * このファイルはLocationURI階層を通じた要件構造の柔軟な表現をテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "location_hierarchy_test_db";

// メイン実行関数
(async () => {
  console.log("===== LocationURI階層構造テスト =====");
  
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
    
    // 4. モジュール階層構造の作成
    console.log("\n4. モジュール階層構造の作成");
    try {
      const createResult = await callNamedDml(conn, "location_hierarchy_queries.cypher", "create_module_hierarchy", {});
      
      createResult.resetIterator();
      const resultRow = createResult.getNextSync();
      console.log(`  モジュール階層構造を作成: ${resultRow.created_nodes}ノード`);
    } catch (err) {
      console.error(`  モジュール階層構造の作成に失敗: ${err}`);
    }
    
    // 5. 階層を可視化する
    console.log("\n5. 階層を可視化する");
    try {
      const hierarchyResult = await callNamedDml(conn, "location_hierarchy_queries.cypher", "visualize_hierarchy", {});
      
      console.log("  モジュール階層構造の可視化:");
      console.log("  深さ | パス | ID");
      console.log("  -----|------|----");
      
      hierarchyResult.resetIterator();
      while (hierarchyResult.hasNext()) {
        const row = hierarchyResult.getNextSync();
        const indentation = '  '.repeat(row.hierarchy_depth);
        console.log(`  ${row.hierarchy_depth} | ${indentation}${row.child_path} | ${row.child_id}`);
      }
    } catch (err) {
      console.error(`  階層の可視化に失敗: ${err}`);
    }
    
    // 6. 要件をモジュール階層にマッピング
    console.log("\n6. 要件をモジュール階層にマッピング");
    try {
      const requirementsResult = await callNamedDml(conn, "location_hierarchy_queries.cypher", "create_requirements_with_mapping", {});
      
      requirementsResult.resetIterator();
      const reqRow = requirementsResult.getNextSync();
      console.log(`  要件をモジュール階層にマッピング: ${reqRow.created_requirements}要件`);
    } catch (err) {
      console.error(`  要件のモジュール階層へのマッピングに失敗: ${err}`);
    }
    
    // 7. モジュール階層に基づく要件のナビゲーション
    console.log("\n7. モジュール階層に基づく要件のナビゲーション");
    try {
      const navigationResult = await callNamedDml(conn, "location_hierarchy_queries.cypher", "navigate_requirements_by_module", {});
      
      console.log("  モジュール階層と要件のマッピング:");
      navigationResult.resetIterator();
      while (navigationResult.hasNext()) {
        const row = navigationResult.getNextSync();
        const indentation = '  '.repeat(Math.max(0, row.depth));
        console.log(`  ${indentation}${row.module_path}:`);
        
        if (row.requirements_list && row.requirements_list.length > 0) {
          row.requirements_list.forEach((req: string) => {
            console.log(`  ${indentation}  - ${req}`);
          });
        } else {
          console.log(`  ${indentation}  (要件なし)`);
        }
      }
    } catch (err) {
      console.error(`  モジュール階層に基づく要件のナビゲーションに失敗: ${err}`);
    }
    
    // 8. 特定モジュールの子要件を再帰的に取得
    console.log("\n8. 特定モジュールの子要件を再帰的に取得");
    try {
      const childReqResult = await callNamedDml(conn, "location_hierarchy_queries.cypher", "get_child_requirements", {
        moduleId: 'module-auth'
      });
      
      console.log(`  authモジュールとその子モジュールの要件:`);
      childReqResult.resetIterator();
      while (childReqResult.hasNext()) {
        const row = childReqResult.getNextSync();
        console.log(`  モジュール: ${row.module_path}`);
        
        for (let i = 0; i < row.requirement_ids.length; i++) {
          console.log(`    - ${row.requirement_titles[i]} (${row.requirement_ids[i]})`);
        }
      }
    } catch (err) {
      console.error(`  特定モジュールの子要件の再帰的取得に失敗: ${err}`);
    }
    
    // 9. 階層関係とともにコード実装を追加
    console.log("\n9. 階層関係とともにコード実装を追加");
    try {
      const codeResult = await callNamedDml(conn, "location_hierarchy_queries.cypher", "add_code_implementation", {});
      
      codeResult.resetIterator();
      const codeRow = codeResult.getNextSync();
      console.log(`  コード実装を追加: ${codeRow["authService.persistent_id"]}, ${codeRow["loginController.persistent_id"]}, ${codeRow["registerController.persistent_id"]}`);
    } catch (err) {
      console.error(`  階層関係とともにコード実装の追加に失敗: ${err}`);
    }
    
    // 10. 階層構造全体を通じた追跡（要件→モジュール→コード）
    console.log("\n10. 階層構造全体を通じた追跡（要件→モジュール→コード）");
    try {
      const traceResult = await callNamedDml(conn, "location_hierarchy_queries.cypher", "trace_hierarchy", {});
      
      console.log("  階層構造全体を通じた追跡結果:");
      traceResult.resetIterator();
      while (traceResult.hasNext()) {
        const row = traceResult.getNextSync();
        console.log(`\n  要件: ${row.requirement_title} (${row.requirement_id})`);
        console.log(`  モジュール: ${row.module_path} (親: ${row.parent_module || 'なし'})`);
        
        const moduleCodeList = row.module_code_ids || [];
        console.log(`  モジュール内のコード: ${moduleCodeList.length > 0 ? moduleCodeList.join(', ') : '(なし)'}`);
        
        const implCodeList = row.implementing_code_ids || [];
        console.log(`  実装コード: ${implCodeList.length > 0 ? implCodeList.join(', ') : '(なし)'}`);
      }
    } catch (err) {
      console.error(`  階層構造全体を通じた追跡に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("LocationURI階層を通じた要件構造の柔軟な表現テストが完了しました。");
    
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