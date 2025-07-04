// 既存要件を更新（新バージョン作成）
// パラメータ: $req_id, $title, $description, $status, $priority, $author, $reason, $timestamp
// 戻り値: entity_id, version_id

// 既存要件を取得
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (l)-[:LOCATES]->(r:RequirementEntity)

// 現在のバージョン数を取得
OPTIONAL MATCH (r)-[:HAS_VERSION]->(v:VersionState)
WITH l, r, count(v) as version_count

// 要件を更新
SET r.title = COALESCE($title, r.title),
    r.description = COALESCE($description, r.description),
    r.status = COALESCE($status, r.status),
    r.priority = COALESCE($priority, r.priority)

// 新しいバージョンを作成
CREATE (new_v:VersionState {
    id: CONCAT('ver_', $req_id, '_v', CAST(version_count + 1, 'STRING')),
    timestamp: $timestamp,
    operation: 'UPDATE',
    author: $author,
    change_reason: $reason
})
CREATE (r)-[:HAS_VERSION]->(new_v)

RETURN r.id as entity_id, new_v.id as version_id