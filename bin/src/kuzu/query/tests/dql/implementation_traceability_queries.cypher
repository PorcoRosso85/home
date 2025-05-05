// 階層型トレーサビリティモデル - 実装トレーサビリティ関連クエリ

// 要件とコードエンティティを作成し、関連付ける
// @name: create_requirement_and_code
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

// 要件からコードへのトレーサビリティを分析
// @name: trace_requirement_to_code
MATCH (r:RequirementEntity {id: 'REQ-IMPL-001'})-[rel:IS_IMPLEMENTED_BY]->(c:CodeEntity)
RETURN r.id, r.title, c.persistent_id, c.name, rel.implementation_type;

// コードから要件へのトレーサビリティを分析
// @name: trace_code_to_requirement
MATCH (c:CodeEntity {persistent_id: 'CODE-EXPORT-001'})<-[rel:IS_IMPLEMENTED_BY]-(r:RequirementEntity)
RETURN c.persistent_id, c.name, r.id, r.title, rel.implementation_type;

// 未実装の要件を作成
// @name: create_unimplemented_requirement
CREATE (r:RequirementEntity {
  id: 'REQ-UNIMPLEMENTED',
  title: '未実装の要件',
  description: 'これはまだ実装されていない要件です',
  priority: 'high',
  requirement_type: 'functional'
})
RETURN r.id, r.title;

// 未実装の要件を検出
// @name: find_unimplemented_requirements
MATCH (r:RequirementEntity)
WHERE NOT EXISTS { MATCH (r)-[:IS_IMPLEMENTED_BY]->() }
RETURN r.id, r.title, r.priority;

// 関連要件間の依存関係を作成
// @name: create_requirement_dependency
MATCH (req1:RequirementEntity {id: 'REQ-UNIMPLEMENTED'}), (req2:RequirementEntity {id: 'REQ-IMPL-001'})
CREATE (req1)-[:DEPENDS_ON {dependency_type: 'functional'}]->(req2)
RETURN req1.id, req2.id;

// 影響分析（依存する要件と、その実装コード）
// @name: analyze_requirement_impact
MATCH (r:RequirementEntity {id: 'REQ-UNIMPLEMENTED'})-[:DEPENDS_ON*1..3]->(dep:RequirementEntity)
OPTIONAL MATCH (dep)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
RETURN r.id AS source_req, dep.id AS dependency, 
       collect(DISTINCT c.persistent_id) AS affected_code;

// コード変更のシミュレーション（既存コードを修正）
// @name: update_code
MATCH (c:CodeEntity {persistent_id: 'CODE-EXPORT-001'})
SET c.name = 'exportToCSV_v2',
    c.signature = 'public void exportToCSV(Data data, String filename, ExportOptions options)'
RETURN c.persistent_id, c.name, c.signature;

// 変更されたコードに関連する要件を追跡
// @name: analyze_code_change_impact
MATCH (c:CodeEntity {persistent_id: 'CODE-EXPORT-001'})<-[:IS_IMPLEMENTED_BY]-(r:RequirementEntity)
OPTIONAL MATCH (r)<-[:DEPENDS_ON]-(depReq:RequirementEntity)
RETURN c.persistent_id, c.name, r.id AS direct_req, 
       collect(DISTINCT depReq.id) AS dependent_reqs;

// 実装カバレッジの測定
// @name: measure_implementation_coverage
MATCH (r:RequirementEntity)
WITH count(r) AS total
MATCH (r2:RequirementEntity)
WHERE EXISTS { MATCH (r2)-[:IS_IMPLEMENTED_BY]->() }
WITH total, count(r2) AS implemented
RETURN total, implemented, 1.0 * implemented / total * 100 AS coverage_percentage;