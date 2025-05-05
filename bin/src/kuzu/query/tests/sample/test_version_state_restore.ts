/**
 * 階層型トレーサビリティモデル - バージョン状態復元テスト
 * 
 * このファイルは特定バージョン時点での全要件・全コードの状態を復元するための機能をテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "version_state_restore_test_db";

// メイン実行関数
(async () => {
  console.log("===== バージョン状態復元テスト =====");
  
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
    
    // 4. バージョン状態のためのテストデータを作成
    console.log("\n4. バージョン状態のためのテストデータを作成");
    try {
      const createResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "create_version_states", {});
      
      createResult.resetIterator();
      const createRow = createResult.getNextSync();
      console.log(`  バージョン状態テストデータを作成: ${createRow.created_versions}バージョン`);
    } catch (err) {
      console.error(`  バージョン状態テストデータの作成に失敗: ${err}`);
    }
    
    // 5. バージョンの履歴を取得
    console.log("\n5. バージョンの履歴を取得");
    try {
      const historyResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "get_version_history", {});
      
      console.log("  バージョン履歴:");
      console.log("  バージョン | タイムスタンプ | 説明 | 作成者 | コミットID");
      console.log("  ----------|--------------|------|--------|----------");
      
      historyResult.resetIterator();
      while (historyResult.hasNext()) {
        const row = historyResult.getNextSync();
        console.log(`  ${row.version_id} | ${row.timestamp} | ${row.description} | ${row.author} | ${row.commit_id}`);
      }
    } catch (err) {
      console.error(`  バージョンの履歴取得に失敗: ${err}`);
    }
    
    // 6. v1.0.0の状態を復元
    console.log("\n6. v1.0.0（初期バージョン）の状態を復元");
    try {
      // 要件の取得
      const reqResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "get_requirements_at_version", {
        version: 'v1.0.0'
      });
      
      console.log(`  v1.0.0の要件: ${reqResult.getNumTuples()}件`);
      console.log("  要件ID | タイトル | 説明 | 優先度 | タイプ");
      console.log("  -------|----------|------|--------|------");
      
      reqResult.resetIterator();
      while (reqResult.hasNext()) {
        const row = reqResult.getNextSync();
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.requirement_description.substring(0, 30)}... | ${row.requirement_priority} | ${row.requirement_type}`);
      }
      
      // コードの取得
      const codeResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "get_code_at_version", {
        version: 'v1.0.0'
      });
      
      console.log(`\n  v1.0.0のコード: ${codeResult.getNumTuples()}件`);
      console.log("  コードID | 名前 | タイプ | シグネチャ | 複雑度");
      console.log("  ---------|------|--------|-----------|-------");
      
      codeResult.resetIterator();
      while (codeResult.hasNext()) {
        const row = codeResult.getNextSync();
        console.log(`  ${row.code_id} | ${row.code_name} | ${row.code_type} | ${row.code_signature} | ${row.code_complexity}`);
      }
      
      // 関連の取得
      const relResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "get_relationships_at_version", {
        version: 'v1.0.0'
      });
      
      console.log(`\n  v1.0.0の実装関係: ${relResult.getNumTuples()}件`);
      console.log("  要件ID | 要件タイトル | コードID | コード名 | 実装タイプ");
      console.log("  -------|-------------|----------|----------|------------");
      
      relResult.resetIterator();
      while (relResult.hasNext()) {
        const row = relResult.getNextSync();
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.code_id} | ${row.code_name} | ${row.implementation_type}`);
      }
    } catch (err) {
      console.error(`  v1.0.0の状態復元に失敗: ${err}`);
    }
    
    // 7. v1.0.0とv1.1.0の要件を比較
    console.log("\n7. v1.0.0とv1.1.0の要件を比較");
    try {
      const compareResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "compare_requirements_between_versions", {
        version1: 'v1.0.0',
        version2: 'v1.1.0'
      });
      
      console.log(`  変更された要件: ${compareResult.getNumTuples()}件`);
      
      compareResult.resetIterator();
      while (compareResult.hasNext()) {
        const row = compareResult.getNextSync();
        console.log(`  要件ID: ${row.requirement_id}`);
        console.log(`  タイトル: ${row.old_title} -> ${row.new_title}`);
        console.log(`  説明: ${row.old_description} -> ${row.new_description}`);
        console.log(`  優先度: ${row.old_priority} -> ${row.new_priority}`);
        console.log(`  タイプ: ${row.old_type} -> ${row.new_type}`);
        console.log("  ---");
      }
    } catch (err) {
      console.error(`  要件の比較に失敗: ${err}`);
    }
    
    // 8. v1.1.0で追加された要件を取得
    console.log("\n8. v1.1.0で追加された要件を取得");
    try {
      const addedResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "get_added_requirements", {
        older: 'v1.0.0',
        newer: 'v1.1.0'
      });
      
      console.log(`  追加された要件: ${addedResult.getNumTuples()}件`);
      console.log("  要件ID | タイトル | 説明 | 優先度 | タイプ");
      console.log("  -------|----------|------|--------|------");
      
      addedResult.resetIterator();
      while (addedResult.hasNext()) {
        const row = addedResult.getNextSync();
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.requirement_description.substring(0, 30)}... | ${row.requirement_priority} | ${row.requirement_type}`);
      }
    } catch (err) {
      console.error(`  追加された要件の取得に失敗: ${err}`);
    }
    
    // 9. v1.1.0で追加されたコードを取得
    console.log("\n9. v1.1.0で追加されたコードを取得");
    try {
      const addedCodeResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "get_added_code", {
        older: 'v1.0.0',
        newer: 'v1.1.0'
      });
      
      console.log(`  追加されたコード: ${addedCodeResult.getNumTuples()}件`);
      console.log("  コードID | 名前 | タイプ | シグネチャ | 複雑度");
      console.log("  ---------|------|--------|-----------|-------");
      
      addedCodeResult.resetIterator();
      while (addedCodeResult.hasNext()) {
        const row = addedCodeResult.getNextSync();
        console.log(`  ${row.code_id} | ${row.code_name} | ${row.code_type} | ${row.code_signature} | ${row.code_complexity}`);
      }
    } catch (err) {
      console.error(`  追加されたコードの取得に失敗: ${err}`);
    }
    
    // 10. v1.1.0とv1.2.0の間で削除された要件を取得
    console.log("\n10. v1.1.0とv1.2.0の間で削除された要件を取得");
    try {
      const deletedResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "get_deleted_requirements", {
        older: 'v1.1.0',
        newer: 'v1.2.0'
      });
      
      console.log(`  削除された要件: ${deletedResult.getNumTuples()}件`);
      console.log("  要件ID | タイトル | 説明 | 優先度 | タイプ");
      console.log("  -------|----------|------|--------|------");
      
      deletedResult.resetIterator();
      while (deletedResult.hasNext()) {
        const row = deletedResult.getNextSync();
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.requirement_description.substring(0, 30)}... | ${row.requirement_priority} | ${row.requirement_type}`);
      }
    } catch (err) {
      console.error(`  削除された要件の取得に失敗: ${err}`);
    }
    
    // 11. v1.2.0（最新バージョン）の完全な状態スナップショットを取得
    console.log("\n11. v1.2.0（最新バージョン）の完全な状態スナップショットを取得");
    try {
      const snapshotResult = await callNamedDml(conn, "version_state_restore_queries.cypher", "get_complete_state_snapshot", {
        version: 'v1.2.0'
      });
      
      snapshotResult.resetIterator();
      const snapshotRow = snapshotResult.getNextSync();
      
      console.log(`  バージョン: ${snapshotRow.version_id} (${snapshotRow.timestamp})`);
      console.log(`  説明: ${snapshotRow.description}`);
      console.log(`  要件数: ${snapshotRow.requirements_count}件`);
      console.log(`  コード数: ${snapshotRow.code_count}件`);
      console.log(`  実装関係数: ${snapshotRow.implementation_relationships_count}件`);
      
      // 要件の詳細表示
      console.log("\n  要件一覧:");
      
      if (snapshotRow.requirements && snapshotRow.requirements.length > 0) {
        snapshotRow.requirements.forEach((req: any, index: number) => {
          console.log(`  ${index + 1}. ${req.id}: ${req.title} (${req.priority})`);
        });
      } else {
        console.log("  (要件なし)");
      }
      
      // コードの詳細表示
      console.log("\n  コード一覧:");
      
      if (snapshotRow.code_entities && snapshotRow.code_entities.length > 0) {
        snapshotRow.code_entities.forEach((code: any, index: number) => {
          console.log(`  ${index + 1}. ${code.persistent_id}: ${code.name} (複雑度:${code.complexity})`);
        });
      } else {
        console.log("  (コードなし)");
      }
      
      // 実装関係の詳細表示
      console.log("\n  実装関係:");
      
      if (snapshotRow.implementations && snapshotRow.implementations.length > 0) {
        snapshotRow.implementations.forEach((impl: any, index: number) => {
          console.log(`  ${index + 1}. ${impl.requirement_id} -> ${impl.code_id} (${impl.type})`);
        });
      } else {
        console.log("  (実装関係なし)");
      }
    } catch (err) {
      console.error(`  完全な状態スナップショットの取得に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("特定バージョン時点での全要件・全コードの状態復元テストが完了しました。");
    
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