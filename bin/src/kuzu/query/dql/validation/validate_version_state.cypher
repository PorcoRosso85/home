// VersionState検証（TypeScript versionStateValidation.ts の完全代替）
// パラメータ: $versionStateData
//
// 機能:
// - 必須フィールド検証 (id, timestamp)
// - ISO 8601タイムスタンプ形式検証
// - KuzuDB TIMESTAMP型パース検証
// - オプションフィールド検証 (description)

WITH $versionStateData as data

// 必須フィールド検証
WITH data,
     CASE 
       WHEN data.id IS NULL OR NOT data.id IS :: STRING THEN 'id is required and must be a string'
       WHEN size(trim(data.id)) = 0 THEN 'id cannot be empty'
       ELSE null
     END as id_error,
     CASE 
       WHEN data.timestamp IS NULL OR NOT data.timestamp IS :: STRING THEN 'timestamp is required and must be a string'
       WHEN NOT data.timestamp =~ '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$' 
         THEN 'timestamp must be in ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)'
       ELSE null
     END as timestamp_error
WITH data, id_error, timestamp_error,
     CASE 
       WHEN data.description IS NOT NULL AND NOT data.description IS :: STRING 
         THEN 'description must be a string'
       ELSE null
     END as description_error

WITH [id_error, timestamp_error, description_error] as all_errors
WITH filter(error IN all_errors WHERE error IS NOT null) as validation_errors

// TIMESTAMP型でのパース検証（エラーがない場合のみ）
WITH validation_errors, data,
     CASE 
       WHEN size(validation_errors) = 0 THEN
         // タイムスタンプのパース検証を試行
         CASE 
           WHEN data.timestamp =~ '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$' THEN data.timestamp
           ELSE null
         END
       ELSE null
     END as parsed_timestamp

RETURN {
  is_valid: size(validation_errors) = 0 AND parsed_timestamp IS NOT null,
  data: CASE 
          WHEN size(validation_errors) = 0 AND parsed_timestamp IS NOT null THEN {
            id: data.id,
            timestamp: parsed_timestamp,
            description: data.description
          }
          ELSE null
        END,
  errors: CASE 
            WHEN size(validation_errors) > 0 THEN validation_errors
            WHEN parsed_timestamp IS null THEN ['Invalid timestamp format for parsing']
            ELSE []
          END,
  error: CASE 
           WHEN size(validation_errors) > 0 
             THEN 'Validation failed for VersionState: ' + list_aggregate(validation_errors, ', ')
           WHEN parsed_timestamp IS null
             THEN 'Validation failed for VersionState: Invalid timestamp format'
           ELSE null
         END
} as result