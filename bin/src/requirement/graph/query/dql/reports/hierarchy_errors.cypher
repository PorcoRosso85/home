// 階層エラーレポート - 失敗詳細の構造化出力
// パラメータ: $hierarchies - 検証対象の階層データ
// 戻り値: エラー詳細レポート

WITH $hierarchies AS data
UNWIND data AS hierarchy

// 各エラー類型をチェック
OPTIONAL MATCH (parent:LocationURI {id: hierarchy.parent_id})
OPTIONAL MATCH (child:LocationURI {id: hierarchy.child_id})
OPTIONAL MATCH (parent)-[existing:CONTAINS_LOCATION]->(child)
OPTIONAL MATCH cycle = (child)-[:CONTAINS_LOCATION*1..8]->(parent)

WITH hierarchy,
     CASE WHEN parent IS NULL THEN 'PARENT_NOT_FOUND' ELSE NULL END as parent_error,
     CASE WHEN child IS NULL THEN 'CHILD_NOT_FOUND' ELSE NULL END as child_error,
     CASE WHEN existing IS NOT NULL THEN 'DUPLICATE_RELATION' ELSE NULL END as duplicate_error,
     CASE WHEN cycle IS NOT NULL THEN 'CIRCULAR_REFERENCE' ELSE NULL END as cycle_error

WITH hierarchy, 
     filter(error IN [parent_error, child_error, duplicate_error, cycle_error] WHERE error IS NOT NULL) as errors

RETURN {
  hierarchy_index: hierarchy.parent_id + ' -> ' + hierarchy.child_id,
  parent_id: hierarchy.parent_id,
  child_id: hierarchy.child_id,
  relation_type: hierarchy.relation_type,
  error_types: errors,
  error_count: size(errors),
  is_valid: size(errors) = 0,
  details: CASE 
             WHEN size(errors) = 0 THEN 'OK'
             ELSE 'Failed: ' + list_aggregate(errors, ', ')
           END
} as error_report
ORDER BY size(errors) DESC, hierarchy.parent_id
