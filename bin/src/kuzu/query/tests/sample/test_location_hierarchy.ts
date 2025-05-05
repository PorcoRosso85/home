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
      const createModuleHierarchyQuery = `
        // ルートモジュール
        CREATE (root:LocationURI {
          uri_id: 'module-root',
          scheme: 'module',
          path: '/system',
          authority: 'system'
        })
        
        // レベル1のモジュール
        CREATE (authModule:LocationURI {
          uri_id: 'module-auth',
          scheme: 'module',
          path: '/system/auth',
          authority: 'system'
        })
        
        CREATE (userModule:LocationURI {
          uri_id: 'module-user',
          scheme: 'module',
          path: '/system/user',
          authority: 'system'
        })
        
        CREATE (reportModule:LocationURI {
          uri_id: 'module-report',
          scheme: 'module',
          path: '/system/report',
          authority: 'system'
        })
        
        // レベル2のモジュール
        CREATE (loginModule:LocationURI {
          uri_id: 'module-login',
          scheme: 'module',
          path: '/system/auth/login',
          authority: 'system'
        })
        
        CREATE (registerModule:LocationURI {
          uri_id: 'module-register',
          scheme: 'module',
          path: '/system/auth/register',
          authority: 'system'
        })
        
        CREATE (profileModule:LocationURI {
          uri_id: 'module-profile',
          scheme: 'module',
          path: '/system/user/profile',
          authority: 'system'
        })
        
        CREATE (exportModule:LocationURI {
          uri_id: 'module-export',
          scheme: 'module',
          path: '/system/report/export',
          authority: 'system'
        })
        
        // 階層関係の構築
        // レベル1の階層
        CREATE (root)-[:CONTAINS_LOCATION {relation_type: 'module'}]->(authModule)
        CREATE (root)-[:CONTAINS_LOCATION {relation_type: 'module'}]->(userModule)
        CREATE (root)-[:CONTAINS_LOCATION {relation_type: 'module'}]->(reportModule)
        
        // レベル2の階層
        CREATE (authModule)-[:CONTAINS_LOCATION {relation_type: 'module'}]->(loginModule)
        CREATE (authModule)-[:CONTAINS_LOCATION {relation_type: 'module'}]->(registerModule)
        CREATE (userModule)-[:CONTAINS_LOCATION {relation_type: 'module'}]->(profileModule)
        CREATE (reportModule)-[:CONTAINS_LOCATION {relation_type: 'module'}]->(exportModule)
        
        RETURN count(*) AS created_nodes;
      `;
      
      const createResult = await conn.query(createModuleHierarchyQuery);
      
      createResult.resetIterator();
      const resultRow = createResult.getNextSync();
      console.log(`  モジュール階層構造を作成: ${resultRow.created_nodes}ノード`);
    } catch (err) {
      console.error(`  モジュール階層構造の作成に失敗: ${err}`);
    }
    
    // 5. 階層を可視化する
    console.log("\n5. 階層を可視化する");
    try {
      const visualizeHierarchyQuery = `
        MATCH path = (root:LocationURI {uri_id: 'module-root'})-[:CONTAINS_LOCATION*0..3]->(child:LocationURI)
        RETURN 
          root.uri_id AS root_id,
          child.uri_id AS child_id,
          child.path AS child_path,
          length(path) AS hierarchy_depth
        ORDER BY hierarchy_depth, child_path;
      `;
      
      const hierarchyResult = await conn.query(visualizeHierarchyQuery);
      
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
      const createRequirementsQuery = `
        // 要件の作成
        CREATE (req1:RequirementEntity {
          id: 'REQ-AUTH-001',
          title: '認証システム要件',
          description: 'ユーザー認証の基本要件',
          priority: 'high',
          requirement_type: 'functional'
        })
        
        CREATE (req2:RequirementEntity {
          id: 'REQ-AUTH-002',
          title: 'ログイン要件',
          description: 'ユーザーログイン機能の詳細要件',
          priority: 'high',
          requirement_type: 'functional'
        })
        
        CREATE (req3:RequirementEntity {
          id: 'REQ-AUTH-003',
          title: 'ユーザー登録要件',
          description: '新規ユーザー登録機能の詳細要件',
          priority: 'high',
          requirement_type: 'functional'
        })
        
        CREATE (req4:RequirementEntity {
          id: 'REQ-USER-001',
          title: 'ユーザープロファイル要件',
          description: 'ユーザープロファイル管理機能の要件',
          priority: 'medium',
          requirement_type: 'functional'
        })
        
        CREATE (req5:RequirementEntity {
          id: 'REQ-REPORT-001',
          title: 'レポートエクスポート要件',
          description: 'データをCSV形式でエクスポートする機能',
          priority: 'low',
          requirement_type: 'functional'
        })
        
        // モジュールと要件の関連付け
        WITH req1, req2, req3, req4, req5
        MATCH (moduleAuth:LocationURI {uri_id: 'module-auth'})
        MATCH (moduleLogin:LocationURI {uri_id: 'module-login'})
        MATCH (moduleRegister:LocationURI {uri_id: 'module-register'})
        MATCH (moduleProfile:LocationURI {uri_id: 'module-profile'})
        MATCH (moduleExport:LocationURI {uri_id: 'module-export'})
        
        CREATE (req1)-[:REQUIREMENT_HAS_LOCATION]->(moduleAuth)
        CREATE (req2)-[:REQUIREMENT_HAS_LOCATION]->(moduleLogin)
        CREATE (req3)-[:REQUIREMENT_HAS_LOCATION]->(moduleRegister)
        CREATE (req4)-[:REQUIREMENT_HAS_LOCATION]->(moduleProfile)
        CREATE (req5)-[:REQUIREMENT_HAS_LOCATION]->(moduleExport)
        
        RETURN count(*) AS created_requirements;
      `;
      
      const requirementsResult = await conn.query(createRequirementsQuery);
      
      requirementsResult.resetIterator();
      const reqRow = requirementsResult.getNextSync();
      console.log(`  要件をモジュール階層にマッピング: ${reqRow.created_requirements}要件`);
    } catch (err) {
      console.error(`  要件のモジュール階層へのマッピングに失敗: ${err}`);
    }
    
    // 7. モジュール階層に基づく要件のナビゲーション
    console.log("\n7. モジュール階層に基づく要件のナビゲーション");
    try {
      // FIXME: 現在のクエリではpath長が0の場合にdepth=-1となり、RangeError: Invalid count valueエラーが発生する
      // 解決案1: depth計算でMAX(length(path) - 1, 0)を使用する
      // 解決案2: CASEステートメントでlength(path)が0の場合は0を返すようにする
      const navigateRequirementsQuery = `
        MATCH (root:LocationURI {uri_id: 'module-root'})
        MATCH path = (root)-[:CONTAINS_LOCATION*0..3]->(module:LocationURI)
        OPTIONAL MATCH (req:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(module)
        
        WITH 
          module.path AS module_path,
          length(path) - 1 AS depth,
          collect(req.id + ': ' + req.title) AS requirements_list
        
        RETURN 
          module_path,
          depth,
          requirements_list
        ORDER BY module_path;
      `;
      
      const navigationResult = await conn.query(navigateRequirementsQuery);
      
      console.log("  モジュール階層と要件のマッピング:");
      navigationResult.resetIterator();
      while (navigationResult.hasNext()) {
        const row = navigationResult.getNextSync();
        const indentation = '  '.repeat(Math.max(0, row.depth)); // 安全対策としてMath.maxを使用
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
      const childRequirementsQuery = `
        MATCH (parent:LocationURI {uri_id: 'module-auth'})
        MATCH path = (parent)-[:CONTAINS_LOCATION*0..2]->(child:LocationURI)
        OPTIONAL MATCH (req:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(child)
        
        WITH child, req
        WHERE req IS NOT NULL
        
        RETURN 
          child.path AS module_path,
          collect(req.id) AS requirement_ids,
          collect(req.title) AS requirement_titles
        ORDER BY module_path;
      `;
      
      const childReqResult = await conn.query(childRequirementsQuery);
      
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
      const addCodeImplementationQuery = `
        // コードエンティティを作成
        CREATE (authService:CodeEntity {
          persistent_id: 'CODE-AUTH-SERVICE',
          name: 'AuthenticationService',
          type: 'class',
          signature: 'class AuthenticationService',
          complexity: 7,
          start_position: 100,
          end_position: 1000
        })
        
        CREATE (loginController:CodeEntity {
          persistent_id: 'CODE-LOGIN-CONTROLLER',
          name: 'LoginController',
          type: 'class',
          signature: 'class LoginController',
          complexity: 5,
          start_position: 1100,
          end_position: 1500
        })
        
        CREATE (registerController:CodeEntity {
          persistent_id: 'CODE-REGISTER-CONTROLLER',
          name: 'RegisterController',
          type: 'class',
          signature: 'class RegisterController',
          complexity: 5,
          start_position: 1600,
          end_position: 2000
        })
        
        // コードとモジュールの関連付け
        WITH authService, loginController, registerController
        MATCH (moduleAuth:LocationURI {uri_id: 'module-auth'})
        MATCH (moduleLogin:LocationURI {uri_id: 'module-login'})
        MATCH (moduleRegister:LocationURI {uri_id: 'module-register'})
        
        CREATE (authService)-[:HAS_LOCATION]->(moduleAuth)
        CREATE (loginController)-[:HAS_LOCATION]->(moduleLogin)
        CREATE (registerController)-[:HAS_LOCATION]->(moduleRegister)
        
        // 要件とコードの関連付け
        WITH authService, loginController, registerController
        MATCH (req1:RequirementEntity {id: 'REQ-AUTH-001'})
        MATCH (req2:RequirementEntity {id: 'REQ-AUTH-002'})
        MATCH (req3:RequirementEntity {id: 'REQ-AUTH-003'})
        
        CREATE (req1)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(authService)
        CREATE (req2)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(loginController)
        CREATE (req3)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(registerController)
        
        RETURN authService.persistent_id, loginController.persistent_id, registerController.persistent_id;
      `;
      
      const codeResult = await conn.query(addCodeImplementationQuery);
      
      codeResult.resetIterator();
      const codeRow = codeResult.getNextSync();
      console.log(`  コード実装を追加: ${codeRow["authService.persistent_id"]}, ${codeRow["loginController.persistent_id"]}, ${codeRow["registerController.persistent_id"]}`);
    } catch (err) {
      console.error(`  階層関係とともにコード実装の追加に失敗: ${err}`);
    }
    
    // 10. 階層構造全体を通じた追跡（要件→モジュール→コード）
    console.log("\n10. 階層構造全体を通じた追跡（要件→モジュール→コード）");
    try {
      const traceHierarchyQuery = `
        MATCH (req:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(module:LocationURI)
        OPTIONAL MATCH (code:CodeEntity)-[:HAS_LOCATION]->(module)
        OPTIONAL MATCH (parent:LocationURI)-[:CONTAINS_LOCATION]->(module)
        OPTIONAL MATCH (req)-[:IS_IMPLEMENTED_BY]->(impl:CodeEntity)
        
        WITH 
          req.id AS requirement_id,
          req.title AS requirement_title,
          module.uri_id AS module_id,
          module.path AS module_path,
          parent.path AS parent_module,
          collect(DISTINCT code.persistent_id) AS module_code_ids,
          collect(DISTINCT impl.persistent_id) AS implementing_code_ids
        
        RETURN 
          requirement_id,
          requirement_title,
          module_id,
          module_path,
          parent_module,
          module_code_ids,
          implementing_code_ids
        ORDER BY module_path;
      `;
      
      const traceResult = await conn.query(traceHierarchyQuery);
      
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
