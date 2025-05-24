// パンくずリスト用の階層パス生成
// パラメータ: $currentPath - 現在のノードパス
// ユースケース: UI表示用パンくずリスト

MATCH path = (root:LocationURI)-[:PARENT_OF*0..7]->(current:LocationURI {id: $currentPath})
WHERE NOT EXISTS { MATCH (root)<-[:PARENT_OF]-() }
WITH nodes(path) as hierarchy
UNWIND range(0, size(hierarchy)-1) as idx
WITH hierarchy[idx] as node, idx as level
RETURN level,
       node.id as path_segment,
       CASE WHEN level = size(hierarchy)-1 THEN true ELSE false END as is_current
ORDER BY level;
