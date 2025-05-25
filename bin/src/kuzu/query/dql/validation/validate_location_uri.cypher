// LocationURI検証（TypeScript locationUriValidation.ts の完全代替）
// パラメータ: $locationUriData
//
// 機能:
// - 必須フィールド検証 (id)
// - スキーマ検証 (file, http, https, requirement, test, document)
// - URI形式検証 (<project>/srs/path パターン)
// - プロジェクト名検証 (英数字、ハイフン、アンダースコアのみ)

WITH $locationUriData as data,
     ['file', 'http', 'https', 'requirement', 'test', 'document'] as allowed_schemes

// 基本検証
WITH data, allowed_schemes,
     CASE 
       WHEN data.id IS NULL OR NOT data.id IS :: STRING THEN 'id is required and must be a string'
       WHEN size(trim(data.id)) = 0 THEN 'id cannot be empty'
       ELSE null
     END as id_error

// スキーマ検証
WITH data, allowed_schemes, id_error,
     CASE 
       WHEN id_error IS NULL AND contains(data.id, ':') THEN string_split(data.id, ':')[1]
       ELSE null
     END as scheme
WITH data, allowed_schemes, id_error, scheme,
     CASE 
       WHEN id_error IS NULL AND scheme IS NOT NULL AND NOT scheme IN allowed_schemes 
         THEN 'Invalid scheme \'' + scheme + '\'. Allowed: ' + list_aggregate(allowed_schemes, ', ')
       ELSE null
     END as scheme_error

// URI形式検証（プロジェクト形式）
WITH data, id_error, scheme_error,
     CASE 
       WHEN id_error IS NULL AND scheme_error IS NULL THEN
         CASE 
           WHEN data.id =~ '^<[a-zA-Z0-9_-]+>/srs/.+$' THEN null
           ELSE 'URI must match pattern: <project>/srs/path'
         END
       ELSE null
     END as format_error

WITH [id_error, scheme_error, format_error] as all_errors
WITH filter(error IN all_errors WHERE error IS NOT null) as validation_errors

RETURN {
  is_valid: size(validation_errors) = 0,
  data: CASE 
          WHEN size(validation_errors) = 0 THEN { id: data.id }
          ELSE null
        END,
  errors: validation_errors,
  error: CASE 
           WHEN size(validation_errors) > 0 
             THEN 'Validation failed for LocationURI: ' + list_aggregate(validation_errors, ', ')
           ELSE null
         END,
  validation_details: {
    detected_scheme: CASE 
                       WHEN contains(data.id, ':') THEN string_split(data.id, ':')[1] 
                       ELSE null 
                     END,
    allowed_schemes: allowed_schemes,
    format_check: data.id =~ '^<[a-zA-Z0-9_-]+>/srs/.+$'
  }
} as result