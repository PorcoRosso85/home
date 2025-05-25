// 指定バージョンの進捗率を取得するクエリ
// REFACTORED: completed プロパティ削除に伴い、progress_percentage ベースに変更
MATCH (vs:VersionState {id: $version_id})
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)

WITH vs,
     count(loc) as total_locations

RETURN vs.id as version_id,
       total_locations,
       CAST(total_locations * COALESCE(vs.progress_percentage, 0.0) AS INT64) as completed_locations,
       COALESCE(vs.progress_percentage, 0.0) as progress_percentage
