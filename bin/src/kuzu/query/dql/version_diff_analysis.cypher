// バージョン間のLocationURI差分分析DQL
// $from_version_id と $to_version_id で差分を取得

// fromバージョンのLocationURI
OPTIONAL MATCH (from_v:VersionState {id: $from_version_id})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(from_l:LocationURI)

// toバージョンのLocationURI
OPTIONAL MATCH (to_v:VersionState {id: $to_version_id})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(to_l:LocationURI)

// 全てのLocationURIを収集
WITH collect(DISTINCT from_l) as from_locations,
     collect(DISTINCT to_l) as to_locations

// 各LocationURIに対して変更タイプを判定
UNWIND (from_locations + to_locations) as location
WHERE location IS NOT NULL

WITH location,
     location IN from_locations as exists_in_from,
     location IN to_locations as exists_in_to

// 変更タイプを決定
WITH location,
     CASE
       WHEN exists_in_from AND NOT exists_in_to THEN 'removed'
       WHEN NOT exists_in_from AND exists_in_to THEN 'added'
       WHEN exists_in_from AND exists_in_to THEN 'modified'
       ELSE 'unknown'
     END as change_type

// 結果を返す
RETURN location.uri_id as uri_id,
       location.scheme as scheme,
       location.authority as authority,
       location.path as path,
       location.fragment as fragment,
       location.query as query,
       change_type
ORDER BY change_type, location.path, location.uri_id
