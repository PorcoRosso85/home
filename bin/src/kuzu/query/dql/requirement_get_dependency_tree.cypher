// 要件の依存関係ツリー
// 特定要件から辿れる全ての依存関係を再帰的に取得
MATCH path = (r:RequirementEntity {id: $requirementId})-[:DEPENDS_ON*]->(d:RequirementEntity)
RETURN r.id as source, 
       [n IN nodes(path) | n.id] as dependency_chain,
       d.id as target,
       length(path) as depth
ORDER BY depth;