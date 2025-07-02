// 新規要件をバージョン付きで作成
// パラメータ: $req_id, $title, $description, $status, $priority, $author, $reason
// 戻り値: entity_id, version_id, location_uri

WITH timestamp() as ts
CREATE (r:RequirementEntity {
    id: $req_id + '_v_' + toString(ts),
    requirement_id: $req_id,
    title: $title,
    description: $description,
    status: COALESCE($status, 'draft'),
    priority: COALESCE($priority, 1)
})
CREATE (v:VersionState {
    id: 'ver_' + $req_id + '_' + toString(ts),
    timestamp: datetime(),
    operation: 'CREATE',
    author: $author,
    change_reason: $reason
})
CREATE (r)-[:HAS_VERSION]->(v)
MERGE (l:LocationURI {id: 'req://' + $req_id})
CREATE (l)-[:LOCATES {current: true}]->(r)
RETURN r.id as entity_id, v.id as version_id, l.id as location_uri