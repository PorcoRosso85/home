/**
 * 階層型トレーサビリティモデル - 外部参照との関係性テスト
 * 
 * このファイルは外部APIや依存ライブラリとの関係を明確にし、外部変更の影響を把握できることをテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "external_reference_test_db";

// メイン実行関数
(async () => {
  console.log("===== 外部参照との関係性テスト =====");
  
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
    
    // 4. 外部参照の作成
    console.log("\n4. 外部参照の作成");
    try {
      const createResult = await callNamedDml(conn, "external_reference_queries.cypher", "create_external_references", {});
      
      createResult.resetIterator();
      const createRow = createResult.getNextSync();
      console.log(`  外部参照を作成: ${createRow.created_references}件`);
    } catch (err) {
      console.error(`  外部参照の作成に失敗: ${err}`);
    }
    
    // 5. 外部参照と要件・コードの関連付け
    console.log("\n5. 外部参照と要件・コードの関連付け");
    try {
      const dependenciesResult = await callNamedDml(conn, "external_reference_queries.cypher", "create_requirements_and_dependencies", {});
      
      dependenciesResult.resetIterator();
      const depRow = dependenciesResult.getNextSync();
      console.log(`  関連付けを作成: 要件=${depRow.created_requirements}件, コード=${depRow.created_code}件`);
    } catch (err) {
      console.error(`  外部参照と要件・コードの関連付けに失敗: ${err}`);
    }
    
    // 6. 外部参照の一覧取得
    console.log("\n6. 外部参照の一覧取得");
    try {
      const listResult = await callNamedDml(conn, "external_reference_queries.cypher", "list_external_references", {
        types: ['external_api', 'external_library', 'framework']
      });
      
      console.log("  外部参照一覧:");
      listResult.resetIterator();
      while (listResult.hasNext()) {
        const row = listResult.getNextSync();
        console.log(`  ${row.reference_id} | ${row.reference_name} | タイプ: ${row.reference_type} | バージョン: ${row.reference_version}`);
        console.log(`  説明: ${row.reference_description}`);
        console.log(`  URL: ${row.reference_url}`);
        console.log("  ---");
      }
    } catch (err) {
      console.error(`  外部参照の一覧取得に失敗: ${err}`);
    }
    
    // 7. 要件から外部参照への依存関係を追跡
    console.log("\n7. 要件から外部参照への依存関係を追跡");
    try {
      const traceReqResult = await callNamedDml(conn, "external_reference_queries.cypher", "trace_requirements_to_external", {});
      
      console.log("  要件から外部参照への依存関係:");
      console.log("  要件ID | 要件タイトル | 外部参照ID | 外部参照名 | タイプ | バージョン");
      console.log("  -------|-------------|------------|------------|--------|----------");
      
      traceReqResult.resetIterator();
      while (traceReqResult.hasNext()) {
        const row = traceReqResult.getNextSync();
        console.log(`  ${row.requirement_id} | ${row.requirement_title} | ${row.reference_id} | ${row.reference_name} | ${row.reference_type} | ${row.reference_version}`);
      }
    } catch (err) {
      console.error(`  要件から外部参照への依存関係の追跡に失敗: ${err}`);
    }
    
    // 8. コードから外部参照への依存関係を追跡
    console.log("\n8. コードから外部参照への依存関係を追跡");
    try {
      const traceCodeResult = await callNamedDml(conn, "external_reference_queries.cypher", "trace_code_to_external", {});
      
      console.log("  コードから外部参照への依存関係:");
      console.log("  コードID | コード名 | 依存タイプ | 外部参照ID | 外部参照名 | タイプ | バージョン");
      console.log("  ---------|----------|------------|------------|------------|--------|----------");
      
      traceCodeResult.resetIterator();
      while (traceCodeResult.hasNext()) {
        const row = traceCodeResult.getNextSync();
        console.log(`  ${row.code_id} | ${row.code_name} | ${row.dependency_type} | ${row.reference_id} | ${row.reference_name} | ${row.reference_type} | ${row.reference_version}`);
      }
    } catch (err) {
      console.error(`  コードから外部参照への依存関係の追跡に失敗: ${err}`);
    }
    
    // 9. 特定の外部参照に依存するすべての要件とコードを取得
    console.log("\n9. 特定の外部参照に依存するすべての要件とコードを取得");
    try {
      const dependenciesResult = await callNamedDml(conn, "external_reference_queries.cypher", "get_dependencies_for_reference", {
        referenceId: 'EXT-API-001'  // Payment Gateway API
      });
      
      dependenciesResult.resetIterator();
      const depRow = dependenciesResult.getNextSync();
      
      console.log(`  外部参照「${depRow.reference_name} (${depRow.reference_id})」への依存関係:`);
      
      console.log("\n  依存する要件:");
      if (depRow.requirements && depRow.requirements.length > 0) {
        depRow.requirements.forEach((req: any, index: number) => {
          console.log(`    ${index + 1}. ${req.title || req.id} (${req.id}) - 依存タイプ: ${req.dependency_type || '不明'}`);
        });
      } else {
        console.log("    (依存する要件はありません)");
      }
      
      console.log("\n  依存するコード:");
      if (depRow.code_entities && depRow.code_entities.length > 0) {
        depRow.code_entities.forEach((code: any, index: number) => {
          console.log(`    ${index + 1}. ${code.name || code.id} (${code.id}) - 依存タイプ: ${code.dependency_type || '不明'}`);
        });
      } else {
        console.log("    (依存するコードはありません)");
      }
    } catch (err) {
      console.error(`  特定の外部参照に依存するすべての要件とコードの取得に失敗: ${err}`);
    }
    
    // 10. 外部参照の更新をシミュレート
    console.log("\n10. 外部参照の更新をシミュレート");
    try {
      const updateResult = await callNamedDml(conn, "external_reference_queries.cypher", "simulate_reference_update", {
        referenceId: 'EXT-API-001',
        newVersion: '3.0',
        updateDate: '2024-05-01'
      });
      
      updateResult.resetIterator();
      const updateRow = updateResult.getNextSync();
      console.log(`  外部参照「${updateRow["ref.name"]} (${updateRow["ref.id"]})」をバージョン ${updateRow["ref.version"]} に更新しました`);
      console.log(`  更新日: ${updateRow["ref.update_date"]}`);
    } catch (err) {
      console.error(`  外部参照の更新シミュレーションに失敗: ${err}`);
    }
    
    // 11. 外部参照の更新による影響範囲分析
    console.log("\n11. 外部参照の更新による影響範囲分析");
    try {
      const impactResult = await callNamedDml(conn, "external_reference_queries.cypher", "analyze_update_impact", {
        referenceId: 'EXT-API-001'
      });
      
      impactResult.resetIterator();
      const impactRow = impactResult.getNextSync();
      
      console.log(`  外部参照「${impactRow.reference_name} (${impactRow.reference_version})」の更新による影響範囲:`);
      console.log(`  影響を受ける要件数: ${impactRow.affected_requirements_count}件`);
      console.log(`  影響を受ける要件: ${impactRow.affected_requirements.join(', ') || '(なし)'}`);
      console.log(`  直接影響を受けるコード数: ${impactRow.affected_code_count}件`);
      console.log(`  直接影響を受けるコード: ${impactRow.affected_code.join(', ') || '(なし)'}`);
      console.log(`  間接的に影響を受けるコード数: ${impactRow.indirectly_affected_code_count}件`);
      console.log(`  間接的に影響を受けるコード: ${impactRow.indirectly_affected_code.join(', ') || '(なし)'}`);
    } catch (err) {
      console.error(`  外部参照の更新による影響範囲分析に失敗: ${err}`);
    }
    
    // 12. 外部参照の廃止をシミュレート
    console.log("\n12. 外部参照の廃止をシミュレート");
    try {
      const deprecationResult = await callNamedDml(conn, "external_reference_queries.cypher", "simulate_reference_deprecation", {
        referenceId: 'EXT-API-001',
        deprecationDate: '2024-12-31',
        replacementId: 'EXT-API-NEW-001'
      });
      
      deprecationResult.resetIterator();
      const depRow = deprecationResult.getNextSync();
      console.log(`  外部参照「${depRow["ref.name"]} (${depRow["ref.id"]})」を廃止としてマーク`);
      console.log(`  廃止予定日: ${depRow["ref.deprecation_date"]}`);
      console.log(`  代替参照ID: ${depRow["ref.replacement_id"]}`);
    } catch (err) {
      console.error(`  外部参照の廃止シミュレーションに失敗: ${err}`);
    }
    
    // 13. 代替の外部参照を作成
    console.log("\n13. 代替の外部参照を作成");
    try {
      const replacementResult = await callNamedDml(conn, "external_reference_queries.cypher", "create_replacement_reference", {
        newReferenceId: 'EXT-API-NEW-001',
        newReferenceName: 'Payment Gateway API (New)',
        newReferenceDescription: '次世代決済処理用の外部API',
        referenceType: 'external_api',
        version: '1.0',
        url: 'https://api-next.payment-gateway.example.com/v1',
        oldReferenceId: 'EXT-API-001'
      });
      
      replacementResult.resetIterator();
      const replRow = replacementResult.getNextSync();
      console.log(`  代替の外部参照「${replRow["newRef.name"]} (${replRow["newRef.id"]})」を作成`);
      console.log(`  バージョン: ${replRow["newRef.version"]}`);
    } catch (err) {
      console.error(`  代替の外部参照の作成に失敗: ${err}`);
    }
    
    // 14. 外部参照の移行計画を作成
    console.log("\n14. 外部参照の移行計画を作成");
    try {
      const planResult = await callNamedDml(conn, "external_reference_queries.cypher", "create_migration_plan", {
        oldReferenceId: 'EXT-API-001',
        newReferenceId: 'EXT-API-NEW-001'
      });
      
      planResult.resetIterator();
      const planRow = planResult.getNextSync();
      
      console.log(`  移行計画: ${planRow.old_reference_name} (${planRow.old_reference_version}) -> ${planRow.new_reference_name} (${planRow.new_reference_version})`);
      
      console.log("\n  移行が必要な要件:");
      if (planRow.requirements_to_migrate && planRow.requirements_to_migrate.length > 0) {
        planRow.requirements_to_migrate.forEach((req: any, index: number) => {
          console.log(`    ${index + 1}. ${req.title || req.id} (${req.id}) - 依存タイプ: ${req.dependency_type || '不明'}`);
        });
      } else {
        console.log("    (移行が必要な要件はありません)");
      }
      
      console.log("\n  移行が必要なコード:");
      if (planRow.code_to_migrate && planRow.code_to_migrate.length > 0) {
        planRow.code_to_migrate.forEach((code: any, index: number) => {
          console.log(`    ${index + 1}. ${code.name || code.id} (${code.id}) - 依存タイプ: ${code.dependency_type || '不明'}`);
        });
      } else {
        console.log("    (移行が必要なコードはありません)");
      }
    } catch (err) {
      console.error(`  外部参照の移行計画の作成に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("外部参照との関係性の管理テストが完了しました。");
    
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