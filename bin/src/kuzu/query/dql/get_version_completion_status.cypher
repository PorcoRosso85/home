// 各バージョンの進捗率とLocationURI一覧を取得
// REFACTORED: completed プロパティ削除に伴い、progress_percentage ベースに変更
MATCH (vs:VersionState)
OPTIONAL MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
OPTIONAL MATCH (prevVs:VersionState)-[:FOLLOWS]->(vs)
OPTIONAL MATCH (vs)-[:FOLLOWS]->(nextVs:VersionState)

WITH vs, 
     count(loc) as total_locations,
     CAST(count(loc) * COALESCE(vs.progress_percentage, 0.0) AS INT64) as completed_locations,
     collect(loc.id) as completed_uri_list,
     prevVs.id as previous_version,
     nextVs.id as next_version

RETURN vs.id as version_id,
       vs.timestamp as timestamp,
       vs.description as description,
       vs.progress_percentage as progress_percentage,
       total_locations,
       completed_locations,
       completed_uri_list,
       previous_version,
       next_version
ORDER BY vs.timestamp ASC
