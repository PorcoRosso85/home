// 階層型トレーサビリティモデル - 外部参照関連クエリ

// 外部参照（APIやライブラリ）のノードとそれらへの依存関係を作成
// @name: create_external_references
// 外部API参照の作成
CREATE (api1:ReferenceEntity {
  id: 'EXT-API-001',
  name: 'Payment Gateway API',
  description: '決済処理用の外部API',
  reference_type: 'external_api',
  version: '2.1',
  url: 'https://api.payment-gateway.example.com/v2'
})

CREATE (api2:ReferenceEntity {
  id: 'EXT-API-002',
  name: 'Geolocation API',
  description: '位置情報取得用の外部API',
  reference_type: 'external_api',
  version: '1.5',
  url: 'https://api.geolocation.example.com/v1'
})

// 外部ライブラリの作成
CREATE (lib1:ReferenceEntity {
  id: 'EXT-LIB-001',
  name: 'AuthLibrary',
  description: '認証・認可用ライブラリ',
  reference_type: 'external_library',
  version: '3.2.1',
  url: 'https://github.com/example/auth-library'
})

CREATE (lib2:ReferenceEntity {
  id: 'EXT-LIB-002',
  name: 'DataProcessorLibrary',
  description: 'データ処理用ライブラリ',
  reference_type: 'external_library',
  version: '2.4.0',
  url: 'https://github.com/example/data-processor'
})

// 外部フレームワークの作成
CREATE (framework:ReferenceEntity {
  id: 'EXT-FRAME-001',
  name: 'WebAppFramework',
  description: 'Webアプリケーション開発フレームワーク',
  reference_type: 'framework',
  version: '5.1.3',
  url: 'https://github.com/example/web-framework'
})

// LocationURIの作成（管理用）
CREATE (extLoc:LocationURI {
  uri_id: 'ext-references',
  scheme: 'external',
  path: '/external-references',
  authority: 'system'
})

// 外部参照とLocationURIの関連付け
CREATE (api1)-[:REFERENCE_HAS_LOCATION]->(extLoc)
CREATE (api2)-[:REFERENCE_HAS_LOCATION]->(extLoc)
CREATE (lib1)-[:REFERENCE_HAS_LOCATION]->(extLoc)
CREATE (lib2)-[:REFERENCE_HAS_LOCATION]->(extLoc)
CREATE (framework)-[:REFERENCE_HAS_LOCATION]->(extLoc)

RETURN 5 AS created_references;

// 外部参照と要件・コードの関連付け
// @name: create_requirements_and_dependencies
// 要件の作成
CREATE (req1:RequirementEntity {
  id: 'REQ-EXT-001',
  title: '決済処理要件',
  description: 'システムは外部決済ゲートウェイを使用して支払いを処理できること',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req2:RequirementEntity {
  id: 'REQ-EXT-002',
  title: '位置情報表示要件',
  description: 'システムはユーザーの現在位置を地図上に表示できること',
  priority: 'medium',
  requirement_type: 'functional'
})

CREATE (req3:RequirementEntity {
  id: 'REQ-EXT-003',
  title: '認証要件',
  description: 'システムはOAuth2.0を使用してユーザー認証を行うこと',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req4:RequirementEntity {
  id: 'REQ-EXT-004',
  title: 'データエクスポート要件',
  description: 'システムはデータをCSV形式でエクスポートできること',
  priority: 'low',
  requirement_type: 'functional'
})

// コードエンティティの作成
CREATE (code1:CodeEntity {
  persistent_id: 'CODE-EXT-001',
  name: 'PaymentProcessor',
  type: 'class',
  signature: 'class PaymentProcessor',
  complexity: 7,
  start_position: 100,
  end_position: 1000
})

CREATE (code2:CodeEntity {
  persistent_id: 'CODE-EXT-002',
  name: 'LocationService',
  type: 'class',
  signature: 'class LocationService',
  complexity: 6,
  start_position: 1100,
  end_position: 2000
})

CREATE (code3:CodeEntity {
  persistent_id: 'CODE-EXT-003',
  name: 'AuthenticationManager',
  type: 'class',
  signature: 'class AuthenticationManager',
  complexity: 8,
  start_position: 2100,
  end_position: 3000
})

CREATE (code4:CodeEntity {
  persistent_id: 'CODE-EXT-004',
  name: 'DataExporter',
  type: 'class',
  signature: 'class DataExporter',
  complexity: 5,
  start_position: 3100,
  end_position: 4000
})

// 外部参照と要件の関連付け
WITH req1, req2, req3, req4, code1, code2, code3, code4
MATCH (api1:ReferenceEntity {id: 'EXT-API-001'})  // Payment Gateway API
MATCH (api2:ReferenceEntity {id: 'EXT-API-002'})  // Geolocation API
MATCH (lib1:ReferenceEntity {id: 'EXT-LIB-001'})  // AuthLibrary
MATCH (lib2:ReferenceEntity {id: 'EXT-LIB-002'})  // DataProcessorLibrary
MATCH (framework:ReferenceEntity {id: 'EXT-FRAME-001'}) // WebAppFramework

// 要件と外部参照の関連付け
CREATE (req1)-[:DEPENDS_ON_EXTERNAL {dependency_type: 'required'}]->(api1)
CREATE (req2)-[:DEPENDS_ON_EXTERNAL {dependency_type: 'required'}]->(api2)
CREATE (req3)-[:DEPENDS_ON_EXTERNAL {dependency_type: 'required'}]->(lib1)
CREATE (req4)-[:DEPENDS_ON_EXTERNAL {dependency_type: 'optional'}]->(lib2)

// 要件とコードの関連付け
CREATE (req1)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code1)
CREATE (req2)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code2)
CREATE (req3)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code3)
CREATE (req4)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code4)

