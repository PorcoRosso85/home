// 要件の全変更履歴を時系列で取得
// パラメータ: $req_id
// 戻り値: 要件情報とバージョン履歴

// LocationURI経由で要件にアクセス
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (l)-[:LOCATES]->(r:RequirementEntity)
MATCH (r)-[:HAS_VERSION]->(v:VersionState)

// 要件情報と各バージョンの情報を返す
RETURN r.id as entity_id,
       r.title as title,
       r.description as description,
       r.status as status,
       r.priority as priority,
       v.id as version_id,
       v.operation as operation,
       v.author as author,
       v.change_reason as change_reason,
       v.timestamp as timestamp
ORDER BY v.timestamp