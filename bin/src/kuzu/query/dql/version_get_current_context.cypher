// 現在アクティブなバージョンのコンテキスト取得
// 最新の未完了バージョンとその進捗状況を取得
MATCH (vs:VersionState)
WHERE vs.progress_percentage < 1.0
WITH vs ORDER BY vs.timestamp DESC LIMIT 1
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
OPTIONAL MATCH (loc)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
WITH vs, 
     count(DISTINCT r) as total,
     sum(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) THEN 1 ELSE 0 END) as completed,
     sum(CASE 
       WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) 
       AND NOT EXISTS((r)-[:IS_VERIFIED_BY]->()) 
       THEN 1 ELSE 0 
     END) as in_progress
RETURN vs.id as id,
       vs.description as description,
       vs.timestamp as timestamp,
       vs.progress_percentage as progress_percentage,
       total,
       completed,
       in_progress;