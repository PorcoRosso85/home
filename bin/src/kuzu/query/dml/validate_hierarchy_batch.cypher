// 階層バッチバリデーション - TypeScript検証機能をCypher側に移行
// パラメータ: $hierarchies - 階層データ配列
// 戻り値: validation_result - 成功/失敗とエラー詳細

WITH $hierarchies AS data

// Step 1: 基本パラメータ検証
WITH data,
     CASE 
       WHEN data IS NULL THEN ['hierarchies parameter is required']
       WHEN NOT data IS :: LIST THEN ['hierarchies must be an array']
       WHEN size(data) = 0 THEN ['hierarchies cannot be empty']
       ELSE []
     END as basic_errors

// Step 2: 各階層要素の検証
UNWIND CASE WHEN size(basic_errors) = 0 THEN data ELSE [{}] END as hierarchy
WITH basic_errors, hierarchy,
     CASE 
       WHEN size(basic_errors) > 0 THEN []
       WHEN hierarchy.parent_id IS NULL THEN ['parent_id is required']
       WHEN hierarchy.child_id IS NULL THEN ['child_id is required']
       WHEN hierarchy.relation_type IS NULL THEN ['relation_type is required']
       WHEN NOT hierarchy.parent_id IS :: STRING THEN ['parent_id must be string']
       WHEN NOT hierarchy.child_id IS :: STRING THEN ['child_id must be string']
       WHEN NOT hierarchy.relation_type IS :: STRING THEN ['relation_type must be string']
       WHEN trim(hierarchy.parent_id) = '' THEN ['parent_id cannot be empty']
       WHEN trim(hierarchy.child_id) = '' THEN ['child_id cannot be empty']
       WHEN hierarchy.parent_id = hierarchy.child_id THEN ['parent_id and child_id cannot be same']
       ELSE []
     END as field_errors

// Step 3: 存在チェック
WITH basic_errors, field_errors, hierarchy
OPTIONAL MATCH (parent:LocationURI {id: hierarchy.parent_id})
OPTIONAL MATCH (child:LocationURI {id: hierarchy.child_id})
WITH basic_errors, field_errors, hierarchy,
     CASE 
       WHEN size(basic_errors) > 0 OR size(field_errors) > 0 THEN []
       WHEN parent IS NULL THEN ['parent LocationURI not found: ' + hierarchy.parent_id]
       WHEN child IS NULL THEN ['child LocationURI not found: ' + hierarchy.child_id]
       ELSE []
     END as existence_errors

// Step 4: 重複・循環参照チェック
OPTIONAL MATCH (parent)-[existing:CONTAINS_LOCATION]->(child)
OPTIONAL MATCH cycle = (child)-[:CONTAINS_LOCATION*1..8]->(parent)
WITH basic_errors, field_errors, existence_errors, hierarchy,
     CASE 
       WHEN size(basic_errors) > 0 OR size(field_errors) > 0 OR size(existence_errors) > 0 THEN []
       WHEN existing IS NOT NULL THEN ['duplicate relation already exists: ' + hierarchy.parent_id + ' -> ' + hierarchy.child_id]
       WHEN cycle IS NOT NULL THEN ['circular reference detected: ' + hierarchy.parent_id + ' -> ' + hierarchy.child_id]
       ELSE []
     END as relation_errors

// Step 5: 結果集約
WITH basic_errors + field_errors + existence_errors + relation_errors as all_errors
WITH filter(error IN all_errors WHERE error IS NOT NULL AND error <> '') as validation_errors

RETURN {
  is_valid: size(validation_errors) = 0,
  errors: validation_errors,
  error_count: size(validation_errors),
  message: CASE 
             WHEN size(validation_errors) = 0 THEN 'All validations passed'
             ELSE 'Validation failed: ' + list_aggregate(validation_errors, '; ')
           END
} as validation_result
