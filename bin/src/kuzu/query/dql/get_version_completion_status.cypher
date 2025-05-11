// 各バージョンの進捗率と完了済みLocationURI一覧を取得
MATCH (vs:VersionState)
OPTIONAL MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
OPTIONAL MATCH (prevVs:VersionState)-[:FOLLOWS]->(vs)
OPTIONAL MATCH (vs)-[:FOLLOWS]->(nextVs:VersionState)

WITH vs, 
     count(loc) as total_locations,
     count(CASE WHEN loc.completed = true THEN 1 END) as completed_locations,
     collect(CASE WHEN loc.completed = true THEN loc.uri_id END) as completed_uri_list,
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
