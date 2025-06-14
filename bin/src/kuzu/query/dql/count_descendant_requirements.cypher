// 指定ノード配下の要件数をカウント
// パラメータ: $parentPath - 親ノードのパス
// ユースケース: 配下要件数カウント、統計情報

MATCH (parent:LocationURI {id: $parentPath})-[:CONTAINS_LOCATION*]->(leaf:LocationURI)
WHERE NOT EXISTS { MATCH (leaf)-[:CONTAINS_LOCATION]->() }
RETURN parent.id as parent_category,
       count(leaf) as requirement_count,
       collect(leaf.id)[0..5] as sample_requirements
ORDER BY requirement_count DESC;
