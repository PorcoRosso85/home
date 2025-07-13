// get_dependencies.cypher
// 全依存関係の取得（循環チェック用）

MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(dep:RequirementEntity)
RETURN r.id as from_id, dep.id as to_id