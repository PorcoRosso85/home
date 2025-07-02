// 既存要件を更新（新バージョン作成）
// パラメータ: $req_id, $title, $description, $status, $priority, $author, $reason
// 戻り値: entity_id, version_id

// 現在のバージョンを取得
MATCH (l:LocationURI {id: 'req://' + $req_id})
MATCH (l)-[:LOCATES {current: true}]->(current:RequirementEntity)

// 新しいバージョンを作成
WITH l, current, timestamp() as ts
CREATE (r:RequirementEntity {
    id: $req_id + '_v_' + toString(ts),
    requirement_id: $req_id,
    title: COALESCE($title, current.title),
    description: COALESCE($description, current.description),
    status: COALESCE($status, current.status),
    priority: COALESCE($priority, current.priority)
})
CREATE (v:VersionState {
    id: 'ver_' + $req_id + '_' + toString(ts),
    timestamp: datetime(),
    operation: 'UPDATE',
    author: $author,
    change_reason: $reason,
    previous_version: current.id
})
CREATE (r)-[:HAS_VERSION]->(v)

// LocationURIのポインタを更新
MATCH (l)-[old:LOCATES {current: true}]->()
SET old.current = false
CREATE (l)-[:LOCATES {current: true}]->(r)

RETURN r.id as entity_id, v.id as version_id