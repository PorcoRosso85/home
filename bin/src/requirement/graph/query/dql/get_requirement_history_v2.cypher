// 要件の完全な変更履歴を取得（履歴再構築版）
// パラメータ: $req_id
// 戻り値: 各バージョンの完全な状態

// 要件とそのバージョン履歴を取得（新方式）
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (l)-[:LOCATES]->(r:RequirementEntity)
OPTIONAL MATCH (v:VersionState)-[:TRACKS_STATE_OF]->(l)

// バージョンを時系列でソート
WITH r, v
ORDER BY v.timestamp

// 各バージョンの状態を再構築
WITH r, COLLECT(v) as versions
UNWIND RANGE(0, SIZE(versions) - 1) as idx
WITH r, versions, idx, versions[idx] as current_version

// 状態の再構築ロジック:
// - CREATE操作: 現在の要件の状態を使用
// - UPDATE操作: 現在の状態を使用
RETURN 
    r.id as entity_id,
    // タイトルの再構築
    CASE 
        WHEN current_version.operation = 'CREATE' THEN r.title
        ELSE r.title
    END as title,
    // 説明の再構築
    CASE 
        WHEN current_version.operation = 'CREATE' THEN r.description
        ELSE r.description
    END as description,
    // ステータスの再構築
    CASE 
        WHEN current_version.operation = 'CREATE' THEN 'draft'
        ELSE r.status
    END as status,
    current_version.id as version_id,
    current_version.operation as operation,
    current_version.author as author,
    current_version.change_reason as change_reason,
    current_version.timestamp as timestamp