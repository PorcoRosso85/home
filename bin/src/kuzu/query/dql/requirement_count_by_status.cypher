// 要件の状態別カウント
// 優先度ごとに実装・テスト状態を集計
MATCH (r:RequirementEntity)
RETURN r.priority,
       count(*) as total,
       sum(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) THEN 1 ELSE 0 END) as implemented,
       sum(CASE WHEN EXISTS((r)-[:IS_VERIFIED_BY]->()) THEN 1 ELSE 0 END) as tested,
       sum(CASE 
         WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) AND EXISTS((r)-[:IS_VERIFIED_BY]->()) THEN 1 
         ELSE 0 
       END) as fully_completed
ORDER BY 
  CASE r.priority 
    WHEN 'high' THEN 1 
    WHEN 'medium' THEN 2 
    WHEN 'low' THEN 3 
    ELSE 4 
  END;