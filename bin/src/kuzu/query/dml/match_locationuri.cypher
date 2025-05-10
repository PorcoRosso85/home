// LocationURIノードを検索するクエリ
MATCH (locationuri:LocationURI {uri_id: $uri_id})
RETURN locationuri