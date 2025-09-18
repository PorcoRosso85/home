// TRACKS_STATE_OF_LOCATED_ENTITY関係を作成するクエリ
MATCH (version:VersionState {id: $version_id})
MATCH (location:LocationURI {id: $id})
CREATE (version)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(location)
RETURN version.id as version_id, location.id as id
