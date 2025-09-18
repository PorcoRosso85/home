// 実装順序の最適化
// 依存関係を考慮した実装順序の提案
MATCH (r:RequirementEntity)
WHERE NOT EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
OPTIONAL MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
WITH r, 
     count(dep) as dependency_count,
     sum(CASE WHEN EXISTS((dep)-[:IS_IMPLEMENTED_BY]->()) THEN 0 ELSE 1 END) as unimplemented_deps
RETURN r.id, r.title, r.priority,
       dependency_count,
       unimplemented_deps,
       CASE 
         WHEN unimplemented_deps = 0 THEN 'ready'
         ELSE 'blocked'
       END as status
ORDER BY 
  unimplemented_deps ASC,
  CASE r.priority 
    WHEN 'high' THEN 1 
    WHEN 'medium' THEN 2 
    WHEN 'low' THEN 3 
    ELSE 4 
  END,
  dependency_count ASC;