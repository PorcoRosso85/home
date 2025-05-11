// 複数LocationURIの完了状態を一括更新
// $uri_ids は文字列のリスト: ["uri1", "uri2", "uri3", ...]
// $completed_values は対応するBOOLEANのリスト: [true, false, true, ...]

UNWIND range(0, size($uri_ids) - 1) as i
WITH $uri_ids[i] as uri_id, $completed_values[i] as completed
MATCH (loc:LocationURI {uri_id: uri_id})
SET loc.completed = completed
RETURN loc.uri_id as uri_id, loc.completed as completed
