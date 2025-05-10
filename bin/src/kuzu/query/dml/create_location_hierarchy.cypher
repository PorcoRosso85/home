// LocationURI階層構造の一括作成DML（ファイル階層と要件階層を分離）
// 入力形式: {hierarchies: [{parent_uri: string, child_uri: string, relation_type: string}]}

WITH $hierarchies AS data
UNWIND data AS hierarchy
MATCH (parent:LocationURI {uri_id: hierarchy.parent_uri})
MATCH (child:LocationURI {uri_id: hierarchy.child_uri})
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: hierarchy.relation_type}]->(child)

WITH hierarchy.relation_type as relation_type, count(*) as count
RETURN relation_type,
       count,
       CASE 
         WHEN relation_type = 'file_hierarchy' THEN 'ファイル階層'
         WHEN relation_type = 'requirement_hierarchy' THEN '要件階層'
         ELSE '不明な階層種別'
       END as hierarchy_type
