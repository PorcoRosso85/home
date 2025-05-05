// 階層型トレーサビリティモデル - 要件カバレッジ測定関連クエリ

// テスト用の要件とコード実装、検証を作成
// @name: create_coverage_test_data
// 要件の作成
CREATE (req1:RequirementEntity {
  id: 'REQ-COV-001',
  title: '認証機能',
  description: 'ユーザーを認証する機能',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req2:RequirementEntity {
  id: 'REQ-COV-002',
  title: '認可機能',
  description: 'ユーザーアクセスを制御する機能',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req3:RequirementEntity {
  id: 'REQ-COV-003',
  title: 'プロファイル管理',
  description: 'ユーザープロファイルを管理する機能',
  priority: 'medium',
  requirement_type: 'functional'
})

CREATE (req4:RequirementEntity {
  id: 'REQ-COV-004',
  title: 'データエクスポート',
  description: 'データをエクスポートする機能',
  priority: 'low',
  requirement_type: 'functional'
})

CREATE (req5:RequirementEntity {
  id: 'REQ-COV-005',
  title: 'レポート生成',
  description: 'レポートを生成する機能',
  priority: 'medium',
  requirement_type: 'functional'
})

// コードエンティティを作成
CREATE (code1:CodeEntity {
  persistent_id: 'CODE-COV-001',
  name: 'AuthenticationService',
  type: 'class',
  signature: 'class AuthenticationService',
  complexity: 7,
  start_position: 100,
  end_position: 1000
})

CREATE (code2:CodeEntity {
  persistent_id: 'CODE-COV-002',
  name: 'AuthorizationService',
  type: 'class',
  signature: 'class AuthorizationService',
  complexity: 6,
  start_position: 1100,
  end_position: 2000
})

CREATE (code3:CodeEntity {
  persistent_id: 'CODE-COV-003',
  name: 'ProfileManager',
  type: 'class',
  signature: 'class ProfileManager',
  complexity: 5,
  start_position: 2100,
  end_position: 3000
})

// 検証エンティティを作成
CREATE (ver1:RequirementVerification {
  id: 'TEST-COV-001',
  name: '認証テスト',
  description: 'ユーザー認証機能のテスト',
  verification_type: 'unit_test'
})

CREATE (ver2:RequirementVerification {
  id: 'TEST-COV-002',
  name: '認可テスト',
  description: 'ユーザー認可機能のテスト',
  verification_type: 'unit_test'
})

CREATE (ver3:RequirementVerification {
  id: 'TEST-COV-003',
  name: 'プロファイルテスト',
  description: 'プロファイル管理機能のテスト',
  verification_type: 'integration_test'
})

// 実装関係を作成
CREATE (req1)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code1)
CREATE (req2)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code2)
CREATE (req3)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code3)

// 検証関係を作成
CREATE (req1)-[:VERIFIED_BY]->(ver1)
CREATE (req2)-[:VERIFIED_BY]->(ver2)
CREATE (req4)-[:VERIFIED_BY]->(ver3)

RETURN 5 AS created_requirements, 3 AS created_code, 3 AS created_verifications;

// 要件全体のカバレッジを測定
// @name: measure_overall_coverage
MATCH (r:RequirementEntity)
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(v:RequirementVerification)

WITH 
  count(r) AS total_requirements,
  count(DISTINCT CASE WHEN c IS NOT NULL THEN r END) AS implemented_requirements,
  count(DISTINCT CASE WHEN v IS NOT NULL THEN r END) AS verified_requirements,
  count(DISTINCT CASE WHEN c IS NOT NULL AND v IS NOT NULL THEN r END) AS fully_covered_requirements

RETURN 
  total_requirements,
  implemented_requirements,
  verified_requirements,
  fully_covered_requirements,
  1.0 * implemented_requirements / total_requirements * 100 AS implementation_coverage_pct,
  1.0 * verified_requirements / total_requirements * 100 AS verification_coverage_pct,
  1.0 * fully_covered_requirements / total_requirements * 100 AS full_coverage_pct;

// 優先度ごとのカバレッジを測定
// @name: measure_coverage_by_priority
MATCH (r:RequirementEntity)
WHERE r.priority IN $priorities OR $priorities IS NULL
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(v:RequirementVerification)

WITH 
  r.priority AS priority,
  count(r) AS total,
  count(DISTINCT CASE WHEN c IS NOT NULL THEN r END) AS implemented,
  count(DISTINCT CASE WHEN v IS NOT NULL THEN r END) AS verified,
  count(DISTINCT CASE WHEN c IS NOT NULL AND v IS NOT NULL THEN r END) AS fully_covered

RETURN 
  priority,
  total,
  implemented,
  verified,
  fully_covered,
  1.0 * implemented / total * 100 AS implementation_coverage_pct,
  1.0 * verified / total * 100 AS verification_coverage_pct,
  1.0 * fully_covered / total * 100 AS full_coverage_pct
