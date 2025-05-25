// 全バージョンの進捗率サマリーを時系列で取得
// REFACTORED: completed プロパティ削除に伴い、progress_percentage ベースに変更
OPTIONAL MATCH (vs:VersionState)
OPTIONAL MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)

WITH vs,
     count(loc) as total_locations,
     CAST(count(loc) * COALESCE(vs.progress_percentage, 0.0) AS INT64) as completed_locations,
     CASE 
       WHEN vs IS NULL THEN 'unknown'
       WHEN COALESCE(vs.progress_percentage, 0.0) = 1.0 THEN 'completed'
       WHEN COALESCE(vs.progress_percentage, 0.0) = 0.0 THEN 'not_started'
       WHEN COALESCE(vs.progress_percentage, 0.0) > 0.0 THEN 'in_progress'
       ELSE 'unknown'
     END as completion_status

WHERE vs IS NOT NULL

RETURN vs.id as version_id,
       COALESCE(vs.timestamp, '') as timestamp,
       COALESCE(vs.description, '') as description,
       COALESCE(vs.progress_percentage, 0.0) as progress_percentage,
       total_locations,
       completed_locations,
       completion_status
ORDER BY vs.timestamp ASC
