// 特定時点の要件状態を取得
// パラメータ: $req_id, $timestamp
// 戻り値: requirement, version

// LocationURI経由で要件にアクセス
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (l)-[:LOCATES]->(r:RequirementEntity)
MATCH (r)-[:HAS_VERSION]->(v:VersionState)
WHERE v.timestamp <= $timestamp

// 最新のものを選択
WITH r, v
ORDER BY v.timestamp DESC
LIMIT 1

// 要件と履歴情報を返す
RETURN r as requirement, v as version