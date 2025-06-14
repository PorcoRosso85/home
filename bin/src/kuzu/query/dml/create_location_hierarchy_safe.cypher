// 安全な階層作成 - バリデーション通過後の実行版
// パラメータ: $hierarchies - 階層データ配列（事前バリデーション済み）

WITH $hierarchies AS data
UNWIND data AS hierarchy

// バリデーション済み前提で直接実行
MATCH (parent:LocationURI {id: hierarchy.parent_id})
MATCH (child:LocationURI {id: hierarchy.child_id})
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: hierarchy.relation_type}]->(child)

WITH hierarchy.relation_type as relation_type, count(*) as count
RETURN relation_type,
       count,
       CASE 
         WHEN relation_type = 'file_hierarchy' THEN 'ファイル階層'
         WHEN relation_type = 'requirement_hierarchy' THEN '要件階層'
         ELSE '不明な階層種別'
       END as hierarchy_type,
       'SUCCESS' as status