// 特定時点の要件状態を取得
// パラメータ: $req_id, $timestamp
// 戻り値: requirement, version

// LocationURI経由で要件にアクセス（新方式）
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (v:VersionState)-[:TRACKS_STATE_OF]->(l)
WHERE v.timestamp <= $timestamp
MATCH (l)-[:LOCATES]->(r:RequirementEntity)

// 最新のものを選択
WITH r, v
ORDER BY v.timestamp DESC
LIMIT 1

// 要件と履歴情報を返す
RETURN r as requirement, v as version