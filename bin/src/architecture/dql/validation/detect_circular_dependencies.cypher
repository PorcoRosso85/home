// 循環依存検出クエリ
// 目的: 要件間の循環依存を検出

MATCH path = (req1:RequirementEntity)-[:DEPENDS_ON*]->(req1)
WITH req1, path
RETURN 
    req1.id as circular_requirement_id,
    req1.title as circular_requirement_title,
    [node in nodes(path) | node.id] as cycle_path,
    length(path) as cycle_length
ORDER BY cycle_length;