// 指定バージョンの未完了LocationURI一覧を取得
MATCH (vs:VersionState {id: $version_id})
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
WHERE loc.completed = false OR loc.completed IS NULL

WITH loc,
     vs.id as version_id,
     vs.description as version_description

RETURN version_id,
       version_description,
       loc.uri_id as uri_id,
       loc.scheme as scheme,
       loc.authority as authority,
       loc.path as path,
       loc.fragment as fragment,
       loc.query as query,
       loc.completed as is_completed
ORDER BY loc.uri_id
