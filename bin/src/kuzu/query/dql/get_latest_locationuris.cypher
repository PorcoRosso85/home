// 各LocationURIの最新バージョンを取得するDQL
// REFACTORED: 最小化されたスキーマに対応

// 各LocationURIについて、最後に関連付けられたバージョンを特定
MATCH (v:VersionState)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)

// 各LocationURIについて最新のバージョンを取得
WITH l.id as id, 
     l.completed as completed,
     max(v.timestamp) as latest_timestamp,
     collect({version_id: v.id, timestamp: v.timestamp, description: v.description}) as all_versions

// 最新タイムスタンプに一致するバージョン情報を取得
WITH id, completed, latest_timestamp,
     [version IN all_versions WHERE version.timestamp = latest_timestamp][0] as latest_version

RETURN id,
       completed,
       latest_version.version_id as latest_version_id,
       latest_version.timestamp as updated_at,
       latest_version.description as version_description

ORDER BY id ASC
