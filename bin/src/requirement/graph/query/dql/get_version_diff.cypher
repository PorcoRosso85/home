// 指定されたバージョン番号の要件情報を取得（差分計算用）
// パラメータ: $req_id, $from_version, $to_version
// 戻り値: 2つのバージョンの情報
// 注: KuzuDBはバージョン番号を直接持たないため、タイムスタンプ順での取得

// LocationURI経由で要件にアクセス（新方式）
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (v:VersionState)-[:TRACKS_STATE_OF]->(l)
MATCH (l)-[:LOCATES]->(r:RequirementEntity)

// タイムスタンプ順にソートして番号を付ける
WITH r, v ORDER BY v.timestamp
WITH r, COLLECT(v) as versions

// from_versionとto_versionに該当するバージョンを取得
// 注: バージョン番号は1ベース（最初のバージョンが1）
WITH r, 
     CASE WHEN $from_version <= SIZE(versions) 
          THEN versions[$from_version - 1] 
          ELSE NULL 
     END as from_v,
     CASE WHEN $to_version <= SIZE(versions) 
          THEN versions[$to_version - 1] 
          ELSE NULL 
     END as to_v

// 両バージョンの情報を返す
RETURN {
    from_version: {
        entity_id: r.id,
        title: r.title,
        description: r.description,
        status: r.status,
        priority: r.priority,
        version_id: from_v.id,
        operation: from_v.operation,
        author: from_v.author,
        change_reason: from_v.change_reason,
        timestamp: from_v.timestamp
    },
    to_version: {
        entity_id: r.id,
        title: r.title,
        description: r.description,
        status: r.status,
        priority: r.priority,
        version_id: to_v.id,
        operation: to_v.operation,
        author: to_v.author,
        change_reason: to_v.change_reason,
        timestamp: to_v.timestamp
    }
} as version_data