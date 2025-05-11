// LocationURIノードを更新するクエリ
MATCH (locationuri:LocationURI {uri_id: $uri_id})
SET locationuri.scheme = COALESCE($scheme, locationuri.scheme),
    locationuri.authority = COALESCE($authority, locationuri.authority),
    locationuri.path = COALESCE($path, locationuri.path),
    locationuri.fragment = COALESCE($fragment, locationuri.fragment),
    locationuri.query = COALESCE($query, locationuri.query),
    locationuri.completed = COALESCE($completed, locationuri.completed)
RETURN locationuri