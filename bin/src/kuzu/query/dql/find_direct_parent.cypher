// 指定ノードの直接の親ノードを取得
// パラメータ: $childPath - 子ノードのパス
// ユースケース: 親カテゴリ特定、権限チェック

MATCH (parent:LocationURI)-[:CONTAINS_LOCATION]->(child:LocationURI {id: $childPath})
RETURN parent.id as parent_path,
       child.id as child_path
ORDER BY parent_path;
