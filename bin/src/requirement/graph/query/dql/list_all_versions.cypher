// 要件の全バージョン一覧を取得
// パラメータ: $req_id
// 戻り値: バージョンIDと基本情報の一覧

// LocationURI経由で要件にアクセス
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (l)-[:LOCATES]->(r:RequirementEntity)
MATCH (r)-[:HAS_VERSION]->(v:VersionState)

// バージョン情報を時系列で返す
RETURN v.id as version_id,
       v.operation as operation,
       v.timestamp as timestamp,
       v.author as author
ORDER BY v.timestamp