// バージョン作成とその関連データを一括処理するDML
// REFACTORED: 最小化されたLocationURIスキーマに対応（idのみ）

// Step 1: VersionStateを作成
CREATE (v1:VersionState {id: $version_id, timestamp: $timestamp, description: $description, change_reason: $change_reason})

// Step 2: 関連するLocationURIを作成（最小化スキーマ）
WITH v1
UNWIND $location_uris as location_data
MERGE (loc:LocationURI {id: location_data.id})
CREATE (v1)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc)

RETURN v1.id as version_id,
       collect(loc.id) as created_location_uris
