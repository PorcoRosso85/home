// 要件を削除（削除マークの新バージョン作成）
// パラメータ: $req_id, $author, $reason
// 戻り値: entity_id, version_id

// 現在のバージョンを取得
MATCH (l:LocationURI {id: 'req://' + $req_id})
MATCH (l)-[:LOCATES {current: true}]->(current:RequirementEntity)

// 削除バージョンを作成（内容は現在のものを保持）
WITH l, current, timestamp() as ts
CREATE (r:RequirementEntity {
    id: $req_id + '_v_' + toString(ts),
    requirement_id: $req_id,
    title: current.title,
    description: current.description,
    status: 'deleted'  // ステータスを削除に変更
})
CREATE (v:VersionState {
    id: 'ver_' + $req_id + '_' + toString(ts),
    timestamp: datetime(),
    operation: 'DELETE',
    author: $author,
    change_reason: $reason
})
CREATE (v)-[:TRACKS_STATE_OF {entity_type: 'requirement'}]->(l)

// LocationURIのポインタを更新（削除状態もポイント）
MATCH (l)-[old:LOCATES {current: true}]->()
SET old.current = false
CREATE (l)-[:LOCATES {current: true, deleted: true}]->(r)

RETURN r.id as entity_id, v.id as version_id