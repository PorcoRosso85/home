// 指定ノード配下の全子孫ノードを取得
// パラメータ: $parentPath - 親ノードのパス
// ユースケース: カテゴリ内要件一覧、影響範囲分析、レビュー範囲

MATCH (parent:LocationURI {id: $parentPath})-[:PARENT_OF*]->(descendants:LocationURI)
RETURN descendants.id as descendant_path, 
       size((parent)-[:PARENT_OF*]->(descendants)) as depth_from_parent
ORDER BY depth_from_parent, descendant_path;
