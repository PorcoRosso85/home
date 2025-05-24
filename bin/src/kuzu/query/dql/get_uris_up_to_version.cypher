// 指定バージョン以前での各LocationURIの最新状態を取得するDQL
// ステップ1: 指定バージョンまでの全バージョンを取得
MATCH (target:VersionState {id: $version_id})
MATCH (historic:VersionState)
WHERE (historic)-[:FOLLOWS*0..]->(target)

// ステップ2: 各バージョンから各LocationURIへ
MATCH (historic)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)

// ステップ3: 各URIごとに最新のバージョンを特定
WITH l, 
     max(historic.timestamp) as max_timestamp,
     collect({v_id: historic.id, v_ts: historic.timestamp, v_desc: historic.description}) as all_versions

// ステップ4: 最新のバージョン情報を抽出
UNWIND all_versions as v
WITH l, v, max_timestamp
WHERE v.v_ts = max_timestamp

RETURN l.id as id,
       v.v_id as from_version,
       v.v_ts as updated_at,
       v.v_desc as version_description

ORDER BY l.id ASC
