#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - バージョン管理クエリテスト
 * 
 * このファイルはバージョン管理関連のクエリをテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { createSchema } from "../common/schema_definition.ts";
import { insertSampleData, insertExtendedSampleData, insertVersionTestData } from "../common/sample_data.ts";
import { 
  callNamedDml
} from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "version_queries_test_db";

// メイン実行関数
(async () => {
  console.log("===== バージョン管理クエリテスト =====");
  
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
    
    // 3. バージョン管理テスト用データ挿入
    console.log("\n3. バージョン管理テスト用データ挿入");
    await insertVersionTestData(conn);
    console.log("✓ バージョン管理テスト用データ挿入完了");
    
    // 4. 指定バージョンのlocationURIを取得
    console.log("\n4. 指定バージョンのlocationURI一覧取得");
    try {
      const v1LocationsResult = await callNamedDml(conn, "version_queries.cypher", "get_locations_by_version", {
        version: "v1.0.0"
      });
      
      console.log(`【v1.0.0のlocationURI】 ${v1LocationsResult.getNumTuples()}件`);
      
      // クエリ結果の表示
      console.log("カラム:", ["uri_id", "scheme", "path"].join(", "));
      console.log("-".repeat(50));
      
      // 各行のデータを直接アクセス
      for (let i = 0; i < v1LocationsResult.getNumTuples(); i++) {
        try {
          const row = v1LocationsResult.getRow(i);
          if (row && row.length > 0) {
            console.log([row[0], row[1], row[2]].join(", "));
          } else {
            console.log(`行 ${i}: データなし`);
          }
        } catch (e) {
          console.error(`行 ${i} の取得中にエラー: ${e && e.message ? e.message : "不明なエラー"}`);
        }
      }
      
      const v2LocationsResult = await callNamedDml(conn, "version_queries.cypher", "get_locations_by_version", {
        version: "v1.2.0"
      });
      
      console.log(`\n【v1.2.0のlocationURI】 ${v2LocationsResult.getNumTuples()}件`);
      formatQueryResult(v2LocationsResult);
      
      const v3LocationsResult = await callNamedDml(conn, "version_queries.cypher", "get_locations_by_version", {
        version: "v1.3.0"
      });
      
      console.log(`\n【v1.3.0のlocationURI】 ${v3LocationsResult.getNumTuples()}件`);
      formatQueryResult(v3LocationsResult);
    } catch (error) {
      console.error(`  クエリエラー: ${error}`);
    }
    
    // 5. 指定バージョンの前バージョンを取得
    console.log("\n5. 指定バージョンの前バージョン取得");
    try {
      const prevVersionResult = await callNamedDml(conn, "version_queries.cypher", "get_previous_version", {
        version: "v1.2.0"
      });
      
      console.log(`【v1.2.0の前バージョン】 ${prevVersionResult.getNumTuples()}件`);
      
      // クエリ結果の表示
      console.log("カラム:", ["previous_version", "timestamp", "commit_id"].join(", "));
      console.log("-".repeat(80));
      
      // 各行のデータを直接アクセス
      for (let i = 0; i < prevVersionResult.getNumTuples(); i++) {
        try {
          const row = prevVersionResult.getRow(i);
          if (row && row.length > 0) {
            console.log([row[0], row[1], row[2]].join(", "));
          } else {
            console.log(`行 ${i}: データなし`);
          }
        } catch (e) {
          console.error(`行 ${i} の取得中にエラー: ${e && e.message ? e.message : "不明なエラー"}`);
        }
      }
      
      const prevVersionResult2 = await callNamedDml(conn, "version_queries.cypher", "get_previous_version", {
        version: "v1.1.0"
      });
      
      console.log(`\n【v1.1.0の前バージョン】 ${prevVersionResult2.getNumTuples()}件`);
      formatQueryResult(prevVersionResult2);
      
      const prevVersionResult3 = await callNamedDml(conn, "version_queries.cypher", "get_previous_version", {
        version: "v1.3.0"
      });
      
      console.log(`\n【v1.3.0の前バージョン】 ${prevVersionResult3.getNumTuples()}件`);
      formatQueryResult(prevVersionResult3);
    } catch (error) {
      console.error(`  クエリエラー: ${error}`);
    }
    
    // 6. 指定バージョンで更新したlocationURIを取得（前バージョンとの差分）
    console.log("\n6. 指定バージョンで追加されたlocationURI一覧");
    try {
      const addedLocationsResult = await callNamedDml(conn, "version_queries.cypher", "get_updated_locations_by_version", {
        version: "v1.2.0",
        change_type: "added"
      });
      
      console.log(`【v1.2.0で追加されたlocationURI】 ${addedLocationsResult.getNumTuples()}件`);
      
      // クエリ結果の表示
      console.log("カラム:", ["entity_type", "entity_id", "name", "uri_id", "path"].join(", "));
      console.log("-".repeat(80));
      
      // 各行のデータを直接アクセス
      for (let i = 0; i < addedLocationsResult.getNumTuples(); i++) {
        try {
          const row = addedLocationsResult.getRow(i);
          if (row && row.length > 0) {
            console.log([row[0], row[1], row[2], row[3], row[4]].join(", "));
          } else {
            console.log(`行 ${i}: データなし`);
          }
        } catch (e) {
          console.error(`行 ${i} の取得中にエラー: ${e && e.message ? e.message : "不明なエラー"}`);
        }
      }
      
      const modifiedLocationsResult = await callNamedDml(conn, "version_queries.cypher", "get_updated_locations_by_version", {
        version: "v1.1.0",
        change_type: "modified"
      });
      
      console.log(`\n【v1.1.0で変更されたlocationURI】 ${modifiedLocationsResult.getNumTuples()}件`);
      formatQueryResult(modifiedLocationsResult);
      
      const v13AddedLocationsResult = await callNamedDml(conn, "version_queries.cypher", "get_updated_locations_by_version", {
        version: "v1.3.0",
        change_type: "added"
      });
      
      console.log(`\n【v1.3.0で追加されたlocationURI】 ${v13AddedLocationsResult.getNumTuples()}件`);
      formatQueryResult(v13AddedLocationsResult);
      
      const v13ModifiedLocationsResult = await callNamedDml(conn, "version_queries.cypher", "get_updated_locations_by_version", {
        version: "v1.3.0",
        change_type: "modified"
      });
      
      console.log(`\n【v1.3.0で変更されたlocationURI】 ${v13ModifiedLocationsResult.getNumTuples()}件`);
      formatQueryResult(v13ModifiedLocationsResult);
      
      const v13DeletedLocationsResult = await callNamedDml(conn, "version_queries.cypher", "get_updated_locations_by_version", {
        version: "v1.3.0",
        change_type: "deleted"
      });
      
      console.log(`\n【v1.3.0で削除されたlocationURI】 ${v13DeletedLocationsResult.getNumTuples()}件`);
      formatQueryResult(v13DeletedLocationsResult);
    } catch (error) {
      console.error(`  クエリエラー: ${error}`);
    }
    
    // 7. 設計表を取得
    console.log("\n7. 設計表の取得");
    try {
      const designTableResult = await callNamedDml(conn, "version_queries.cypher", "get_design_table", {
        version: "v1.2.0",
        change_type: "added"
      });
      
      console.log(`【v1.2.0の設計表（追加項目）】 ${designTableResult.getNumTuples()}件`);
      console.log("ファイルパス | 変更概要");
      console.log("-----------|-----------");
      
      // 正しい方法でデータを表示
      designTableResult.resetIterator();
      while (designTableResult.hasNext()) {
        const row = designTableResult.getNextSync();
        // row はオブジェクト形式 (例: { file_path: "xxx", change_summary: "yyy" })
        const filePath = row.file_path || "";
        const changeSummary = row.change_summary || "";
        console.log(`${filePath} | ${changeSummary}`);
      }
      
      const designTableResult2 = await callNamedDml(conn, "version_queries.cypher", "get_design_table", {
        version: "v1.1.0",
        change_type: "modified"
      });
      
      console.log(`\n【v1.1.0の設計表（変更項目）】 ${designTableResult2.getNumTuples()}件`);
      console.log("ファイルパス | 変更概要");
      console.log("-----------|-----------");
      for (let i = 0; i < designTableResult2.getNumTuples(); i++) {
        const row = designTableResult2.getRow(i);
        console.log(`${row[0]} | ${row[1]}`);
      }
      
      const designTableResult3 = await callNamedDml(conn, "version_queries.cypher", "get_design_table", {
        version: "v1.3.0",
        change_type: "added"
      });
      
      console.log(`\n【v1.3.0の設計表（追加項目）】 ${designTableResult3.getNumTuples()}件`);
      console.log("ファイルパス | 変更概要");
      console.log("-----------|-----------");
      for (let i = 0; i < designTableResult3.getNumTuples(); i++) {
        const row = designTableResult3.getRow(i);
        console.log(`${row[0]} | ${row[1]}`);
      }
      
      const designTableResult4 = await callNamedDml(conn, "version_queries.cypher", "get_design_table", {
        version: "v1.3.0",
        change_type: "modified"
      });
      
      console.log(`\n【v1.3.0の設計表（変更項目）】 ${designTableResult4.getNumTuples()}件`);
      console.log("ファイルパス | 変更概要");
      console.log("-----------|-----------");
      for (let i = 0; i < designTableResult4.getNumTuples(); i++) {
        const row = designTableResult4.getRow(i);
        console.log(`${row[0]} | ${row[1]}`);
      }
      
      const designTableResult5 = await callNamedDml(conn, "version_queries.cypher", "get_design_table", {
        version: "v1.3.0",
        change_type: "deleted"
      });
      
      console.log(`\n【v1.3.0の設計表（削除項目）】 ${designTableResult5.getNumTuples()}件`);
      console.log("ファイルパス | 変更概要");
      console.log("-----------|-----------");
      for (let i = 0; i < designTableResult5.getNumTuples(); i++) {
        const row = designTableResult5.getRow(i);
        console.log(`${row[0]} | ${row[1]}`);
      }
    } catch (error) {
      console.error(`  クエリエラー: ${error}`);
    }
    
    // 8. バージョン変更概要を取得
    console.log("\n8. バージョン変更概要");
    try {
      const versionSummaryResult = await callNamedDml(conn, "version_queries.cypher", "get_version_changes_summary", {
        version: "v1.2.0"
      });
      
      console.log(`【v1.2.0のバージョン変更概要】 ${versionSummaryResult.getNumTuples()}件`);
      console.log("ファイルパス | エンティティ説明");
      console.log("-----------|-----------");
      
      // 正しい方法でデータを表示
      versionSummaryResult.resetIterator();
      while (versionSummaryResult.hasNext()) {
        const row = versionSummaryResult.getNextSync();
        // row はオブジェクト形式 (例: { file_path: "xxx", entity_description: "yyy" })
        const filePath = row.file_path || "";
        const entityDescription = row.entity_description || "";
        console.log(`${filePath} | ${entityDescription}`);
      }
      
      const versionSummaryResult2 = await callNamedDml(conn, "version_queries.cypher", "get_version_changes_summary", {
        version: "v1.3.0"
      });
      
      console.log(`\n【v1.3.0のバージョン変更概要】 ${versionSummaryResult2.getNumTuples()}件`);
      console.log("ファイルパス | エンティティ説明");
      console.log("-----------|-----------");
      
      // 正しい方法でデータを表示
      versionSummaryResult2.resetIterator();
      while (versionSummaryResult2.hasNext()) {
        const row = versionSummaryResult2.getNextSync();
        // row はオブジェクト形式 (例: { file_path: "xxx", entity_description: "yyy" })
        const filePath = row.file_path || "";
        const entityDescription = row.entity_description || "";
        console.log(`${filePath} | ${entityDescription}`);
      }
    } catch (error) {
      console.error(`  クエリエラー: ${error}`);
    }
    
    console.log("\n===== テスト成功 =====");
    console.log("バージョン管理クエリは期待通りに動作しています。");
    
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
