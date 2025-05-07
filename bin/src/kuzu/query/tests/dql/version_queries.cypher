// 階層型トレーサビリティモデル - バージョン管理関連クエリ

// 指定したバージョンのlocationuriを一覧で取得するクエリ
// @name: get_locations_by_version
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)-[:HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT l.uri_id, l.scheme, l.path
UNION
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)-[:REQUIREMENT_HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT l.uri_id, l.scheme, l.path
UNION
// FIXME: 旧名称 "TRACKS_STATE_OF_REF" から "TRACKS_STATE_OF_REFERENCE" に変更。省略形を避けて完全名称に統一
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_REFERENCE]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l:LocationURI)
RETURN DISTINCT l.uri_id, l.scheme, l.path;

// 要件の進捗状況を集計するクエリ
// @name: get_requirement_progress
MATCH (r:RequirementEntity)
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(code:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(ver:RequirementVerification)
WITH r, 
  CASE 
    WHEN code IS NOT NULL AND ver IS NOT NULL THEN 'completed'
    WHEN code IS NOT NULL OR ver IS NOT NULL THEN 'in_progress'
    ELSE 'not_started'
  END AS status
WITH status, count(r) AS count
RETURN status, count
ORDER BY CASE status
  WHEN 'completed' THEN 1
  WHEN 'in_progress' THEN 2
  WHEN 'not_started' THEN 3
  ELSE 4
END;

// モジュール別の進捗状況を分析するクエリ
// @name: get_module_progress
MATCH (mod:LocationURI)<-[:REQUIREMENT_HAS_LOCATION]-(r:RequirementEntity)
WHERE mod.uri_id IN $module_ids OR $module_ids IS NULL
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(code:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(ver:RequirementVerification)
WITH mod.path AS module, r,
  CASE 
    WHEN code IS NOT NULL AND ver IS NOT NULL THEN 'completed'
    WHEN code IS NOT NULL OR ver IS NOT NULL THEN 'in_progress'
    ELSE 'not_started'
  END AS status
WITH module, status, count(r) AS count
WITH module, 
  sum(CASE WHEN status = 'completed' THEN count ELSE 0 END) AS completed,
  sum(CASE WHEN status = 'in_progress' THEN count ELSE 0 END) AS in_progress,
  sum(CASE WHEN status = 'not_started' THEN count ELSE 0 END) AS not_started,
  sum(count) AS total
RETURN 
  module,
  completed,
  in_progress,
  not_started,
  total
ORDER BY module;

// 優先度による進捗状況分析クエリ
// @name: get_priority_progress
MATCH (r:RequirementEntity)
WHERE r.priority IN $priorities OR $priorities IS NULL
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(code:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(ver:RequirementVerification)
WITH r.priority AS priority, r,
  CASE 
    WHEN code IS NOT NULL AND ver IS NOT NULL THEN 'completed'
    WHEN code IS NOT NULL OR ver IS NOT NULL THEN 'in_progress'
    ELSE 'not_started'
  END AS status
WITH priority, status, count(r) AS count
WITH priority, 
  sum(CASE WHEN status = 'completed' THEN count ELSE 0 END) AS completed,
  sum(CASE WHEN status = 'in_progress' THEN count ELSE 0 END) AS in_progress,
  sum(CASE WHEN status = 'not_started' THEN count ELSE 0 END) AS not_started,
  sum(count) AS total
RETURN 
  priority,
  completed,
  in_progress,
  not_started,
  total
ORDER BY CASE priority
  WHEN 'high' THEN 1
  WHEN 'medium' THEN 2
  WHEN 'low' THEN 3
  ELSE 4
END;

// 検証の進捗状況分析クエリ
// @name: get_verification_progress
MATCH (v:RequirementVerification)
OPTIONAL MATCH (v)-[:VERIFICATION_IS_IMPLEMENTED_BY]->(c:CodeEntity)
WITH v, 
  CASE 
    WHEN c IS NOT NULL THEN 'passed'
    ELSE 'not_started'
  END AS status
WITH status, count(v) AS count
RETURN status, count
ORDER BY CASE status
  WHEN 'passed' THEN 1
  WHEN 'in_progress' THEN 2
  WHEN 'not_started' THEN 3
  ELSE 4
END;

// コード実装の進捗状況分析クエリ
// @name: get_code_progress
MATCH (c:CodeEntity)
WITH c, 
  CASE 
    WHEN c.complexity > 5 THEN 'completed'
    WHEN c.complexity > 3 THEN 'in_progress'
    ELSE 'not_started'
  END AS status
WITH status, count(c) AS count
RETURN status, count
ORDER BY CASE status
  WHEN 'completed' THEN 1
  WHEN 'in_progress' THEN 2
  WHEN 'not_started' THEN 3
  ELSE 4
END;

// 要件の完了率クエリ
// @name: get_requirement_completion_rate
MATCH (r:RequirementEntity)
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(code:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(ver:RequirementVerification)
WITH r,
  CASE 
    WHEN code IS NOT NULL AND ver IS NOT NULL THEN 'completed'
    WHEN code IS NOT NULL OR ver IS NOT NULL THEN 'in_progress'
    ELSE 'not_started'
  END AS status
RETURN 
  count(r) AS total_requirements,
  sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_requirements,
  1.0 * sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / count(r) * 100 AS requirements_completion_rate,
  sum(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress_requirements,
  sum(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) AS not_started_requirements;

// 検証の完了率クエリ
// @name: get_verification_completion_rate
MATCH (v:RequirementVerification)
OPTIONAL MATCH (v)-[:VERIFICATION_IS_IMPLEMENTED_BY]->(c:CodeEntity)
WITH v, 
  CASE 
    WHEN c IS NOT NULL THEN 'passed'
    ELSE 'not_started'
  END AS status
RETURN 
  count(v) AS total_verifications,
  sum(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) AS passed_verifications,
  1.0 * sum(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) / count(v) * 100 AS verification_pass_rate,
  0 AS in_progress_verifications,
  sum(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) AS not_started_verifications;

// コード実装の完了率クエリ
// @name: get_code_completion_rate
MATCH (c:CodeEntity)
WITH c, 
  CASE 
    WHEN c.complexity > 5 THEN 'completed'
    WHEN c.complexity > 3 THEN 'in_progress'
    ELSE 'not_started'
  END AS status
RETURN 
  count(c) AS total_code,
  sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_code,
  1.0 * sum(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / count(c) * 100 AS code_completion_rate,
  sum(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress_code,
  sum(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) AS not_started_code;

// トレーサビリティの状況クエリ
// @name: get_traceability_status
MATCH (r:RequirementEntity)
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(v:RequirementVerification)

WITH 
  count(r) AS total_requirements,
  count(DISTINCT r) - count(DISTINCT CASE WHEN c IS NULL THEN null ELSE r END) AS requirements_without_code,
  count(DISTINCT r) - count(DISTINCT CASE WHEN v IS NULL THEN null ELSE r END) AS requirements_without_verification,
  count(DISTINCT CASE WHEN c IS NOT NULL AND v IS NOT NULL THEN r ELSE null END) AS requirements_with_both

RETURN 
  total_requirements,
  requirements_without_code,
  requirements_without_verification,
  requirements_with_both,
  1.0 * requirements_with_both / total_requirements * 100 AS full_traceability_rate;

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
// FIXME: 旧名称 "TRACKS_STATE_OF_REF" から "TRACKS_STATE_OF_REFERENCE" に変更。省略形を避けて完全名称に統一
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (curr)-[:TRACKS_STATE_OF_REFERENCE]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (prev)-[:TRACKS_STATE_OF_REFERENCE]->(ref)
}
AND $change_type = 'added'
RETURN DISTINCT 'reference' AS entity_type, ref.id AS entity_id, ref.description, l.uri_id, l.path

UNION

// 参照の差分 - 削除
// FIXME: 旧名称 "TRACKS_STATE_OF_REF" から "TRACKS_STATE_OF_REFERENCE" に変更。省略形を避けて完全名称に統一
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_REFERENCE]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l:LocationURI)
WHERE NOT EXISTS {
  MATCH (curr)-[:TRACKS_STATE_OF_REFERENCE]->(ref)
}
AND $change_type = 'deleted'
RETURN DISTINCT 'reference' AS entity_type, ref.id AS entity_id, ref.description, l.uri_id, l.path

UNION

// 参照の差分 - 変更
// FIXME: 旧名称 "TRACKS_STATE_OF_REF" から "TRACKS_STATE_OF_REFERENCE" に変更。省略形を避けて完全名称に統一
MATCH (prev:VersionState)-[:FOLLOWS]->(curr:VersionState {id: $version})
MATCH (prev)-[:TRACKS_STATE_OF_REFERENCE]->(ref:ReferenceEntity)
MATCH (curr)-[:TRACKS_STATE_OF_REFERENCE]->(ref)
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
// FIXME: 旧名称 "TRACKS_STATE_OF_REF" から "TRACKS_STATE_OF_REFERENCE" に変更。省略形を避けて完全名称に統一
OPTIONAL MATCH (curr)-[:TRACKS_STATE_OF_REFERENCE]->(ref:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(l3:LocationURI)
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
