// バージョンに関連する次のタスク候補
// 指定バージョンの未実装要件を依存関係と優先度で並び替え
MATCH (vs:VersionState {id: $versionId})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
WHERE NOT EXISTS((r)-[:IS_IMPLEMENTED_BY]->())
OPTIONAL MATCH (r)-[:DEPENDS_ON]->(dep:RequirementEntity)
WHERE NOT EXISTS((dep)-[:IS_IMPLEMENTED_BY]->())
WITH r, loc, collect(dep.id) as blocked_by
RETURN r.id as req_id,
       r.title as req_title, 
       r.description as req_description,
       r.priority as req_priority,
       loc.id as location_uri,
       blocked_by,
       CASE 
         WHEN size(blocked_by) = 0 THEN 'ready' 
         ELSE 'blocked' 
       END as status,
       CASE 
         WHEN size(blocked_by) = 0 AND r.priority = 'high' THEN '最優先度の未実装要件'
         WHEN size(blocked_by) = 0 AND r.priority = 'medium' THEN '中優先度の実装可能要件'
         WHEN size(blocked_by) = 0 THEN '実装可能な要件'
         ELSE size(blocked_by) + '個の要件に依存中'
       END as reason
ORDER BY 
  CASE WHEN size(blocked_by) = 0 THEN 0 ELSE 1 END,
  CASE r.priority 
    WHEN 'high' THEN 1 
    WHEN 'medium' THEN 2 
    WHEN 'low' THEN 3 
  END,
  r.id;