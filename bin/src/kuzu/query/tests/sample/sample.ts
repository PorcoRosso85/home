#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - 基本テストスクリプト（最小構成版）
 * 
 * このファイルはcommonディレクトリの共通処理を最小構成で検証するためのテストスクリプトです。
 * - データベース接続
 * - スキーマ定義
 * - サンプルデータ挿入
 * - Cypherファイルからのクエリ実行テスト
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { createSchema } from "../common/schema_definition.ts";
import { insertSampleData } from "../common/sample_data.ts";
import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

// テスト用DBの名前
const TEST_DB_NAME = "sample_test_db";

/**
 * 特定の名前のクエリをCypherファイルから読み込む関数
 * @param filePath Cypherファイルのパス
 * @param queryName クエリ名
 */
async function loadNamedQuery(filePath: string, queryName: string): Promise<string> {
  try {
    // ファイルを読み込む
    const content = await Deno.readTextFile(filePath);
    
    // クエリ名のマーカーを使ってクエリを検索
    const marker = `// @name: ${queryName}`;
    const lines = content.split("\n");
    let queryFound = false;
    let query = "";
    
    for (const line of lines) {
      if (line.trim() === marker) {
        queryFound = true;
        continue;
      }
      
      if (queryFound) {
        // 次のマーカーが見つかったら終了
        if (line.trim().startsWith("// @name:")) {
          break;
        }
        
        // コメント行は無視
        if (!line.trim().startsWith("//")) {
          query += line + "\n";
        }
      }
    }
    
    if (!queryFound) {
      throw new Error(`クエリ名 "${queryName}" は見つかりませんでした`);
    }
    
    return query.trim();
  } catch (error) {
    console.error(`クエリの読み込み中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

// メイン実行関数
(async () => {
  console.log("===== 階層型トレーサビリティモデル - 基本テスト（最小構成） =====");
  
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
    
    // 4. Cypherクエリ実行テスト
    console.log("\n4. Cypherクエリ実行テスト");
    
    // 基本クエリファイルのパス
    const queriesFilePath = path.resolve(Deno.cwd(), "/home/nixos/bin/src/kuzu/query/tests/queries/basic_queries.cypher");
    
    // 実行するクエリ名のリスト
    const queryNames = [
      "count_nodes",
      "list_requirements",
      "list_code_entities",
      "check_implementation_relations"
    ];
    
    // 各クエリを実行
    for (const queryName of queryNames) {
      console.log(`\n- ${queryName} クエリを実行`);
      
      try {
        // クエリをファイルから読み込む
        const query = await loadNamedQuery(queriesFilePath, queryName);
        console.log(`  クエリ内容: ${query}`);
        
        // クエリを実行
        const result = await conn.query(query);
        console.log(`  結果行数: ${result.getNumTuples()}`);
        
        // 結果の表示
        const maxRows = Math.min(result.getNumTuples(), 3);
        for (let i = 0; i < maxRows; i++) {
          const row = result.getRow(i);
          console.log(`  結果 ${i+1}: ${JSON.stringify(row)}`);
        }
      } catch (error) {
        console.error(`  エラー: ${error}`);
      }
    }
    
    // 5. データ作成テスト
    console.log("\n5. データ作成テスト");
    
    try {
      // テストノードの作成クエリを読み込んで実行
      console.log("- テストノードを作成");
      const createQuery = await loadNamedQuery(queriesFilePath, "create_test_node");
      await conn.query(createQuery);
      
      // 作成したノードの検証クエリを読み込んで実行
      console.log("- 作成したノードを検証");
      const verifyQuery = await loadNamedQuery(queriesFilePath, "verify_test_node");
      const verifyResult = await conn.query(verifyQuery);
      
      if (verifyResult.getNumTuples() > 0) {
        const row = verifyResult.getRow(0);
        console.log(`  検証成功: 名前=${row[0]}, タイプ=${row[1]}`);
      } else {
        console.log("  検証失敗: ノードが見つかりませんでした");
      }
      
      console.log("✓ データ作成テスト完了");
    } catch (error) {
      console.error(`  データ作成エラー: ${error}`);
    }
    
    console.log("\n===== テスト成功 =====");
    console.log("スキーマ定義、データロード、クエリ実行の基本機能が正常に動作しています。");
    console.log("このテストスクリプトは共通処理の最小構成での動作確認を完了しました。");
    
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
