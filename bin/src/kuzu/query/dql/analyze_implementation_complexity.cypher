// 実装の複雑度と要件の関係
// 複雑な実装を持つ要件を特定
MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
WHERE c.complexity > $complexityThreshold
RETURN r.id, r.title,
       avg(c.complexity) as avg_complexity,
       count(c) as implementation_count,
       collect({name: c.name, complexity: c.complexity}) as complex_implementations
ORDER BY avg_complexity DESC;