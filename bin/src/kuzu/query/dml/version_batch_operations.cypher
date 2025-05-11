// バージョン作成とその関連データを一括処理するDML
// NOTE: 2025-05-10 - FOREACHによる条件付き関係作成が以下のエラーで失敗したため、分離
// Error: "Parser exception: Invalid input <OPTIONAL MATCH (prev_version:VersionState {id: NULL}) FOREACH>"
// 原因: NULLのパラメータ埋め込みとFOREACH文の複雑な構文が原因
// 対策: FOLLOWS関係は別クエリ(create_follows.cypher)で処理するよう変更

// Step 1: VersionStateを作成
CREATE (v1:VersionState {id: $version_id, timestamp: $timestamp, description: $description, change_reason: $change_reason})

// Step 2: 関連するLocationURIを作成（存在チェック付き）
// NOTE: 2025-05-10 - CREATE文からMERGE文に変更
// 理由: LocationURIは複数バージョンで共有されるため重複エラーが発生
// Error: "Runtime exception: Found duplicated primary key value file:///src/main.ts"
// 対策: MERGEで存在チェックを行い、存在する場合はfragment/queryのみ更新
WITH v1
UNWIND $location_uris as location_data
MERGE (loc:LocationURI {uri_id: location_data.uri_id})
ON CREATE SET 
  loc.scheme = location_data.scheme,
  loc.authority = location_data.authority,
  loc.path = location_data.path,
  loc.fragment = location_data.fragment,
  loc.query = location_data.query
ON MATCH SET
  loc.fragment = location_data.fragment,
  loc.query = location_data.query
CREATE (v1)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc)

RETURN v1.id as version_id,
       collect(loc.uri_id) as created_location_uris
