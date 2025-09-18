// 後処理クエリ: VersionStateと関連付けられていないLocationURIを修正
// このクエリはCSVインポート後に実行され、データ整合性を保証します

// 1. 孤立したLocationURIの数を確認
MATCH (l:LocationURI) 
OPTIONAL MATCH (l)<-[:TRACKS_STATE_OF_LOCATED_ENTITY]-(v:VersionState) 
WITH l, v 
WHERE v IS NULL 
RETURN count(l) as initial_orphan_count;

// 2. 初期バージョン（v0.0.0）が存在しない場合は作成
MERGE (initial:VersionState {version_id: 'v0.0.0'})
ON CREATE SET 
    initial.timestamp = '2000-01-01T00:00:00Z',
    initial.description = 'Initial version for orphan LocationURIs',
    initial.change_reason = 'System generated for data consistency';

// 3. 孤立したLocationURIを初期バージョンに関連付け
MATCH (l:LocationURI)
OPTIONAL MATCH (l)<-[:TRACKS_STATE_OF_LOCATED_ENTITY]-(existing:VersionState)
WITH l, existing
WHERE existing IS NULL
MATCH (initial:VersionState {version_id: 'v0.0.0'})
CREATE (initial)-[:TRACKS_STATE_OF_LOCATED_ENTITY {change_type: 'INITIAL'}]->(l);

// 4. 修正後の確認
MATCH (l:LocationURI) 
OPTIONAL MATCH (l)<-[:TRACKS_STATE_OF_LOCATED_ENTITY]-(v:VersionState) 
WITH l, v 
WHERE v IS NULL 
RETURN count(l) as remaining_orphan_count;