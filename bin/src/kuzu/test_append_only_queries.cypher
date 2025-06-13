-- 1. 各バージョンの変更タイプ別集計
MATCH (v:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(:LocationURI)
RETURN v.version_id, r.change_type, count(*) as count
ORDER BY v.version_id, r.change_type;

-- 2. v1.2.0時点のアクティブなファイル
WITH 'v1.2.0' as target_version
MATCH (target:VersionState {version_id: target_version})
MATCH (v:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
WHERE v.timestamp <= target.timestamp
AND NOT EXISTS {
  MATCH (v2:VersionState)-[r2:TRACKS_STATE_OF_LOCATED_ENTITY]->(l)
  WHERE v2.timestamp > v.timestamp 
  AND v2.timestamp <= target.timestamp
}
AND r.change_type != 'DELETE'
RETURN count(l) as active_files;

-- 3. main.tsの変更履歴
MATCH (v:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
WHERE l.id CONTAINS 'main.ts'
RETURN v.version_id, l.id, r.change_type, v.timestamp
ORDER BY v.timestamp;
