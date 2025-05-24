// LocationURIノードを更新するクエリ
// REFACTORED: 最小化されたスキーマ（idのみ）では更新対象プロパティなし
MATCH (locationuri:LocationURI {id: $id})
RETURN locationuri