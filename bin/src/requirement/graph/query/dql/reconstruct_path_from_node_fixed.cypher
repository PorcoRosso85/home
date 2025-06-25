// LocationURI階層パス再構築（修正版）
// FIXED: PARENT_OF → CONTAINS_LOCATION に修正
// パラメータ: $nodeId

MATCH path = (root:LocationURI)-[:CONTAINS_LOCATION*0..7]->(target:LocationURI {id: $nodeId})
WHERE NOT EXISTS { MATCH (root)<-[:CONTAINS_LOCATION]-() }
WITH nodes(path) as hierarchy, target,
     // relation_typeで階層種別を取得
     [rel in relationships(path) | rel.relation_type] as relation_types

// 一貫した階層種別かチェック
WITH hierarchy, target, relation_types,
     size(filter(rt in relation_types WHERE rt = relation_types[0])) = size(relation_types) as consistent_hierarchy,
     relation_types[0] as hierarchy_type

RETURN target.id as reconstructed_path,
       hierarchy_type,
       consistent_hierarchy,
       [node in hierarchy | node.id] as full_path
