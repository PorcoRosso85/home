// 要件の全バージョンを取得（現在のAppend-Only実装に対応）
// パラメータ: $base_id (バージョン番号を除いたベースID)
// 戻り値: 全バージョンの要件情報

// ベースIDで始まる全ての要件を取得
MATCH (r:RequirementEntity)
WHERE r.id = $base_id OR r.id STARTS WITH CONCAT($base_id, '_v')
RETURN 
    r.id as version_id,
    r.title as title,
    r.description as description,
    r.status as status,
    r.id as raw_id
ORDER BY r.id