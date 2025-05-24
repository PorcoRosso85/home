// 指定ノードのルートノードを特定
// パラメータ: $childPath - 子ノードのパス
// ユースケース: ルート特定、トップレベルカテゴリ特定

MATCH (child:LocationURI {id: $childPath})<-[:PARENT_OF*]-(root:LocationURI)
WHERE NOT EXISTS { MATCH (root)<-[:PARENT_OF]-() }
RETURN root.id as root_path,
       child.id as child_path,
       size((child)<-[:PARENT_OF*]-(root)) as depth_from_root
ORDER BY root_path;
