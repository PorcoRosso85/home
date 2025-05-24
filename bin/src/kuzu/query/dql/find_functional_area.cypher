// 指定ノードの機能領域（第2階層）を特定
// パラメータ: $nodePath - ノードパス
// ユースケース: 権限チェック、管理者特定

MATCH (node:LocationURI {id: $nodePath})<-[:PARENT_OF*]-(ancestors:LocationURI)
WITH ancestors, size((node)<-[:PARENT_OF*]-(ancestors)) as levels_up
WHERE levels_up >= 0
WITH ancestors
ORDER BY size(ancestors.id) ASC
LIMIT 1
WITH ancestors as deepest_ancestor
MATCH (root:LocationURI)-[:PARENT_OF]->(category:LocationURI)-[:PARENT_OF*0..6]->(deepest_ancestor)
WHERE NOT EXISTS { MATCH (root)<-[:PARENT_OF]-() }
RETURN category.id as functional_area,
       root.id as root_category,
       $nodePath as original_node
ORDER BY functional_area;
