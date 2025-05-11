// バージョン詳細情報を取得
OPTIONAL MATCH (vs:VersionState)
OPTIONAL MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)

WITH vs,
     count(loc) as total_locations,
     count(CASE WHEN loc.completed = true THEN 1 END) as completed_locations,
     count(CASE WHEN loc.completed = false OR loc.completed IS NULL THEN 1 END) as incomplete_locations

WHERE vs IS NOT NULL

RETURN vs.id as version_id,
       total_locations as total,
       completed_locations as completed,
       incomplete_locations as incomplete,
       COALESCE(vs.progress_percentage, 0.0) as progress
ORDER BY vs.id
