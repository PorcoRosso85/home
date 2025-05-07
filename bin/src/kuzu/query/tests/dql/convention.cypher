// 階層型トレーサビリティモデル - CONVENTION規約用DQL
// CONVENTION.yamlを削除しても利用可能な規約検索クエリ

// ===== 規約の基本検索クエリ =====

// 1. すべての規約ルールを取得
// @name: get_all_convention_rules
MATCH (r:ReferenceEntity)
WHERE r.type = 'CONVENTION_RULE'
RETURN r.id AS rule_id,
       r.description AS rule_description,
       r.type AS rule_type,
       r.source_type AS source_type
ORDER BY r.id;

// 2. 特定IDの規約ルールを取得
// @name: get_convention_rule_by_id
MATCH (r:ReferenceEntity {id: $rule_id})
WHERE r.type = 'CONVENTION_RULE'
OPTIONAL MATCH (r)-[:REFERENCE_HAS_LOCATION]->(loc:LocationURI)
RETURN r.id AS rule_id,
       r.description AS rule_description,
       loc.fragment AS rule_path,
       loc.uri_id AS location_id
LIMIT 1;

// ===== 階層構造検索クエリ =====

// 3. 規約のルート階層を取得
// @name: get_convention_root_hierarchy
MATCH (root:LocationURI {uri_id: 'convention:root'})
MATCH (root)-[:CONTAINS_LOCATION]->(category:LocationURI)
OPTIONAL MATCH (category)<-[:REFERENCE_HAS_LOCATION]-(r:ReferenceEntity)
RETURN category.uri_id AS category_id,
       category.fragment AS category_name,
       r.id AS rule_id,
       r.description AS rule_description
ORDER BY category.fragment;

// 4. 特定カテゴリに属する規約を取得
// @name: get_rules_by_category
MATCH (cat:LocationURI)
WHERE cat.fragment = $category_name
MATCH path = (cat)-[:CONTAINS_LOCATION*]->(child:LocationURI)
MATCH (child)<-[:REFERENCE_HAS_LOCATION]-(rule:ReferenceEntity)
RETURN rule.id AS rule_id,
       rule.description AS rule_description,
       child.fragment AS full_path
ORDER BY child.fragment;

// 5. 規約の階層構造を取得
// @name: get_convention_hierarchy
MATCH path = (root:LocationURI {uri_id: 'convention:root'})-[:CONTAINS_LOCATION*]->(leaf:LocationURI)
OPTIONAL MATCH (leaf)<-[:REFERENCE_HAS_LOCATION]-(rule:ReferenceEntity)
WITH path, leaf, rule,
     [node IN nodes(path) | node.fragment] AS hierarchy_path
RETURN hierarchy_path,
       leaf.uri_id AS leaf_id,
       rule.id AS rule_id,
       rule.description AS rule_description
ORDER BY size(hierarchy_path), hierarchy_path;

// ===== フラグメント検索クエリ =====

