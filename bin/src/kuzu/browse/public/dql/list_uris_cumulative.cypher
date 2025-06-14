// 指定バージョンまでのLocationURIを取得（append-only対応）
// 各LocationURIの最新状態を取得し、DELETEされたものを除外
WITH $version_id as target_version
MATCH (target:VersionState {id: target_version})
MATCH (v:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
WHERE v.timestamp <= target.timestamp
// より新しい変更がないことを確認
AND NOT EXISTS {
  MATCH (v2:VersionState)-[r2:TRACKS_STATE_OF_LOCATED_ENTITY]->(l)
  WHERE v2.timestamp > v.timestamp 
  AND v2.timestamp <= target.timestamp
}
// DELETEされたものを除外
AND r.change_type != 'DELETE'
RETURN l.id as id,
       l.id as uri_id,
       v.id as from_version,
       v.description as version_description,
       r.change_type as change_type
ORDER BY l.id ASC
