// 指定ノード配下のリーフノード（要件）のみを取得
// パラメータ: $parentPath - 親ノードのパス
// ユースケース: 機能領域の全要件取得、テスト範囲特定

MATCH (parent:LocationURI {id: $parentPath})-[:PARENT_OF*]->(leaf:LocationURI)
WHERE NOT EXISTS { MATCH (leaf)-[:PARENT_OF]->() }
RETURN leaf.id as requirement_path,
       size((parent)-[:PARENT_OF*]->(leaf)) as depth_from_parent
ORDER BY depth_from_parent, requirement_path;
