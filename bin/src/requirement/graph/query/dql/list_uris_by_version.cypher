// 特定バージョンのLocationURI一覧を取得するDQL
MATCH (v:VersionState {id: $version_id})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)

RETURN v.id as version_id,
       v.timestamp as version_timestamp,
       v.description as version_description,
       l.id as uri_id
       
ORDER BY l.id ASC
