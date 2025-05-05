/**
 * 階層型トレーサビリティモデル - 階層関係テスト
 * 
 * このファイルは要件とコードの階層構造をLocationURIで一元管理する機能をテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "hierarchy_relation_test_db";

// メイン実行関数
(async () => {
  console.log("===== 階層関係テスト =====");
  
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
    
    // 4. 初期状態の確認
    console.log("\n4. 初期状態の確認");
    console.log("ノード総数の確認:");
    try {
      const nodesResult = await callNamedDml(conn, "basic_queries.cypher", "count_nodes", {});
      nodesResult.resetIterator();
      const row = nodesResult.getNextSync();
      console.log(`  データベース内のノード総数: ${row.count}件`);
    } catch (err) {
      console.error(`  ノード総数の取得に失敗: ${err}`);
    }
    
    // 5. LocationURI階層構造のテスト
    console.log("\n5. LocationURI階層構造のテスト");
    // 新しいLocationURIを作成し、既存のLocationURIと階層関係を作成する
    try {
      const createResult = await callNamedDml(conn, "hierarchy_test_queries.cypher", "create_test_location", {});
      
      createResult.resetIterator();
      const locationRow = createResult.getNextSync();
      const newLocationId = locationRow["l.uri_id"];
      console.log(`  新しいLocationURIを作成: ${newLocationId}, パス: ${locationRow["l.path"]}`);
      
      // 親ディレクトリのLocationURIを作成
      const parentResult = await callNamedDml(conn, "hierarchy_test_queries.cypher", "create_parent_location", {});
      
      parentResult.resetIterator();
      const parentRow = parentResult.getNextSync();
      const parentLocationId = parentRow["l.uri_id"];
      console.log(`  親LocationURIを作成: ${parentLocationId}, パス: ${parentRow["l.path"]}`);
      
      // 階層関係を作成
      const relationshipResult = await callNamedDml(conn, "hierarchy_test_queries.cypher", "create_hierarchy_relationship", {});
      
      relationshipResult.resetIterator();
      const relRow = relationshipResult.getNextSync();
      console.log(`  階層関係を作成: ${relRow["parent.uri_id"]} -> ${relRow["child.uri_id"]}`);
    } catch (err) {
      console.error(`  LocationURI階層構造のテストに失敗: ${err}`);
    }
    
    // 6. 子階層の取得テスト
    console.log("\n6. 子階層の取得テスト");
    try {
      const childrenResult = await callNamedDml(conn, "hierarchy_test_queries.cypher", "get_child_locations", {});
      
      childrenResult.resetIterator();
      if (childrenResult.hasNext()) {
        const firstRow = childrenResult.getNextSync();
        console.log(`  親パス ${firstRow.parent_path} の子要素:`);
        
        // 最初の行は既に取得済みなので、まずそれを表示
        console.log(`    - ${firstRow.child_path}`);
        
        // 残りの行を取得
        while (childrenResult.hasNext()) {
          const row = childrenResult.getNextSync();
          console.log(`    - ${row.child_path}`);
        }
      }
    } catch (err) {
      console.error(`  子階層の取得テストに失敗: ${err}`);
    }
    
    // 7. 要件とコードの階層関係のテスト
    console.log("\n7. 要件とコードの階層関係のテスト");
    try {
      // 要件とLocationURIの関連付け
      const reqLocationResult = await callNamedDml(conn, "hierarchy_test_queries.cypher", "create_test_requirement_with_location", {});
      
      reqLocationResult.resetIterator();
      const reqRow = reqLocationResult.getNextSync();
      console.log(`  要件と階層の関連付け: ${reqRow["r.id"]} -> ${reqRow["l.uri_id"]}`);
      
      // コードエンティティとLocationURIの関連付け
      const codeLocationResult = await callNamedDml(conn, "hierarchy_test_queries.cypher", "create_test_code_with_location", {});
      
      codeLocationResult.resetIterator();
      const codeRow = codeLocationResult.getNextSync();
      console.log(`  コードと階層の関連付け: ${codeRow["c.persistent_id"]} -> ${codeRow["l.uri_id"]}`);
    } catch (err) {
      console.error(`  要件とコードの階層関係のテストに失敗: ${err}`);
    }
    
    // 8. 同一階層に属する要件とコードの検索
    console.log("\n8. 同一階層に属する要件とコードの検索");
    try {
      const sameLocationResult = await callNamedDml(conn, "hierarchy_test_queries.cypher", "find_requirements_code_same_location", {});
      
      console.log(`  同一階層の要件とコードのペア数: ${sameLocationResult.getNumTuples()}`);
      
      sameLocationResult.resetIterator();
      while (sameLocationResult.hasNext()) {
        const row = sameLocationResult.getNextSync();
        console.log(`    - 要件「${row.requirement_title}」(${row.requirement_id})とコード「${row.code_name}」(${row.code_id})が同じ場所: ${row.location_path}`);
      }
    } catch (err) {
      console.error(`  同一階層の検索に失敗: ${err}`);
    }
    
    // 9. 階層構造を活用した複雑なナビゲーションテスト
    console.log("\n9. 階層構造を活用した複雑なナビゲーションテスト");
    try {
      const navigationResult = await callNamedDml(conn, "hierarchy_test_queries.cypher", "navigate_hierarchy_structure", {});
      
      console.log(`  階層ナビゲーション結果: ${navigationResult.getNumTuples()}件`);
      
      navigationResult.resetIterator();
      while (navigationResult.hasNext()) {
        const row = navigationResult.getNextSync();
        console.log(`    - 親ディレクトリ: ${row.parent_directory}`);
        console.log(`      ファイルパス: ${row.file_path}`);
        console.log(`      要件: ${Array.isArray(row.requirements) && row.requirements.length > 0 ? row.requirements : '(なし)'}`);
        console.log(`      コードエンティティ: ${Array.isArray(row.code_entities) && row.code_entities.length > 0 ? row.code_entities : '(なし)'}`);
      }
    } catch (err) {
      console.error(`  階層ナビゲーションテストに失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("要件とコードの階層関係テストが完了しました。");
    
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
