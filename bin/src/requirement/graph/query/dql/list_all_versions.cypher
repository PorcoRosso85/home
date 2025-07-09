// 要件の全バージョン一覧を取得
// パラメータ: $req_id
// 戻り値: バージョンIDと基本情報の一覧

// LocationURI経由で要件にアクセス（新方式）
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (v:VersionState)-[:TRACKS_STATE_OF]->(l)
MATCH (l)-[:LOCATES]->(r:RequirementEntity)

// バージョン情報を時系列で返す
RETURN v.id as version_id,
       v.operation as operation,
       v.timestamp as timestamp,
       v.author as author
ORDER BY v.timestamp