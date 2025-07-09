// 要件の全変更履歴を時系列で取得
// パラメータ: $req_id
// 戻り値: 要件情報とバージョン履歴

// 要件の変更履歴を取得（新方式）
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (v:VersionState)-[:TRACKS_STATE_OF]->(l)
MATCH (l)-[:LOCATES]->(r:RequirementEntity)

// 現在の状態と履歴情報を返す
RETURN 
    r.id as entity_id,
    r.title as current_title,
    r.description as current_description,
    r.status as current_status,
    v.id as version_id,
    v.operation as operation,
    v.author as author,
    v.change_reason as change_reason,
    v.timestamp as timestamp
ORDER BY v.timestamp