// find_dependencies_simple.cypher  
// 指定要件の直接依存関係を検索（深度1固定）

MATCH (r:RequirementEntity {id: $id})-[:DEPENDS_ON]->(dep:RequirementEntity)
RETURN dep.id, dep.title, dep.description, dep.status