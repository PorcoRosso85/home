// 指定バージョンの進捗率を計算・更新するクエリ
// 1. 対象バージョンに関連するLocationURIの統計を取得
MATCH (vs:VersionState {id: $version_id})
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)

WITH vs,
     count(loc) as total_locations,
     count(CASE WHEN loc.completed = true THEN 1 END) as completed_locations

// 2. 進捗率を計算
WITH vs, total_locations, completed_locations,
     CASE 
       WHEN total_locations = 0 THEN 0.0
       ELSE CAST(completed_locations AS FLOAT) / CAST(total_locations AS FLOAT)
     END as progress_rate

// 3. VersionStateの進捗率を更新
SET vs.progress_percentage = progress_rate

RETURN vs.id as version_id,
       total_locations,
       completed_locations,
       vs.progress_percentage as progress_percentage
