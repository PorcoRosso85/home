// 既存要件を更新（新バージョン作成）
// パラメータ: $req_id, $title, $description, $status, $priority, $author, $reason, $timestamp
// 戻り値: entity_id, version_id

// 現在のバージョンを取得
MATCH (l:LocationURI {id: CONCAT('req://', $req_id)})
MATCH (l)-[:LOCATES {current: true}]->(current:RequirementEntity)
MATCH (current)-[:HAS_VERSION]->(cv:VersionState)

// バージョン番号を計算
WITH l, current, cv, count(cv) as version_count

// 新しいバージョンを作成
CREATE (r:RequirementEntity {
    id: CONCAT($req_id, '_v', CAST(version_count + 1, 'STRING')),
    title: COALESCE($title, current.title),
    description: COALESCE($description, current.description),
    status: COALESCE($status, current.status),
    priority: COALESCE($priority, current.priority)
})
CREATE (v:VersionState {
    id: CONCAT('ver_', $req_id, '_v', CAST(version_count + 1, 'STRING')),
    timestamp: $timestamp,
    operation: 'UPDATE',
    author: $author,
    change_reason: $reason
})
CREATE (r)-[:HAS_VERSION]->(v)

// LocationURIのポインタを更新
WITH l, r, v, current
MATCH (l)-[old:LOCATES {current: true}]->()
SET old.current = false
CREATE (l)-[:LOCATES {current: true}]->(r)

RETURN r.id as entity_id, v.id as version_id