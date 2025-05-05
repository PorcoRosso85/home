/**
 * 階層型トレーサビリティモデル - 実装トレーサビリティテスト
 * 
 * このファイルは要件からコード実装への双方向トレーサビリティをテストします。
 */

import { 
  setupDatabase, 
  closeDatabase 
} from "../common/db_connection.ts";
import { callDdl } from "../call_ddl.ts";
import { callDml, callNamedDml } from "../call_dml.ts";
import { formatQueryResult } from "../common/result_formatter.ts";

// テスト用DBの名前
const TEST_DB_NAME = "implementation_traceability_test_db";

// メイン実行関数
(async () => {
  console.log("===== 実装トレーサビリティテスト =====");
  
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
    console.log("要件とコードの初期状態:");
    try {
      const requirementsResult = await callNamedDml(conn, "basic_queries.cypher", "list_requirements", {});
      const codeEntitiesResult = await callNamedDml(conn, "basic_queries.cypher", "list_code_entities", {});
      const implementationRelationsResult = await callNamedDml(conn, "basic_queries.cypher", "check_implementation_relations", {});
      
      console.log("\n  要件一覧:");
      requirementsResult.resetIterator();
      let reqCount = 1;
      while (requirementsResult.hasNext()) {
        const row = requirementsResult.getNextSync();
        console.log(`    ${reqCount}. ${row["r.title"]} (${row["r.id"]})`);
        reqCount++;
      }
      
      console.log("\n  コードエンティティ一覧:");
      codeEntitiesResult.resetIterator();
      let codeCount = 1;
      while (codeEntitiesResult.hasNext()) {
        const row = codeEntitiesResult.getNextSync();
        console.log(`    ${codeCount}. ${row["c.name"]} (${row["c.persistent_id"]})`);
        codeCount++;
      }
      
      console.log("\n  実装関係一覧:");
      implementationRelationsResult.resetIterator();
      let implCount = 1;
      while (implementationRelationsResult.hasNext()) {
        const row = implementationRelationsResult.getNextSync();
        console.log(`    ${implCount}. 要件 ${row["r.id"]} -> コード ${row["c.persistent_id"]}`);
        implCount++;
      }
    } catch (err) {
      console.error(`  初期状態の確認に失敗: ${err}`);
    }
    
    // 5. 実装トレーサビリティテスト（要件からコード）
    console.log("\n5. 実装トレーサビリティテスト（要件からコード）");
    try {
      // 新しい要件とコードを作成して関連付ける
      const createReqAndCodeQuery = `
        // 新しい要件を作成
        CREATE (r:RequirementEntity {
          id: 'REQ-IMPL-001',
          title: 'データエクスポート機能',
          description: 'ユーザーはデータをCSV形式でエクスポートできること',
          priority: 'medium',
          requirement_type: 'functional'
        })
        
        // 新しいコードエンティティを作成
        CREATE (c1:CodeEntity {
          persistent_id: 'CODE-EXPORT-001',
          name: 'exportToCSV',
          type: 'function',
          signature: 'public void exportToCSV(Data data, String filename)',
          complexity: 3,
          start_position: 200,
          end_position: 300
        })
        
        CREATE (c2:CodeEntity {
          persistent_id: 'CODE-EXPORT-002',
          name: 'CSVFormatter',
          type: 'class',
          signature: 'public class CSVFormatter',
          complexity: 5,
          start_position: 400,
          end_position: 800
        })
        
        // 要件からコードへの実装関係を作成
        CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(c1)
        CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'support'}]->(c2)
        
        RETURN r.id, c1.persistent_id, c2.persistent_id;
      `;
      const createResult = await conn.query(createReqAndCodeQuery);
      
      createResult.resetIterator();
      const createRow = createResult.getNextSync();
      console.log(`  要件「${createRow["r.id"]}」をコード「${createRow["c1.persistent_id"]}」と「${createRow["c2.persistent_id"]}」に関連付けました`);
      
      // 要件からコードを取得するクエリ
      const reqToCodeQuery = `
        MATCH (r:RequirementEntity {id: 'REQ-IMPL-001'})-[rel:IS_IMPLEMENTED_BY]->(c:CodeEntity)
        RETURN r.id, r.title, c.persistent_id, c.name, rel.implementation_type;
      `;
      const reqToCodeResult = await conn.query(reqToCodeQuery);
      
      console.log("\n  要件からのコード実装トレーサビリティ:");
      reqToCodeResult.resetIterator();
      while (reqToCodeResult.hasNext()) {
        const row = reqToCodeResult.getNextSync();
        console.log(`    要件: ${row["r.title"]} (${row["r.id"]}) -> コード: ${row["c.name"]} (${row["c.persistent_id"]}) - 実装タイプ: ${row["rel.implementation_type"]}`);
      }
    } catch (err) {
      console.error(`  実装トレーサビリティテスト（要件からコード）に失敗: ${err}`);
    }
    
    // 6. 実装トレーサビリティテスト（コードから要件）
    console.log("\n6. 実装トレーサビリティテスト（コードから要件）");
    try {
      // コードから要件を取得するクエリ
      const codeToReqQuery = `
        MATCH (c:CodeEntity {persistent_id: 'CODE-EXPORT-001'})<-[rel:IS_IMPLEMENTED_BY]-(r:RequirementEntity)
        RETURN c.persistent_id, c.name, r.id, r.title, rel.implementation_type;
      `;
      const codeToReqResult = await conn.query(codeToReqQuery);
      
      console.log("\n  コードからの要件トレーサビリティ:");
      codeToReqResult.resetIterator();
      while (codeToReqResult.hasNext()) {
        const row = codeToReqResult.getNextSync();
        console.log(`    コード: ${row["c.name"]} (${row["c.persistent_id"]}) <- 要件: ${row["r.title"]} (${row["r.id"]}) - 実装タイプ: ${row["rel.implementation_type"]}`);
      }
    } catch (err) {
      console.error(`  実装トレーサビリティテスト（コードから要件）に失敗: ${err}`);
    }
    
    // 7. 未実装の要件を検出
    console.log("\n7. 未実装の要件を検出");
    try {
      // 追加の未実装要件を作成
      const createUnimplementedReqQuery = `
        CREATE (r:RequirementEntity {
          id: 'REQ-UNIMPLEMENTED',
          title: '未実装の要件',
          description: 'これはまだ実装されていない要件です',
          priority: 'high',
          requirement_type: 'functional'
        })
        RETURN r.id, r.title;
      `;
      const createUnimplementedResult = await conn.query(createUnimplementedReqQuery);
      
      createUnimplementedResult.resetIterator();
      const unimplementedRow = createUnimplementedResult.getNextSync();
      console.log(`  未実装の要件を作成: ${unimplementedRow["r.title"]} (${unimplementedRow["r.id"]})`);
      
      // 未実装の要件を検出するクエリ
      const unimplementedReqQuery = `
        MATCH (r:RequirementEntity)
        WHERE NOT EXISTS { MATCH (r)-[:IS_IMPLEMENTED_BY]->() }
        RETURN r.id, r.title, r.priority;
      `;
      const unimplementedReqResult = await conn.query(unimplementedReqQuery);
      
      console.log("\n  未実装の要件一覧:");
      unimplementedReqResult.resetIterator();
      let count = 1;
      while (unimplementedReqResult.hasNext()) {
        const row = unimplementedReqResult.getNextSync();
        console.log(`    ${count}. ${row["r.title"]} (${row["r.id"]}) - 優先度: ${row["r.priority"]}`);
        count++;
      }
    } catch (err) {
      console.error(`  未実装の要件の検出に失敗: ${err}`);
    }
    
    // 8. 関連コードが存在しない要件の影響分析
    console.log("\n8. 関連コードが存在しない要件の影響分析");
    try {
      // 関連要件間の依存関係を作成
      const createDependencyQuery = `
        MATCH (req1:RequirementEntity {id: 'REQ-UNIMPLEMENTED'}), (req2:RequirementEntity {id: 'REQ-IMPL-001'})
        CREATE (req1)-[:DEPENDS_ON {dependency_type: 'functional'}]->(req2)
        RETURN req1.id, req2.id;
      `;
      const createDependencyResult = await conn.query(createDependencyQuery);
      
      createDependencyResult.resetIterator();
      const depRow = createDependencyResult.getNextSync();
      console.log(`  依存関係を作成: ${depRow["req1.id"]} -> ${depRow["req2.id"]}`);
      
      // 影響分析クエリ（依存する要件と、その実装コード）
      const impactAnalysisQuery = `
        MATCH (r:RequirementEntity {id: 'REQ-UNIMPLEMENTED'})-[:DEPENDS_ON*1..3]->(dep:RequirementEntity)
        OPTIONAL MATCH (dep)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
        RETURN r.id AS source_req, dep.id AS dependency, 
               collect(DISTINCT c.persistent_id) AS affected_code;
      `;
      const impactAnalysisResult = await conn.query(impactAnalysisQuery);
      
      console.log("\n  影響分析結果:");
      impactAnalysisResult.resetIterator();
      while (impactAnalysisResult.hasNext()) {
        const row = impactAnalysisResult.getNextSync();
        console.log(`    要件 ${row["source_req"]} は ${row["dependency"]} に依存しています`);
        console.log(`    影響を受ける可能性のあるコード: ${row["affected_code"].length > 0 ? row["affected_code"].join(', ') : '(なし)'}`);
      }
    } catch (err) {
      console.error(`  関連コードが存在しない要件の影響分析に失敗: ${err}`);
    }
    
    // 9. コード変更時の要件追跡
    console.log("\n9. コード変更時の要件追跡");
    try {
      // コード変更のシミュレーション（既存コードを修正）
      const updateCodeQuery = `
        MATCH (c:CodeEntity {persistent_id: 'CODE-EXPORT-001'})
        SET c.name = 'exportToCSV_v2',
            c.signature = 'public void exportToCSV(Data data, String filename, ExportOptions options)'
        RETURN c.persistent_id, c.name, c.signature;
      `;
      const updateCodeResult = await conn.query(updateCodeQuery);
      
      updateCodeResult.resetIterator();
      const updateRow = updateCodeResult.getNextSync();
      console.log(`  コード変更: ${updateRow["c.persistent_id"]} -> ${updateRow["c.name"]}, ${updateRow["c.signature"]}`);
      
      // 変更されたコードに関連する要件を追跡
      const codeChangeImpactQuery = `
        MATCH (c:CodeEntity {persistent_id: 'CODE-EXPORT-001'})<-[:IS_IMPLEMENTED_BY]-(r:RequirementEntity)
        OPTIONAL MATCH (r)<-[:DEPENDS_ON]-(depReq:RequirementEntity)
        RETURN c.persistent_id, c.name, r.id AS direct_req, 
               collect(DISTINCT depReq.id) AS dependent_reqs;
      `;
      const codeChangeImpactResult = await conn.query(codeChangeImpactQuery);
      
      console.log("\n  コード変更の影響を受ける要件:");
      codeChangeImpactResult.resetIterator();
      while (codeChangeImpactResult.hasNext()) {
        const row = codeChangeImpactResult.getNextSync();
        console.log(`    変更コード: ${row["c.name"]} (${row["c.persistent_id"]})`);
        console.log(`    直接関連する要件: ${row["direct_req"]}`);
        console.log(`    間接的に影響を受ける要件: ${row["dependent_reqs"].length > 0 ? row["dependent_reqs"].join(', ') : '(なし)'}`);
      }
    } catch (err) {
      console.error(`  コード変更時の要件追跡に失敗: ${err}`);
    }
    
    // 10. 実装カバレッジの測定
    console.log("\n10. 実装カバレッジの測定");
    try {
      // 全要件数と実装済み要件数を取得
      const coverageQuery = `
        MATCH (r:RequirementEntity)
        WITH count(r) AS total
        MATCH (r2:RequirementEntity)
        WHERE EXISTS { MATCH (r2)-[:IS_IMPLEMENTED_BY]->() }
        WITH total, count(r2) AS implemented
        RETURN total, implemented, 1.0 * implemented / total * 100 AS coverage_percentage;
      `;
      const coverageResult = await conn.query(coverageQuery);
      
      coverageResult.resetIterator();
      const coverageRow = coverageResult.getNextSync();
      console.log(`  要件の実装カバレッジ:`);
      console.log(`    全要件数: ${coverageRow["total"]}`);
      console.log(`    実装済み要件数: ${coverageRow["implemented"]}`);
      console.log(`    実装カバレッジ: ${parseFloat(coverageRow["coverage_percentage"]).toFixed(2)}%`);
    } catch (err) {
      console.error(`  実装カバレッジの測定に失敗: ${err}`);
    }
    
    console.log("\n===== テスト完了 =====");
    console.log("要件からコード実装への双方向トレーサビリティテストが完了しました。");
    
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
