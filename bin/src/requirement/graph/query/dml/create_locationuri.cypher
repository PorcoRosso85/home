// LocationURIノードを作成するクエリ
// REFACTORED: 最小化されたスキーマに対応（idのみ）
CREATE (locationuri:LocationURI {
  id: $id
})
RETURN locationuri
