// 指定バージョンのLocationURI一覧を取得
// REFACTORED: completed プロパティ削除に伴い、全LocationURIを返すように変更
// progress_percentage により完了状況は管理される
MATCH (vs:VersionState {id: $version_id})
MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)

WITH loc,
     vs.id as version_id,
     vs.description as version_description,
     vs.progress_percentage as progress_percentage

RETURN version_id,
       version_description,
       progress_percentage,
       loc.id as id
ORDER BY loc.id
