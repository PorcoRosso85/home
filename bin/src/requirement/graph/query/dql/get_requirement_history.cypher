// 要件の全変更履歴を時系列で取得
// パラメータ: $req_id
// 戻り値: 要件情報とバージョン履歴

// LocationURI経由で全バージョンの要件にアクセス
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (l)-[:LOCATES*]->(r:RequirementEntity)
WHERE r.id = $req_id

// 各バージョンの要件情報を返す
RETURN r.id as entity_id,
       r.title as title,
       r.description as description,
       r.status as status,
       r.priority as priority,
       r.version_id as version_id,
       r.operation as operation,
       "system" as author,
       r.operation as change_reason,
       r.created_at as timestamp
ORDER BY r.created_at