// コードと外部参照の関連付け
// FIXME: 旧リレーション "DEPENDS_ON_EXTERNAL" は "REFERS_TO" との一貫性のために変更を検討
// "DEPENDS_ON_EXTERNAL" はクエリの一部でのみ使用され、スキーマで定義された "REFERENCES_EXTERNAL"/"REFERS_TO" とは異なる
CREATE (code1)-[:REFERS_TO {dependency_type: 'imports'}]->(api1)
CREATE (code2)-[:REFERS_TO {dependency_type: 'imports'}]->(api2)
CREATE (code3)-[:REFERS_TO {dependency_type: 'imports'}]->(lib1)
CREATE (code4)-[:REFERS_TO {dependency_type: 'imports'}]->(lib2)

// すべてのコードはフレームワークに依存
CREATE (code1)-[:REFERS_TO {dependency_type: 'extends'}]->(framework)
CREATE (code2)-[:REFERS_TO {dependency_type: 'extends'}]->(framework)
CREATE (code3)-[:REFERS_TO {dependency_type: 'extends'}]->(framework)
CREATE (code4)-[:REFERS_TO {dependency_type: 'extends'}]->(framework)

RETURN 4 AS created_requirements, 4 AS created_code;

// 外部参照の一覧取得
// @name: list_external_references
MATCH (ref:ReferenceEntity)
WHERE ref.reference_type IN $types OR $types IS NULL
RETURN 
  ref.id AS reference_id,
  ref.name AS reference_name,
  ref.description AS reference_description,
  ref.reference_type AS reference_type,
  ref.version AS reference_version,
  ref.url AS reference_url
ORDER BY ref.reference_type, ref.name;

// 要件から外部参照への依存関係を追跡
// @name: trace_requirements_to_external
MATCH (req:RequirementEntity)-[:DEPENDS_ON_EXTERNAL]->(ref:ReferenceEntity)
RETURN 
  req.id AS requirement_id,
  req.title AS requirement_title,
  req.priority AS requirement_priority,
  ref.id AS reference_id,
  ref.name AS reference_name,
  ref.reference_type AS reference_type,
  ref.version AS reference_version
ORDER BY req.priority, req.id;

// コードから外部参照への依存関係を追跡
// @name: trace_code_to_external
// FIXME: 旧リレーション "DEPENDS_ON_EXTERNAL" から "REFERS_TO" に変更
MATCH (code:CodeEntity)-[rel:REFERS_TO]->(ref:ReferenceEntity)
RETURN 
  code.persistent_id AS code_id,
  code.name AS code_name,
  code.type AS code_type,
  rel.dependency_type AS dependency_type,
  ref.id AS reference_id,
  ref.name AS reference_name,
  ref.reference_type AS reference_type,
  ref.version AS reference_version
ORDER BY code.name, ref.reference_type;

// 特定の外部参照に依存するすべての要件とコードを取得
// @name: get_dependencies_for_reference
MATCH (ref:ReferenceEntity {id: $referenceId})
// FIXME: 要件では "DEPENDS_ON_EXTERNAL" を使用し、コードでは "REFERS_TO" に変更
OPTIONAL MATCH (req:RequirementEntity)-[reqRel:DEPENDS_ON_EXTERNAL]->(ref)
OPTIONAL MATCH (code:CodeEntity)-[codeRel:REFERS_TO]->(ref)

WITH 
  ref,
  collect(DISTINCT {id: req.id, title: req.title, dependency_type: reqRel.dependency_type}) AS requirements,
  collect(DISTINCT {id: code.persistent_id, name: code.name, dependency_type: codeRel.dependency_type}) AS code_entities

