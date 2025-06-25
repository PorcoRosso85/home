// 指定ノード配下の全子孫ノードを取得
// パラメータ: $parentPath - 親ノードのパス
// ユースケース: カテゴリ内要件一覧、影響範囲分析、レビュー範囲

MATCH (parent:LocationURI {id: $parentPath})-[:CONTAINS_LOCATION*]->(descendants:LocationURI)
RETURN descendants.id as descendant_path, 
       size((parent)-[:CONTAINS_LOCATION*]->(descendants)) as depth_from_parent
ORDER BY depth_from_parent, descendant_path;
