// LocationURIノードからフルパス再計算（基本構文のみ）
// パラメータ: $nodeId

MATCH path = (root:LocationURI)-[:PARENT_OF*0..7]->(target:LocationURI {id: $nodeId})
WHERE NOT EXISTS { MATCH (root)<-[:PARENT_OF]-() }
WITH nodes(path) as hierarchy, target
RETURN target.id as reconstructed_path;