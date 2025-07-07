// 循環依存の検出
// 要件間の循環依存を検出（問題のある設計を発見）
MATCH (r:RequirementEntity)-[:DEPENDS_ON*]->(r)
RETURN r.id as circular_requirement, 
       r.title,
       'Circular dependency detected' as issue;