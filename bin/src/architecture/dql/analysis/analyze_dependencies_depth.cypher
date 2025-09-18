// 依存関係の深さ分析クエリ
// 目的: 各要件の依存関係の深さを分析し、複雑度を把握

MATCH path = (req:RequirementEntity)-[:DEPENDS_ON*]->(dep:RequirementEntity)
WHERE NOT (dep)-[:DEPENDS_ON]->()
WITH req, dep, length(path) as depth
RETURN 
    req.id as requirement_id,
    req.title as requirement_title,
    MAX(depth) as max_dependency_depth,
    COUNT(DISTINCT dep) as total_dependencies
ORDER BY max_dependency_depth DESC, total_dependencies DESC;