// 未実装要件の優先度付き一覧
// 実装が必要な要件を優先度順に取得
MATCH (r:RequirementEntity)
WHERE NOT EXISTS {
  MATCH (r)-[:IS_IMPLEMENTED_BY]->()
}
RETURN r.id, r.title, r.priority, r.description
ORDER BY 
  CASE r.priority 
    WHEN 'high' THEN 1 
    WHEN 'medium' THEN 2 
    WHEN 'low' THEN 3 
    ELSE 4 
  END,
  r.id;