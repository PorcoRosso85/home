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
// 新規追加されたエンティティ（前バージョンには存在しないが現バージョンに存在するエンティティ）を取得
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)-[:HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (prev)-[:TRACKS_STATE_OF_CODE]->(c)
}
AND $change_type = 'added'
RETURN DISTINCT 'code' AS entity_type, c.persistent_id AS entity_id, c.name, l.uri_id, l.path

UNION

// 削除されたエンティティ（前バージョンには存在するが現バージョンには存在しないか、特別な削除マーカーがあるエンティティ）を取得
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)-[:HAS_LOCATION]->(l:LocationURI)
WHERE (
  NOT EXISTS { MATCH (curr)-[:TRACKS_STATE_OF_CODE]->(c) }
  OR EXISTS { MATCH (curr)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity) WHERE c.name CONTAINS '_v' }
)
AND $change_type = 'deleted'
RETURN DISTINCT 'code' AS entity_type, c.persistent_id AS entity_id, c.name, l.uri_id, l.path

UNION

// 変更されたエンティティ（前バージョンにも現バージョンにも存在するが変更されたエンティティ）を取得
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)
MATCH (curr)-[:TRACKS_STATE_OF_CODE]->(c)
MATCH (c)-[:HAS_LOCATION]->(l:LocationURI)
WHERE $change_type = 'modified'
RETURN DISTINCT 'code' AS entity_type, c.persistent_id AS entity_id, c.name, l.uri_id, l.path

UNION

// 要件の差分 - 新規追加
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (prev)-[:TRACKS_STATE_OF_REQ]->(r)
}
AND $change_type = 'added'
RETURN DISTINCT 'requirement' AS entity_type, r.id AS entity_id, r.title, l.uri_id, l.path

UNION

// 要件の差分 - 削除
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (curr)-[:TRACKS_STATE_OF_REQ]->(r)
}
AND $change_type = 'deleted'
RETURN DISTINCT 'requirement' AS entity_type, r.id AS entity_id, r.title, l.uri_id, l.path

UNION

// 要件の差分 - 変更
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)
MATCH (curr)-[:TRACKS_STATE_OF_REQ]->(r)
MATCH (r)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
WHERE $change_type = 'modified'
RETURN DISTINCT 'requirement' AS entity_type, r.id AS entity_id, r.title, l.uri_id, l.path

UNION

// 参照の差分 - 新規追加
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_REF]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (prev)-[:TRACKS_STATE_OF_REF]->(ref)
}
AND $change_type = 'added'
RETURN DISTINCT 'reference' AS entity_type, ref.id AS entity_id, ref.description, l.uri_id, l.path

UNION

// 参照の差分 - 削除
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_REF]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (curr)-[:TRACKS_STATE_OF_REF]->(ref)
}
AND $change_type = 'deleted'
RETURN DISTINCT 'reference' AS entity_type, ref.id AS entity_id, ref.description, l.uri_id, l.path

UNION

// 参照の差分 - 変更
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_REF]->(ref:ReferenceEntity)
MATCH (curr)-[:TRACKS_STATE_OF_REF]->(ref)
MATCH (ref)-[:REFERENCE_HAS_LOCATION]->(l:LocationURI)
WHERE $change_type = 'modified'
RETURN DISTINCT 'reference' AS entity_type, ref.id AS entity_id, ref.description, l.uri_id, l.path;

// 設計表：バージョン間の変更を表示するクエリ
// @name: get_design_table
// 新規追加されたコード
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)-[:HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (prev)-[:TRACKS_STATE_OF_CODE]->(c)
}
AND $change_type = 'added'
RETURN l.path AS file_path, '新規追加: ' + c.name + ' (' + c.type + ')' AS change_summary

UNION

// 変更されたコード
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)
MATCH (curr)-[:TRACKS_STATE_OF_CODE]->(c)-[:HAS_LOCATION]->(l:LocationURI)
WHERE $change_type = 'modified'
RETURN l.path AS file_path, '更新: ' + c.name + ' (' + c.type + ')' AS change_summary

UNION

// 削除されたコード
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)-[:HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (curr)-[:TRACKS_STATE_OF_CODE]->(c)
}
AND $change_type = 'deleted'
RETURN l.path AS file_path, '削除: ' + c.name + ' (' + c.type + ')' AS change_summary

UNION

// 新規追加された要件
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (prev)-[:TRACKS_STATE_OF_REQ]->(r)
}
AND $change_type = 'added'
RETURN l.path AS file_path, '新規要件: ' + r.title + ' (' + r.priority + ')' AS change_summary

UNION

// 変更された要件
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)
MATCH (curr)-[:TRACKS_STATE_OF_REQ]->(r)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
WHERE $change_type = 'modified'
RETURN l.path AS file_path, '要件更新: ' + r.title + ' (' + r.priority + ')' AS change_summary

UNION

// 削除された要件
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (curr)-[:TRACKS_STATE_OF_REQ]->(r)
}
AND $change_type = 'deleted'
RETURN l.path AS file_path, '要件削除: ' + r.title + ' (' + r.priority + ')' AS change_summary;

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
