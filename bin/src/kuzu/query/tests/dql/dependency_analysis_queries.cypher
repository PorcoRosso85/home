// 階層型トレーサビリティモデル - 依存関係分析クエリ

// 親要件と子要件、関連要件を作成して依存関係を構築
// @name: create_dependencies_structure
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

// 要件から上流依存関係を取得
// @name: get_upstream_dependencies
MATCH (r:RequirementEntity {id: 'REQ-DEP-CHILD1'})-[:DEPENDS_ON]->(dep:RequirementEntity)
RETURN r.id, r.title, dep.id, dep.title, dep.priority;

// 要件から下流依存関係を取得
// @name: get_downstream_dependencies
MATCH (r:RequirementEntity {id: 'REQ-DEP-PARENT'})<-[:DEPENDS_ON]-(dep:RequirementEntity)
RETURN r.id, r.title, dep.id, dep.title, dep.priority;

// コード実装の依存関係を作成
// @name: create_code_dependencies
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

// 変更影響分析：要件変更時の影響範囲
// @name: analyze_requirement_impact
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

// 変更影響分析：コード変更時の影響範囲
// @name: analyze_code_impact
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

// 多段階の依存関係を作成
// @name: create_multi_level_dependencies
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

// 多段階の依存関係を分析
// @name: analyze_multi_level_dependencies
// コントローラーからの多段階依存関係
MATCH (start:CodeEntity {persistent_id: 'CODE-DEP-CONTROLLER'})
MATCH (start)-[:REFERENCES_CODE*1..4]->(dep:CodeEntity)

WITH start, dep
RETURN 
  start.name AS start_component,
  collect(DISTINCT dep.name) AS dependent_components,
  collect(DISTINCT dep.persistent_id) AS dependent_component_ids;

// 依存関係の最大深度を分析
// @name: analyze_dependency_depth
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