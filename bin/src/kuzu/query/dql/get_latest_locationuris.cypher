// 各LocationURIの最新バージョンを取得するDQL
// gitのワーキングディレクトリと同じ概念で、各URIの最新状態を表示

// 各LocationURIについて、最後に関連付けられたバージョンを特定
MATCH (v:VersionState)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)

// 各LocationURIについて最新のバージョンを取得
WITH l.uri_id as uri_id, 
     l.scheme as scheme,
     l.authority as authority,
     l.path as path,
     l.fragment as fragment,
     l.query as query,
     max(v.timestamp) as latest_timestamp,
     collect({version_id: v.id, timestamp: v.timestamp, description: v.description}) as all_versions

// 最新タイムスタンプに一致するバージョン情報を取得
WITH uri_id, scheme, authority, path, fragment, query, latest_timestamp,
     [version IN all_versions WHERE version.timestamp = latest_timestamp][0] as latest_version

RETURN uri_id,
       scheme,
       authority,
       path,
       fragment,
       query,
       latest_version.version_id as latest_version_id,
       latest_version.timestamp as updated_at,
       latest_version.description as version_description

ORDER BY path ASC, uri_id ASC
