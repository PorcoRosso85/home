// add_dependency_template.cypher
// 要件間の依存関係を追加（テンプレート用、循環チェック済み前提）
// パラメータ: child_id, parent_id, dependency_type, reason

MATCH (child:RequirementEntity {id: $child_id})
MATCH (parent:RequirementEntity {id: $parent_id})
CREATE (child)-[:DEPENDS_ON {dependency_type: $dependency_type, reason: $reason}]->(parent)
RETURN child.id AS child_id, parent.id AS parent_id, $dependency_type AS dependency_type, $reason AS reason