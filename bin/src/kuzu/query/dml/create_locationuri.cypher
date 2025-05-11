// LocationURIノードを作成するクエリ
CREATE (locationuri:LocationURI {
  uri_id: $uri_id, 
  scheme: $scheme, 
  authority: COALESCE($authority, ''), 
  path: $path, 
  fragment: COALESCE($fragment, ''), 
  query: COALESCE($query, ''),
  completed: COALESCE($completed, false)
})
RETURN locationuri
