// 指定ノードの機能領域（第2階層）を特定
// パラメータ: $nodePath - ノードパス
// ユースケース: 権限チェック、管理者特定

MATCH (node:LocationURI {id: $nodePath})<-[:CONTAINS_LOCATION*]-(ancestors:LocationURI)
WITH ancestors, size((node)<-[:CONTAINS_LOCATION*]-(ancestors)) as levels_up
WHERE levels_up >= 0
WITH ancestors
ORDER BY size(ancestors.id) ASC
LIMIT 1
WITH ancestors as deepest_ancestor
MATCH (root:LocationURI)-[:CONTAINS_LOCATION]->(category:LocationURI)-[:CONTAINS_LOCATION*0..6]->(deepest_ancestor)
WHERE NOT EXISTS { MATCH (root)<-[:CONTAINS_LOCATION]-() }
RETURN category.id as functional_area,
       root.id as root_category,
       $nodePath as original_node
ORDER BY functional_area;
