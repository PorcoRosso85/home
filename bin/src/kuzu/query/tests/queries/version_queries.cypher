// 階層型トレーサビリティモデル - バージョン管理関連クエリ

// 指定したバージョンのlocationuriを一覧で取得するクエリ
// @name: get_locations_by_version
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)-[:HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT l.uri_id, l.scheme, l.path
UNION
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT l.uri_id, l.scheme, l.path
UNION
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_REF]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT l.uri_id, l.scheme, l.path;

// 指定したバージョンの一つ前のバージョンを取得するクエリ
// @name: get_previous_version
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
RETURN prev.id AS previous_version, prev.timestamp, prev.commit_id;

// 指定したバージョンで更新したlocationuriを一覧で取得するクエリ（前バージョンとの差分）
// @name: get_updated_locations_by_version
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_CODE {change_type: $change_type}]->(c:CodeEntity)-[:HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT 'code' AS entity_type, c.persistent_id AS entity_id, c.name, l.uri_id, l.path
UNION
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_REQ {change_type: $change_type}]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT 'requirement' AS entity_type, r.id AS entity_id, r.title, l.uri_id, l.path
UNION
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_REF {change_type: $change_type}]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT 'reference' AS entity_type, ref.id AS entity_id, ref.description, l.uri_id, l.path;

// 設計表：バージョン間の変更を表示するクエリ
// @name: get_design_table
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_CODE {change_type: $change_type}]->(c:CodeEntity)-[:HAS_LOCATION]->(l:LocationURI)
RETURN l.path AS file_path, 
       CASE $change_type 
         WHEN 'added' THEN '新規追加: ' + c.name + ' (' + c.type + ')'
         WHEN 'modified' THEN '更新: ' + c.name + ' (' + c.type + ')'
         WHEN 'deleted' THEN '削除: ' + c.name + ' (' + c.type + ')'
         ELSE c.name + ' (' + c.type + ')'
       END AS change_summary
UNION
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_REQ {change_type: $change_type}]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
RETURN l.path AS file_path,
       CASE $change_type
         WHEN 'added' THEN '新規要件: ' + r.title + ' (' + r.priority + ')'
         WHEN 'modified' THEN '要件更新: ' + r.title + ' (' + r.priority + ')'
         WHEN 'deleted' THEN '要件削除: ' + r.title + ' (' + r.priority + ')'
         ELSE r.title + ' (' + r.priority + ')'
       END AS change_summary;

// 特定バージョンの全ファイルと変更概要一覧
// @name: get_version_changes_summary
MATCH (curr:VersionState {id: $version})
OPTIONAL MATCH (curr)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)-[:HAS_LOCATION]->(l1:LocationURI)
OPTIONAL MATCH (curr)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l2:LocationURI)
OPTIONAL MATCH (curr)-[:TRACKS_STATE_OF_REF]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l3:LocationURI)
WITH l1, l2, l3, c, r, ref
WHERE l1 IS NOT NULL OR l2 IS NOT NULL OR l3 IS NOT NULL
RETURN 
  CASE 
    WHEN l1 IS NOT NULL THEN l1.path
    WHEN l2 IS NOT NULL THEN l2.path
    ELSE l3.path
  END AS file_path,
  CASE
    WHEN c IS NOT NULL THEN 'コード: ' + c.name + ' (' + c.type + ')'
    WHEN r IS NOT NULL THEN '要件: ' + r.title + ' (' + r.requirement_type + ')'
    ELSE '参照: ' + ref.description
  END AS entity_description
ORDER BY file_path;
