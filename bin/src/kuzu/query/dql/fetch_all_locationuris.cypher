// 全てのLocationURIノードを取得するクエリ
// REFACTORED: 最小化されたスキーマに対応（idのみ）
MATCH (locationuri:LocationURI)
RETURN locationuri.id AS id
