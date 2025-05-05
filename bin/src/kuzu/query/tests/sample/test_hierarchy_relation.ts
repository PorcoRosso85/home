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
      const createLocationQuery = `
        CREATE (l:LocationURI {
          uri_id: 'hierarchy-test-uri',
          scheme: 'file',
          path: '/src/components/user/profile.ts',
          fragment: 'UserProfile'
        })
        RETURN l.uri_id, l.path;
      `;
      const createResult = await conn.query(createLocationQuery);
      
      createResult.resetIterator();
      const locationRow = createResult.getNextSync();
      const newLocationId = locationRow["l.uri_id"];
      console.log(`  新しいLocationURIを作成: ${newLocationId}, パス: ${locationRow["l.path"]}`);
      
      // 親ディレクトリのLocationURIを作成
      const createParentQuery = `
        CREATE (l:LocationURI {
          uri_id: 'hierarchy-parent-uri',
          scheme: 'file',
          path: '/src/components/user'
        })
        RETURN l.uri_id, l.path;
      `;
      const parentResult = await conn.query(createParentQuery);
      
      parentResult.resetIterator();
      const parentRow = parentResult.getNextSync();
      const parentLocationId = parentRow["l.uri_id"];
      console.log(`  親LocationURIを作成: ${parentLocationId}, パス: ${parentRow["l.path"]}`);
      
      // 階層関係を作成
      const createRelationshipQuery = `
        MATCH (parent:LocationURI {uri_id: 'hierarchy-parent-uri'}),
              (child:LocationURI {uri_id: 'hierarchy-test-uri'})
        CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'directory'}]->(child)
        RETURN parent.uri_id, child.uri_id;
      `;
      const relationshipResult = await conn.query(createRelationshipQuery);
      
      relationshipResult.resetIterator();
      const relRow = relationshipResult.getNextSync();
      console.log(`  階層関係を作成: ${relRow["parent.uri_id"]} -> ${relRow["child.uri_id"]}`);
    } catch (err) {
      console.error(`  LocationURI階層構造のテストに失敗: ${err}`);
    }
    
    // 6. 子階層の取得テスト
    console.log("\n6. 子階層の取得テスト");
    try {
      const getChildrenQuery = `
        MATCH (parent:LocationURI {uri_id: 'hierarchy-parent-uri'})-[:CONTAINS_LOCATION]->(child:LocationURI)
        RETURN parent.path AS parent_path, child.path AS child_path;
      `;
      const childrenResult = await conn.query(getChildrenQuery);
      
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
      const createReqLocationQuery = `
        CREATE (r:RequirementEntity {
          id: 'REQ-HIERARCHY-TEST',
          title: '階層テスト要件',
          description: 'これは階層関係テスト用の要件です',
          priority: 'high',
          requirement_type: 'functional'
        })
        WITH r
        MATCH (l:LocationURI {uri_id: 'hierarchy-test-uri'})
        CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l)
        RETURN r.id, l.uri_id;
      `;
      const reqLocationResult = await conn.query(createReqLocationQuery);
      
      reqLocationResult.resetIterator();
      const reqRow = reqLocationResult.getNextSync();
      console.log(`  要件と階層の関連付け: ${reqRow["r.id"]} -> ${reqRow["l.uri_id"]}`);
      
      // コードエンティティとLocationURIの関連付け
      const createCodeLocationQuery = `
        CREATE (c:CodeEntity {
          persistent_id: 'CODE-HIERARCHY-TEST',
          name: 'UserProfileComponent',
          type: 'component',
          signature: 'class UserProfileComponent',
          complexity: 5,
          start_position: 100,
          end_position: 500
        })
        WITH c
        MATCH (l:LocationURI {uri_id: 'hierarchy-test-uri'})
        CREATE (c)-[:HAS_LOCATION]->(l)
        RETURN c.persistent_id, l.uri_id;
      `;
      const codeLocationResult = await conn.query(createCodeLocationQuery);
      
      codeLocationResult.resetIterator();
      const codeRow = codeLocationResult.getNextSync();
      console.log(`  コードと階層の関連付け: ${codeRow["c.persistent_id"]} -> ${codeRow["l.uri_id"]}`);
    } catch (err) {
      console.error(`  要件とコードの階層関係のテストに失敗: ${err}`);
    }
    
    // 8. 同一階層に属する要件とコードの検索
    console.log("\n8. 同一階層に属する要件とコードの検索");
    try {
      const sameLocationQuery = `
        MATCH (r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)<-[:HAS_LOCATION]-(c:CodeEntity)
        RETURN r.id AS requirement_id, r.title AS requirement_title, 
               l.uri_id AS location_uri, l.path AS location_path,
               c.persistent_id AS code_id, c.name AS code_name;
      `;
      const sameLocationResult = await conn.query(sameLocationQuery);
      
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
      const navigationQuery = `
        MATCH (parent:LocationURI)-[:CONTAINS_LOCATION*]->(child:LocationURI)
        OPTIONAL MATCH (r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(child)
        OPTIONAL MATCH (c:CodeEntity)-[:HAS_LOCATION]->(child)
        RETURN parent.path AS parent_directory,
               child.path AS file_path,
               collect(DISTINCT r.title) AS requirements,
               collect(DISTINCT c.name) AS code_entities;
      `;
      const navigationResult = await conn.query(navigationQuery);
      
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