// 6. キーワードによる規約検索
// @name: search_convention_by_keyword
MATCH (rule:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(loc:LocationURI)
WHERE rule.type = 'CONVENTION_RULE'
  AND (
    rule.description CONTAINS $keyword
    OR loc.fragment CONTAINS $keyword
  )
RETURN rule.id AS rule_id,
       rule.description AS rule_description,
       loc.fragment AS rule_path
ORDER BY rule.id;

// 7. フラグメントパスによる規約検索
// @name: search_convention_by_path
MATCH (loc:LocationURI)
WHERE loc.fragment LIKE $path_pattern
MATCH (loc)<-[:REFERENCE_HAS_LOCATION]-(rule:ReferenceEntity)
RETURN rule.id AS rule_id,
       rule.description AS rule_description,
       loc.fragment AS full_path
ORDER BY loc.fragment;

// ===== 規約適用のクエリ =====

// 8. 特定コードが適用している規約を取得
// @name: get_conventions_for_code
MATCH (code:CodeEntity {persistent_id: $code_id})
MATCH (code)-[:REFERS_TO {ref_type: 'CONVENTION'}]->(rule:ReferenceEntity)
OPTIONAL MATCH (rule)-[:REFERENCE_HAS_LOCATION]->(loc:LocationURI)
RETURN rule.id AS rule_id,
       rule.description AS rule_description,
       loc.fragment AS rule_path
ORDER BY rule.id;

// 9. 特定の規約が適用されているコードを取得
// @name: get_code_using_convention
MATCH (rule:ReferenceEntity {id: $rule_id})
MATCH (code:CodeEntity)-[:REFERS_TO {ref_type: 'CONVENTION'}]->(rule)
OPTIONAL MATCH (code)-[:HAS_LOCATION]->(loc:LocationURI)
RETURN code.persistent_id AS code_id,
       code.name AS code_name,
       code.type AS code_type,
       loc.path AS code_location
ORDER BY code.name;

// 10. 規約適用の集計
// @name: count_convention_usage
MATCH (rule:ReferenceEntity)
WHERE rule.type = 'CONVENTION_RULE'
OPTIONAL MATCH (code:CodeEntity)-[:REFERS_TO {ref_type: 'CONVENTION'}]->(rule)
WITH rule, count(code) AS usage_count
MATCH (rule)-[:REFERENCE_HAS_LOCATION]->(loc:LocationURI)
RETURN rule.id AS rule_id,
       rule.description AS rule_description,
       loc.fragment AS rule_path,
       usage_count
ORDER BY usage_count DESC, rule.id;

// ===== バージョン管理クエリ =====

// 11. 特定バージョンの規約を取得
// @name: get_convention_by_version
MATCH (version:VersionState {id: $version_id})
MATCH (version)-[:TRACKS_STATE_OF_REFERENCE]->(rule:ReferenceEntity)
WHERE rule.type = 'CONVENTION_RULE'
OPTIONAL MATCH (rule)-[:REFERENCE_HAS_LOCATION]->(loc:LocationURI)
RETURN rule.id AS rule_id,
       rule.description AS rule_description,
       loc.fragment AS rule_path
ORDER BY rule.id;

// 12. バージョン間の規約変更を追跡
// @name: track_convention_changes
MATCH (old_version:VersionState {id: $old_version_id})
MATCH (new_version:VersionState {id: $new_version_id})
MATCH (old_version)-[:TRACKS_STATE_OF_REFERENCE]->(old_rule:ReferenceEntity)
WHERE old_rule.type = 'CONVENTION_RULE'
OPTIONAL MATCH (new_version)-[:TRACKS_STATE_OF_REFERENCE]->(new_rule:ReferenceEntity)
WHERE new_rule.id = old_rule.id
OPTIONAL MATCH (old_rule)-[:REFERENCE_HAS_LOCATION]->(old_loc:LocationURI)
OPTIONAL MATCH (new_rule)-[:REFERENCE_HAS_LOCATION]->(new_loc:LocationURI)
WITH old_rule, new_rule, old_loc, new_loc,
     CASE
       WHEN new_rule IS NULL THEN 'DELETED'
       WHEN old_rule.description <> new_rule.description THEN 'MODIFIED'
       WHEN old_loc.fragment <> new_loc.fragment THEN 'RELOCATED'
       ELSE 'UNCHANGED'
     END AS change_type
WHERE change_type <> 'UNCHANGED'
RETURN old_rule.id AS rule_id,
       old_rule.description AS old_description,
       new_rule.description AS new_description,
       old_loc.fragment AS old_path,
       new_loc.fragment AS new_path,
       change_type
ORDER BY change_type, rule_id;

// ===== 高度なクエリ =====

// 13. 規約階層のレベル別集計
// @name: count_rules_by_level
MATCH (loc:LocationURI)
WHERE loc.scheme = 'convention'
WITH loc.fragment AS path
WITH 
  CASE 
    WHEN path IS NULL THEN 0 
    WHEN NOT contains(path, '.') THEN 1
    ELSE 2
  END AS hierarchy_level
RETURN hierarchy_level, count(*) AS locations
ORDER BY hierarchy_level;

// 14. 関連規約の提案
// @name: suggest_related_conventions
MATCH (rule:ReferenceEntity {id: $rule_id})
MATCH (rule)-[:REFERENCE_HAS_LOCATION]->(rule_loc:LocationURI)
WITH rule, split(rule_loc.fragment, '.') AS path_parts
MATCH (other_rule:ReferenceEntity)-[:REFERENCE_HAS_LOCATION]->(other_loc:LocationURI)
WHERE other_rule.id <> rule.id
  AND other_rule.type = 'CONVENTION_RULE'
WITH rule, other_rule, path_parts, split(other_loc.fragment, '.') AS other_parts,
     size([x IN path_parts WHERE x IN other_parts]) AS common_parts
WHERE common_parts > 0
RETURN other_rule.id AS related_rule_id,
       other_rule.description AS related_rule_description,
       other_loc.fragment AS related_rule_path,
       common_parts AS similarity_score
ORDER BY similarity_score DESC, other_rule.id
LIMIT 5;

// 15. 規約適用状況のサマリー
// @name: get_convention_compliance_summary
MATCH (rule:ReferenceEntity)
WHERE rule.type = 'CONVENTION_RULE'
OPTIONAL MATCH (code:CodeEntity)-[:REFERS_TO {ref_type: 'CONVENTION'}]->(rule)
WITH count(DISTINCT rule) AS total_rules,
     count(DISTINCT code) AS total_compliant_code,
     count(DISTINCT rule) - count(DISTINCT CASE WHEN code IS NULL THEN null ELSE rule END) AS unused_rules,
     collect(DISTINCT CASE WHEN code IS NULL THEN rule.id ELSE null END) AS unused_rule_ids
RETURN total_rules,
       total_compliant_code,
       unused_rules,
       unused_rules * 100.0 / total_rules AS unused_percentage,
       unused_rule_ids;
