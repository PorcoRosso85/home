// 要件影響マトリクスレポート
// 目的: 各要件の変更が他の要件に与える影響を可視化

MATCH (req:RequirementEntity)
OPTIONAL MATCH (req)<-[:DEPENDS_ON]-(dependent:RequirementEntity)
OPTIONAL MATCH (req)-[:DEPENDS_ON]->(dependency:RequirementEntity)
WITH req,
     COUNT(DISTINCT dependent) as dependent_count,
     COUNT(DISTINCT dependency) as dependency_count,
     COLLECT(DISTINCT dependent.id) as dependents,
     COLLECT(DISTINCT dependency.id) as dependencies
RETURN 
    req.id as requirement_id,
    req.title as requirement_title,
    req.status as status,
    dependent_count as impacted_by_count,
    dependency_count as impacts_count,
    dependent_count + dependency_count as total_connections,
    dependents[..5] as sample_dependents,
    dependencies[..5] as sample_dependencies
ORDER BY total_connections DESC;