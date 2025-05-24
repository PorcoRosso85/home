// LocationURIノードを検索するクエリ
// REFACTORED: uri_id -> id に変更
MATCH (locationuri:LocationURI {id: $id})
RETURN locationuri