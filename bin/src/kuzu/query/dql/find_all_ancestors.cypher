// 指定ノードから上位ルートまでの全親階層を取得
// パラメータ: $childPath - 子ノードのパス
// ユースケース: 要件所在特定、パンくずリスト生成

MATCH (child:LocationURI {id: $childPath})<-[:CONTAINS_LOCATION*]-(ancestors:LocationURI)
RETURN ancestors.id as ancestor_path,
       size((child)<-[:CONTAINS_LOCATION*]-(ancestors)) as levels_up
ORDER BY levels_up DESC;
