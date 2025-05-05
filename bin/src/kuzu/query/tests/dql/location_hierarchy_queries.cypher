// 階層型トレーサビリティモデル - LocationURI階層構造関連クエリ

// モジュール階層構造を作成するためのクエリ
// @name: create_module_hierarchy
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

// 階層を可視化するクエリ
// @name: visualize_hierarchy
MATCH path = (root:LocationURI {uri_id: 'module-root'})-[:CONTAINS_LOCATION*0..3]->(child:LocationURI)
RETURN 
  root.uri_id AS root_id,
  child.uri_id AS child_id,
  child.path AS child_path,
  length(path) AS hierarchy_depth
ORDER BY hierarchy_depth, child_path;

// 要件をモジュール階層にマッピングするクエリ
// @name: create_requirements_with_mapping
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

// モジュール階層に基づく要件のナビゲーションクエリ
// @name: navigate_requirements_by_module
MATCH (root:LocationURI {uri_id: 'module-root'})
MATCH path = (root)-[:CONTAINS_LOCATION*0..3]->(module:LocationURI)
OPTIONAL MATCH (req:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(module)

WITH 
  module.path AS module_path,
  CASE WHEN length(path) = 0 THEN 0 ELSE length(path) - 1 END AS depth,
  collect(req.id + ': ' + req.title) AS requirements_list

RETURN 
  module_path,
  depth,
  requirements_list
ORDER BY module_path;

// 特定モジュールの子要件を再帰的に取得するクエリ
// @name: get_child_requirements
MATCH (parent:LocationURI {uri_id: $moduleId})
MATCH path = (parent)-[:CONTAINS_LOCATION*0..2]->(child:LocationURI)
OPTIONAL MATCH (req:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(child)

WITH child, req
WHERE req IS NOT NULL

RETURN 
  child.path AS module_path,
  collect(req.id) AS requirement_ids,
  collect(req.title) AS requirement_titles
ORDER BY module_path;

// 階層関係とともにコード実装を追加するクエリ
// @name: add_code_implementation
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

// 階層構造全体を通じた追跡（要件→モジュール→コード）
// @name: trace_hierarchy
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