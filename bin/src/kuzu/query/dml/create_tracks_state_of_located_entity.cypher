// TRACKS_STATE_OF_LOCATED_ENTITY関係を作成するクエリ
MATCH (version:VersionState {id: $version_id})
MATCH (location:LocationURI {uri_id: $uri_id})
CREATE (version)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(location)
RETURN version.id as version_id, location.uri_id as uri_id
