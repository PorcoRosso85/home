// 実装可能な要件の取得
// 依存関係が解決済みで実装可能な要件をバッチ取得
MATCH (r:RequirementEntity)
WHERE NOT EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
  AND NOT EXISTS {
    MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
    WHERE NOT EXISTS((dep)-[:IS_IMPLEMENTED_BY]->())
  }
RETURN r.id, r.title, r.description, r.priority,
       r.estimated_hours as estimated_hours
ORDER BY 
  CASE r.priority 
    WHEN 'high' THEN 1 
    WHEN 'medium' THEN 2 
    WHEN 'low' THEN 3 
    ELSE 4 
  END
LIMIT $batchSize;