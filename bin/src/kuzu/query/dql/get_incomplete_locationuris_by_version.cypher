// 指定バージョンの未完了LocationURI一覧を取得
MATCH (vs:VersionState {id: $version_id})
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)
WHERE loc.completed = false OR loc.completed IS NULL

WITH loc,
     vs.id as version_id,
     vs.description as version_description

RETURN version_id,
       version_description,
       loc.id as id,
       loc.completed as is_completed
ORDER BY loc.id
