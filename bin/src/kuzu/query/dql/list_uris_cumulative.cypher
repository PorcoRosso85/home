// 指定バージョンでトラックされているLocationURIを取得（シンプル版）
// Duck APIからロードされたLocationURIテーブル（idのみ）に対応
MATCH (v:VersionState {id: $version_id})
MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
RETURN l.id as id,
       l.id as uri_id,    // 互換性のため
       v.id as from_version,
       v.description as version_description
ORDER BY l.id ASC
