// add_dependency.cypher
// 要件間の依存関係を追加（循環チェック済み前提）

MATCH (child:RequirementEntity {id: $child_id})
MATCH (parent:RequirementEntity {id: $parent_id})
CREATE (child)-[:DEPENDS_ON]->(parent)
RETURN child, parent