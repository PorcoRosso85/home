// バージョン詳細情報を取得
// REFACTORED: completed プロパティ削除に伴い、progress_percentage ベースに変更
OPTIONAL MATCH (vs:VersionState)
OPTIONAL MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)

WITH vs,
     count(loc) as total_locations,
     CAST(count(loc) * COALESCE(vs.progress_percentage, 0.0) AS INT64) as completed_locations,
     CAST(count(loc) * (1.0 - COALESCE(vs.progress_percentage, 0.0)) AS INT64) as incomplete_locations

WHERE vs IS NOT NULL

RETURN vs.id as version_id,
       total_locations as total,
       completed_locations as completed,
       incomplete_locations as incomplete,
       COALESCE(vs.progress_percentage, 0.0) as progress
ORDER BY vs.id
