// 優先度別の要件取得
// 特定優先度の要件を実装状態と共に取得
MATCH (r:RequirementEntity)
WHERE r.priority = $priority
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(t:CodeEntity)
RETURN r.id, r.title, r.description, r.priority,
       EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) as is_implemented,
       EXISTS((r)-[:IS_VERIFIED_BY]->()) as is_tested,
       count(DISTINCT c) as implementation_count,
       count(DISTINCT t) as test_count
ORDER BY r.id;