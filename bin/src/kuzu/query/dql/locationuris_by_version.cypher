// 特定バージョンのLocationURI一覧を取得するDQL
MATCH (v:VersionState {id: $version_id})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)

RETURN v.id as version_id,
       v.timestamp as version_timestamp,
       v.description as version_description,
       l.uri_id as uri_id,
       l.scheme as scheme,
       l.authority as authority,
       l.path as path,
       l.fragment as fragment,
       l.query as query
ORDER BY l.path ASC, l.uri_id ASC
