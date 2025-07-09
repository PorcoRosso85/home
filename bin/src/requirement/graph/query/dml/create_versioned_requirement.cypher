// 新規要件をバージョン付きで作成
// パラメータ: $req_id, $title, $description, $status, $priority, $author, $reason, $timestamp
// 戻り値: entity_id, version_id, location_uri

CREATE (r:RequirementEntity {
    id: $req_id,
    title: $title,
    description: $description,
    status: COALESCE($status, 'draft'),
    priority: COALESCE($priority, 1)
})
CREATE (v:VersionState {
    id: CONCAT('ver_', $req_id, '_v1'),
    timestamp: $timestamp,
    operation: 'CREATE',
    author: $author,
    change_reason: $reason
})
CREATE (l:LocationURI {id: CONCAT('req://', $req_id)})
CREATE (l)-[:LOCATES]->(r)
CREATE (v)-[:TRACKS_STATE_OF {entity_type: 'requirement'}]->(l)
RETURN r.id as entity_id, v.id as version_id, l.id as location_uri