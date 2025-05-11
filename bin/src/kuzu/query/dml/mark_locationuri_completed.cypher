// LocationURIの完了状態を設定するクエリ
MATCH (locationuri:LocationURI {uri_id: $uri_id})
SET locationuri.completed = $completed
RETURN locationuri.uri_id as uri_id,
       locationuri.completed as completed
