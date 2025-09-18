// VersionBatch統合検証（TypeScript versionBatchValidation.ts の完全代替）
// パラメータ: $versionedLocationData
//
// 機能:
// - VersionState構築・検証
// - LocationURI配列検証
// - previous_version_id検証
// - 全エラー統合・詳細レポート

WITH $versionedLocationData as data

// VersionStateデータ構築
WITH data,
     {
       id: data.version_id,
       timestamp: to_iso_string(now()),
       description: 'Version ' + data.version_id + ' release'
     } as version_state_data

// 基本構造検証
WITH data, version_state_data,
     CASE 
       WHEN data.location_uris IS NULL THEN 'location_uris must be an array'
       ELSE null
     END as array_error
WITH data, version_state_data, array_error,
     CASE 
       WHEN data.previous_version_id IS NOT NULL AND 
            (NOT data.previous_version_id IS :: STRING OR size(trim(data.previous_version_id)) = 0)
         THEN 'previous_version_id must be a non-empty string'
       ELSE null
     END as prev_version_error

// VersionState検証
WITH data, version_state_data, array_error, prev_version_error,
     CASE 
       WHEN version_state_data.id IS NULL OR size(trim(version_state_data.id)) = 0 
         THEN [{field: 'versionState.id', message: 'id cannot be empty'}]
       WHEN NOT version_state_data.timestamp =~ '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$'
         THEN [{field: 'versionState.timestamp', message: 'timestamp must be in ISO 8601 format'}]
       ELSE []
     END as version_state_errors

// LocationURI配列検証
WITH data, array_error, prev_version_error, version_state_errors,
     CASE 
       WHEN array_error IS NULL THEN data.location_uris
       ELSE []
     END as uris_to_validate
UNWIND uris_to_validate as uri 
WITH uri, row_number() OVER() as uri_index,
     data, array_error, prev_version_error, version_state_errors

WITH data, array_error, prev_version_error, version_state_errors,
     collect(
       CASE 
         WHEN uri.id IS NULL OR size(trim(uri.id)) = 0 THEN 
           {field: 'location_uris[' + toString(uri_index-1) + '].id', message: 'id cannot be empty'}
         WHEN NOT uri.id =~ '^<[a-zA-Z0-9_-]+>/srs/.+$' THEN 
           {field: 'location_uris[' + toString(uri_index-1) + '].id', message: 'Invalid URI format'}
         ELSE null
       END
     ) as uri_errors

// 全エラー統合
WITH version_state_errors + filter(error IN uri_errors WHERE error IS NOT null) +
     filter(error IN [
       CASE WHEN array_error IS NOT NULL THEN {field: 'location_uris', message: array_error} ELSE null END,
       CASE WHEN prev_version_error IS NOT NULL THEN {field: 'previous_version_id', message: prev_version_error} ELSE null END
     ] WHERE error IS NOT null) as all_errors

RETURN {
  is_valid: size(all_errors) = 0,
  data: CASE 
          WHEN size(all_errors) = 0 THEN data
          ELSE null
        END,
  errors: all_errors,
  error: CASE 
           WHEN size(all_errors) > 0 THEN 
             'Validation failed for VersionBatch: ' + 
             list_aggregate([error IN all_errors | error.field + ': ' + error.message], ', ')
           ELSE null
         END,
  validation_summary: {
    total_errors: size(all_errors),
    version_state_errors: size(version_state_errors),
    location_uri_errors: size(filter(error IN all_errors WHERE starts_with(error.field, 'location_uris'))),
    basic_structure_errors: size(filter(error IN all_errors WHERE error.field IN ['location_uris', 'previous_version_id']))
  }
} as result