// 指定ノード配下のリーフノード（要件）のみを取得
// パラメータ: $parentPath - 親ノードのパス
// ユースケース: 機能領域の全要件取得、テスト範囲特定

MATCH (parent:LocationURI {id: $parentPath})-[:CONTAINS_LOCATION*]->(leaf:LocationURI)
WHERE NOT EXISTS { MATCH (leaf)-[:CONTAINS_LOCATION]->() }
RETURN leaf.id as requirement_path,
       size((parent)-[:CONTAINS_LOCATION*]->(leaf)) as depth_from_parent
ORDER BY depth_from_parent, requirement_path;
