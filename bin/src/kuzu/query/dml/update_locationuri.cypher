// LocationURIノードを更新するクエリ
MATCH (locationuri:LocationURI {uri_id: $uri_id})
SET locationuri.scheme = $scheme,
    locationuri.authority = $authority,
    locationuri.path = $path,
    locationuri.fragment = $fragment,
    locationuri.query = $query
RETURN locationuri