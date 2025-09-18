// find_dependencies.cypher  
// 指定要件の依存関係を指定深度で検索

MATCH path = (r:RequirementEntity {id: $id})-[:DEPENDS_ON*1..$depth]->(dep:RequirementEntity)
RETURN dep, length(path) as distance
ORDER BY distance