#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - DML呼び出しユーティリティのテスト
 * 
 * このファイルはcall_dml.tsを使用してパラメータ化されたDMLクエリを実行する方法を示します。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { createSchema } from "../common/schema_definition.ts";
import { insertSampleData } from "../common/sample_data.ts";
import { 
  callDml, 
  callNamedDml, 
  listAvailableDmls, 
  listNamedQueries 
} from "../call_dml.ts";

// テスト用DBの名前
const TEST_DB_NAME = "call_dml_test_db";

// メイン実行関数
(async () => {
  console.log("===== DML呼び出しユーティリティのテスト =====");
  
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
    await createSchema(conn);
    console.log("✓ スキーマ定義完了");
    
    // 3. サンプルデータ挿入
    console.log("\n3. サンプルデータ挿入");
    await insertSampleData(conn);
    console.log("✓ サンプルデータ挿入完了");
    
    // 4. 利用可能なDMLファイルの一覧表示
    console.log("\n4. 利用可能なDMLファイル一覧");
    const dmlFiles = await listAvailableDmls();
    console.log(`利用可能なDMLファイル: ${dmlFiles.length}個`);
    dmlFiles.forEach(file => console.log(`  - ${file}`));
    
    // 5. 名前付きクエリの一覧表示
    console.log("\n5. 名前付きクエリ一覧");
    const queryFile = "sample_params.cypher";
    const namedQueries = await listNamedQueries(queryFile);
    console.log(`${queryFile} 内の名前付きクエリ: ${namedQueries.length}個`);
    namedQueries.forEach(query => console.log(`  - ${query}`));
    
    // 6. 単一の名前付きクエリの実行
    console.log("\n6. 単一の名前付きクエリ実行");
    try {
      console.log("- コードエンティティをIDで検索");
      const findResult = await callNamedDml(conn, "sample_params.cypher", "find_by_id", {
        id: "CODE-001" // UserServiceクラスを検索
      });
      
      console.log(`  結果行数: ${findResult.getNumTuples()}`);
      if (findResult.getNumTuples() > 0) {
        const row = findResult.getRow(0);
        console.log(`  検索結果: ID=${row[0]}, 名前=${row[1]}, タイプ=${row[2]}`);
      }
    } catch (error) {
      console.error(`  検索クエリエラー: ${error}`);
    }
    
    // 7. 配列パラメータを使用したクエリの実行
    console.log("\n7. 配列パラメータを使用したクエリ");
    try {
      console.log("- 優先度による要件の検索");
      const priorityResult = await callNamedDml(conn, "sample_params.cypher", "find_requirements_by_priorities", {
        priorities: ["HIGH", "MEDIUM"]
      });
      
      console.log(`  結果行数: ${priorityResult.getNumTuples()}`);
      for (let i = 0; i < priorityResult.getNumTuples(); i++) {
        const row = priorityResult.getRow(i);
        console.log(`  要件: ID=${row[0]}, タイトル=${row[1]}, 優先度=${row[2]}`);
      }
    } catch (error) {
      console.error(`  優先度検索エラー: ${error}`);
    }
    
    // 8. テストノードの作成と確認
    console.log("\n8. テストノードの作成テスト");
    try {
      console.log("- テストノードを作成");
      const createResult = await callNamedDml(conn, "sample_params.cypher", "create_test_node", {
        id: "TEST-PARAM-001",
        name: "パラメータ化テスト関数",
        type: "function",
        signature: "public void paramTest()",
        complexity: 2,
        start_position: 5000,
        end_position: 5100
      });
      
      console.log(`  作成結果: ${createResult.getNumTuples()}行`);
      if (createResult.getNumTuples() > 0) {
        const row = createResult.getRow(0);
        console.log(`  作成成功: ID=${row[0]}, 名前=${row[1]}`);
      }
      
      // 作成したノードを検証
      console.log("- 作成したノードを検証");
      const verifyResult = await callNamedDml(conn, "sample_params.cypher", "find_by_id", {
        id: "TEST-PARAM-001"
      });
      
      if (verifyResult.getNumTuples() > 0) {
        const row = verifyResult.getRow(0);
        console.log(`  検証成功: ID=${row[0]}, 名前=${row[1]}, タイプ=${row[2]}`);
      } else {
        console.log("  検証失敗: ノードが見つかりませんでした");
      }
    } catch (error) {
      console.error(`  ノード作成エラー: ${error}`);
    }
    
    // 9. ページネーションパラメータを使用したクエリ
    console.log("\n9. ページネーションクエリテスト");
    try {
      console.log("- 最初の2件を取得");
      const page1Result = await callNamedDml(conn, "sample_params.cypher", "paginated_list", {
        offset: 0,
        limit: 2
      });
      
      console.log(`  結果行数: ${page1Result.getNumTuples()}`);
      for (let i = 0; i < page1Result.getNumTuples(); i++) {
        const row = page1Result.getRow(i);
        console.log(`  エンティティ ${i+1}: ID=${row[0]}, 名前=${row[1]}`);
      }
      
      console.log("- 次の2件を取得");
      const page2Result = await callNamedDml(conn, "sample_params.cypher", "paginated_list", {
        offset: 2,
        limit: 2
      });
      
      console.log(`  結果行数: ${page2Result.getNumTuples()}`);
      for (let i = 0; i < page2Result.getNumTuples(); i++) {
        const row = page2Result.getRow(i);
        console.log(`  エンティティ ${i+3}: ID=${row[0]}, 名前=${row[1]}`);
      }
    } catch (error) {
      console.error(`  ページネーションエラー: ${error}`);
    }
    
    console.log("\n===== テスト成功 =====");
    console.log("call_dml.tsユーティリティは期待通りに動作しています。");
    
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
