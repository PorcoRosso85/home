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
      const createDependenciesQuery = `
        // 親要件を作成
        CREATE (parent:RequirementEntity {
          id: 'REQ-DEP-PARENT',
          title: 'ユーザー管理機能',
          description: 'システムで管理するユーザーを登録・編集・削除する機能',
          priority: 'high',
          requirement_type: 'functional'
        })
        
        // 子要件群を作成
        CREATE (child1:RequirementEntity {
          id: 'REQ-DEP-CHILD1',
          title: 'ユーザー登録機能',
          description: '新規ユーザーを登録する機能',
          priority: 'high',
          requirement_type: 'functional'
        })
        
        CREATE (child2:RequirementEntity {
          id: 'REQ-DEP-CHILD2',
          title: 'ユーザー編集機能',
          description: '既存ユーザーの情報を編集する機能',
          priority: 'medium',
          requirement_type: 'functional'
        })
        
        CREATE (child3:RequirementEntity {
          id: 'REQ-DEP-CHILD3',
          title: 'ユーザー削除機能',
          description: '既存ユーザーを削除する機能',
          priority: 'medium',
          requirement_type: 'functional'
        })
        
        // 関連要件を作成
        CREATE (related1:RequirementEntity {
          id: 'REQ-DEP-RELATED1',
          title: 'アクセス権管理機能',
          description: 'ユーザーごとのシステムアクセス権を管理する機能',
          priority: 'high',
          requirement_type: 'functional'
        })
        
        CREATE (related2:RequirementEntity {
          id: 'REQ-DEP-RELATED2',
          title: 'ユーザー認証機能',
          description: 'ユーザー名とパスワードによる認証機能',
          priority: 'high',
          requirement_type: 'functional'
        })
        
        // 依存関係を構築
        // 親子関係
        CREATE (child1)-[:DEPENDS_ON {dependency_type: 'parent_child'}]->(parent)
        CREATE (child2)-[:DEPENDS_ON {dependency_type: 'parent_child'}]->(parent)
        CREATE (child3)-[:DEPENDS_ON {dependency_type: 'parent_child'}]->(parent)
        
        // 機能間依存
        CREATE (child1)-[:DEPENDS_ON {dependency_type: 'functional'}]->(related1)
        CREATE (child1)-[:DEPENDS_ON {dependency_type: 'functional'}]->(related2)
        
        RETURN parent.id, child1.id, child2.id, child3.id, related1.id, related2.id;
      `;
      
      const dependenciesResult = await conn.query(createDependenciesQuery);
      
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
      const upstreamDependenciesQuery = `
        MATCH (r:RequirementEntity {id: 'REQ-DEP-CHILD1'})-[:DEPENDS_ON]->(dep:RequirementEntity)
        RETURN r.id, r.title, dep.id, dep.title, dep.priority;
      `;
      
      const upstreamResult = await conn.query(upstreamDependenciesQuery);
      
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
      const downstreamDependenciesQuery = `
        MATCH (r:RequirementEntity {id: 'REQ-DEP-PARENT'})<-[:DEPENDS_ON]-(dep:RequirementEntity)
        RETURN r.id, r.title, dep.id, dep.title, dep.priority;
      `;
      
      const downstreamResult = await conn.query(downstreamDependenciesQuery);
      
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
      const createCodeDependenciesQuery = `
        // コードエンティティを作成
        CREATE (controller:CodeEntity {
          persistent_id: 'CODE-DEP-CONTROLLER',
          name: 'UserController',
          type: 'class',
          signature: 'class UserController',
          complexity: 5,
          start_position: 100,
          end_position: 1000
        })
        
        CREATE (service:CodeEntity {
          persistent_id: 'CODE-DEP-SERVICE',
          name: 'UserService',
          type: 'class',
          signature: 'class UserService',
          complexity: 8,
          start_position: 1100,
          end_position: 2000
        })
        
        CREATE (repository:CodeEntity {
          persistent_id: 'CODE-DEP-REPOSITORY',
          name: 'UserRepository',
          type: 'class',
          signature: 'class UserRepository',
          complexity: 6,
          start_position: 2100,
          end_position: 3000
        })
        
        // コード間の参照関係
        CREATE (controller)-[:REFERENCES_CODE {ref_type: 'dependency'}]->(service)
        CREATE (service)-[:REFERENCES_CODE {ref_type: 'dependency'}]->(repository)
        
        // 要件との関連付け
        WITH controller, service, repository
        MATCH (parentReq:RequirementEntity {id: 'REQ-DEP-PARENT'})
        MATCH (childReq1:RequirementEntity {id: 'REQ-DEP-CHILD1'})
        
        CREATE (parentReq)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(controller)
        CREATE (childReq1)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(service)
        
        RETURN controller.persistent_id, service.persistent_id, repository.persistent_id;
      `;
      
      const codeDepResult = await conn.query(createCodeDependenciesQuery);
      
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
      const requirementImpactQuery = `
        // 親要件が変更された場合の影響
        MATCH (r:RequirementEntity {id: 'REQ-DEP-PARENT'})
        
        // 直接の下流要件を特定
        OPTIONAL MATCH (r)<-[:DEPENDS_ON]-(directDep:RequirementEntity)
        
        // 下流要件から実装コードへの影響
        OPTIONAL MATCH (directDep)-[:IS_IMPLEMENTED_BY]->(depCode:CodeEntity)
        
        // 親要件の実装コード
        OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(directCode:CodeEntity)
        
        // 実装コードの依存関係
        OPTIONAL MATCH (directCode)-[:REFERENCES_CODE*1..3]->(indirectCode:CodeEntity)
        
        RETURN 
          r.id AS changed_req,
          collect(DISTINCT directDep.id) AS affected_requirements,
          collect(DISTINCT directCode.persistent_id) AS direct_code,
          collect(DISTINCT depCode.persistent_id) AS requirement_dependent_code,
          collect(DISTINCT indirectCode.persistent_id) AS code_dependent_code;
      `;
      
      const impactResult = await conn.query(requirementImpactQuery);
      
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
      const codeImpactQuery = `
        // サービスクラスが変更された場合の影響
        MATCH (c:CodeEntity {persistent_id: 'CODE-DEP-SERVICE'})
        
        // 上流のコード依存（サービスに依存するコード）
        OPTIONAL MATCH (upstream:CodeEntity)-[:REFERENCES_CODE]->(c)
        
        // 下流のコード依存（サービスが依存するコード）
        OPTIONAL MATCH (c)-[:REFERENCES_CODE]->(downstream:CodeEntity)
        
        // 関連する要件
        OPTIONAL MATCH (req:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(c)
        
        // 上流コードに関連する要件
        OPTIONAL MATCH (upReq:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(upstream)
        
        RETURN 
          c.persistent_id AS changed_code,
          c.name AS code_name,
          collect(DISTINCT upstream.persistent_id) AS upstream_code,
          collect(DISTINCT downstream.persistent_id) AS downstream_code,
          collect(DISTINCT req.id) AS direct_requirements,
          collect(DISTINCT upReq.id) AS upstream_requirements;
      `;
      
      const codeImpactResult = await conn.query(codeImpactQuery);
      
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
      const createMultiLevelDependenciesQuery = `
        // さらに依存するコンポーネントを追加
        CREATE (util:CodeEntity {
          persistent_id: 'CODE-DEP-UTIL',
          name: 'UserUtils',
          type: 'class',
          signature: 'class UserUtils',
          complexity: 3,
          start_position: 3100,
          end_position: 3500
        })
        
        CREATE (validator:CodeEntity {
          persistent_id: 'CODE-DEP-VALIDATOR',
          name: 'UserValidator',
          type: 'class',
          signature: 'class UserValidator',
          complexity: 4,
          start_position: 3600,
          end_position: 4000
        })
        
        // 既存のリポジトリと接続
        WITH util, validator
        MATCH (repository:CodeEntity {persistent_id: 'CODE-DEP-REPOSITORY'})
        
        CREATE (repository)-[:REFERENCES_CODE {ref_type: 'dependency'}]->(util)
        CREATE (repository)-[:REFERENCES_CODE {ref_type: 'dependency'}]->(validator)
        
        RETURN util.persistent_id, validator.persistent_id;
      `;
      
      await conn.query(createMultiLevelDependenciesQuery);
      
      // 多段階の依存関係を分析
      const multiLevelAnalysisQuery = `
        // コントローラーからの多段階依存関係
        MATCH (start:CodeEntity {persistent_id: 'CODE-DEP-CONTROLLER'})
        MATCH (start)-[:REFERENCES_CODE*1..4]->(dep:CodeEntity)
        
        WITH start, dep
        RETURN 
          start.name AS start_component,
          collect(DISTINCT dep.name) AS dependent_components,
          collect(DISTINCT dep.persistent_id) AS dependent_component_ids;
      `;
      
      const multiLevelResult = await conn.query(multiLevelAnalysisQuery);
      
      multiLevelResult.resetIterator();
      const multiLevelRow = multiLevelResult.getNextSync();
      
      console.log(`  コンポーネント「${multiLevelRow["start_component"]}」の多段階依存関係分析:`);
      console.log(`    依存コンポーネント: ${multiLevelRow["dependent_components"].join(', ')}`);
      console.log(`    依存コンポーネントID: ${multiLevelRow["dependent_component_ids"].join(', ')}`);
      
      // 依存関係の最大深度分析
      const dependencyDepthQuery = `
        MATCH (start:CodeEntity {persistent_id: 'CODE-DEP-CONTROLLER'})
        MATCH path = (start)-[:REFERENCES_CODE*]->(dep:CodeEntity)
        WHERE NOT (dep)-[:REFERENCES_CODE]->()
        
        WITH start, path AS path, length(path) AS depth, dep AS dep
        ORDER BY depth DESC
        LIMIT 1
        
        RETURN 
          start.name AS start_component,
          dep.name AS end_component,
          depth AS max_dependency_depth;
      `;
      
      const depthResult = await conn.query(dependencyDepthQuery);
      
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