ORDER BY CASE priority
  WHEN 'high' THEN 1
  WHEN 'medium' THEN 2
  WHEN 'low' THEN 3
  ELSE 4
END;

// 未カバー要件のリスト取得
// @name: get_uncovered_requirements
MATCH (r:RequirementEntity)
WHERE NOT EXISTS { MATCH (r)-[:IS_IMPLEMENTED_BY]->() }
   OR NOT EXISTS { MATCH (r)-[:VERIFIED_BY]->() }
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(v:RequirementVerification)

RETURN 
  r.id AS requirement_id,
  r.title AS requirement_title,
  r.priority AS requirement_priority,
  CASE WHEN c IS NULL THEN false ELSE true END AS has_implementation,
  CASE WHEN v IS NULL THEN false ELSE true END AS has_verification
ORDER BY r.priority, r.id;

// 追加のコード実装と検証を作成してカバレッジを向上
// @name: improve_coverage
// 残りの要件に対する実装を追加
MATCH (req4:RequirementEntity {id: 'REQ-COV-004'})
MATCH (req5:RequirementEntity {id: 'REQ-COV-005'})

// 新しいコードエンティティを作成
CREATE (code4:CodeEntity {
  persistent_id: 'CODE-COV-004',
  name: 'ExportService',
  type: 'class',
  signature: 'class ExportService',
  complexity: 4,
  start_position: 3100,
  end_position: 4000
})

CREATE (code5:CodeEntity {
  persistent_id: 'CODE-COV-005',
  name: 'ReportGenerator',
  type: 'class',
  signature: 'class ReportGenerator',
  complexity: 6,
  start_position: 4100,
  end_position: 5000
})

// 実装関係を作成
CREATE (req4)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code4)
CREATE (req5)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code5)

// 新しい検証エンティティを作成
CREATE (ver4:RequirementVerification {
  id: 'TEST-COV-004',
  name: 'エクスポートテスト',
  description: 'データエクスポート機能のテスト',
  verification_type: 'integration_test'
})

CREATE (ver5:RequirementVerification {
  id: 'TEST-COV-005',
  name: 'レポート生成テスト',
  description: 'レポート生成機能のテスト',
  verification_type: 'system_test'
})

// 検証関係を作成
CREATE (req3)-[:VERIFIED_BY]->(ver4)  // 既にコード実装のあるreq3に検証を追加
CREATE (req5)-[:VERIFIED_BY]->(ver5)  // req5にも検証を追加（req4は既に検証があるため、追加しない）

RETURN 2 AS created_code, 2 AS created_verifications;

// タイプ別のカバレッジ測定
// @name: measure_coverage_by_type
MATCH (r:RequirementEntity)
WHERE r.requirement_type IN $types OR $types IS NULL
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(v:RequirementVerification)

WITH 
  r.requirement_type AS requirement_type,
  count(r) AS total,
  count(DISTINCT CASE WHEN c IS NOT NULL THEN r END) AS implemented,
  count(DISTINCT CASE WHEN v IS NOT NULL THEN r END) AS verified,
  count(DISTINCT CASE WHEN c IS NOT NULL AND v IS NOT NULL THEN r END) AS fully_covered

RETURN 
  requirement_type,
  total,
  implemented,
  verified,
  fully_covered,
  1.0 * implemented / total * 100 AS implementation_coverage_pct,
  1.0 * verified / total * 100 AS verification_coverage_pct,
  1.0 * fully_covered / total * 100 AS full_coverage_pct
ORDER BY requirement_type;

// 検証タイプによるカバレッジ分析
// @name: analyze_verification_types
MATCH (r:RequirementEntity)-[:VERIFIED_BY]->(v:RequirementVerification)
WITH 
  v.verification_type AS verification_type,
  count(DISTINCT r) AS requirements_count

RETURN 
  verification_type,
  requirements_count
ORDER BY requirements_count DESC;

// 各要件のカバレッジ詳細
// @name: get_detailed_coverage
MATCH (r:RequirementEntity)
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(v:RequirementVerification)

WITH 
  r.id AS requirement_id,
  r.title AS requirement_title,
  r.priority AS priority,
  collect(DISTINCT c.persistent_id) AS implementations,
  collect(DISTINCT v.id) AS verifications,
  CASE WHEN count(c) > 0 THEN true ELSE false END AS has_implementation,
  CASE WHEN count(v) > 0 THEN true ELSE false END AS has_verification

RETURN 
  requirement_id,
  requirement_title,
  priority,
  implementations,
  verifications,
  has_implementation,
  has_verification,
  CASE 
    WHEN has_implementation AND has_verification THEN 'fully_covered'
    WHEN has_implementation THEN 'implemented_only'
    WHEN has_verification THEN 'verified_only'
    ELSE 'not_covered'
  END AS coverage_status
ORDER BY priority, requirement_id;