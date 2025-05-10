// LocationURIノードを作成するクエリ
CREATE (locationuri:LocationURI {uri_id: $uri_id, scheme: $scheme, authority: $authority, path: $path, fragment: $fragment, query: $query})
RETURN locationuri