RETURN 
  ref.id AS reference_id,
  ref.name AS reference_name,
  ref.reference_type AS reference_type,
  ref.version AS reference_version,
  requirements,
  code_entities;

// 外部参照の更新をシミュレート
// @name: simulate_reference_update
// 既存の外部参照をバージョンアップ
MATCH (ref:ReferenceEntity {id: $referenceId})
SET ref.version = $newVersion
SET ref.update_date = $updateDate
RETURN ref.id, ref.name, ref.version, ref.update_date;

// 外部参照の更新による影響範囲分析
// @name: analyze_update_impact
MATCH (ref:ReferenceEntity {id: $referenceId})
// 要件への依存関係を取得
OPTIONAL MATCH (req:RequirementEntity)-[:DEPENDS_ON_EXTERNAL]->(ref)
// コードへの依存関係を取得
// FIXME: 旧リレーション "DEPENDS_ON_EXTERNAL" から "REFERS_TO" に変更
OPTIONAL MATCH (code:CodeEntity)-[:REFERS_TO]->(ref)
// 間接的に依存するコードを取得（要件を通じて）
// FIXME: 片方のリレーションを "REFERS_TO" に変更
OPTIONAL MATCH (indirectReq:RequirementEntity)-[:DEPENDS_ON_EXTERNAL]->(ref)<-[:REFERS_TO]-(otherCode:CodeEntity)
WHERE indirectReq <> req AND otherCode <> code

WITH 
  ref.id AS reference_id,
  ref.name AS reference_name,
  ref.version AS reference_version,
  count(DISTINCT req) AS affected_requirements_count,
  collect(DISTINCT req.id) AS affected_requirements,
  count(DISTINCT code) AS affected_code_count,
  collect(DISTINCT code.persistent_id) AS affected_code,
  count(DISTINCT otherCode) AS indirectly_affected_code_count,
  collect(DISTINCT otherCode.persistent_id) AS indirectly_affected_code

RETURN 
  reference_id,
  reference_name,
  reference_version,
  affected_requirements_count,
  affected_requirements,
  affected_code_count,
  affected_code,
  indirectly_affected_code_count,
  indirectly_affected_code;

// 外部参照の廃止をシミュレート
// @name: simulate_reference_deprecation
// 外部参照に廃止フラグを設定
MATCH (ref:ReferenceEntity {id: $referenceId})
SET ref.deprecated = true
SET ref.deprecation_date = $deprecationDate
SET ref.replacement_id = $replacementId
RETURN ref.id, ref.name, ref.deprecated, ref.deprecation_date, ref.replacement_id;

// 廃止された外部参照とその代替手段の関連付け
// @name: create_replacement_reference
// 代替の外部参照を作成
CREATE (newRef:ReferenceEntity {
  id: $newReferenceId,
  name: $newReferenceName,
  description: $newReferenceDescription,
  reference_type: $referenceType,
  version: $version,
  url: $url
})

// 既存の場所と関連付け
WITH newRef
MATCH (extLoc:LocationURI {uri_id: 'ext-references'})
CREATE (newRef)-[:REFERENCE_HAS_LOCATION]->(extLoc)

// 廃止された参照と関連付け
WITH newRef
MATCH (oldRef:ReferenceEntity {id: $oldReferenceId})
CREATE (oldRef)-[:REPLACED_BY]->(newRef)

RETURN newRef.id, newRef.name, newRef.version;

// 外部参照の移行計画を作成
// @name: create_migration_plan
// 移行すべき要件とコードを特定
MATCH (oldRef:ReferenceEntity {id: $oldReferenceId})
MATCH (newRef:ReferenceEntity {id: $newReferenceId})
OPTIONAL MATCH (req:RequirementEntity)-[reqRel:DEPENDS_ON_EXTERNAL]->(oldRef)
// FIXME: 旧リレーション "DEPENDS_ON_EXTERNAL" から "REFERS_TO" に変更
OPTIONAL MATCH (code:CodeEntity)-[codeRel:REFERS_TO]->(oldRef)

WITH 
  oldRef, newRef,
  collect(DISTINCT {id: req.id, title: req.title, dependency_type: reqRel.dependency_type}) AS requirements_to_migrate,
  collect(DISTINCT {id: code.persistent_id, name: code.name, dependency_type: codeRel.dependency_type}) AS code_to_migrate

RETURN 
  oldRef.id AS old_reference_id,
  oldRef.name AS old_reference_name,
  oldRef.version AS old_reference_version,
  newRef.id AS new_reference_id,
  newRef.name AS new_reference_name,
  newRef.version AS new_reference_version,
  requirements_to_migrate,
  code_to_migrate;
