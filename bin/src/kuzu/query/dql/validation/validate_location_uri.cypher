// LocationURI検証（完全版 - TypeScript代替）
// パラメータ: $locationUriData
//
// 機能:
// - 必須フィールド検証 (id)
// - スキーマ検証 (file, http, https, requirement, test, document)
// - URI形式検証 (<project>/srs/path パターン)
// - フラグメント必須チェック (file, requirement, test, document)
// - フラグメントパターン検証

WITH $locationUriData as data,
     ['file', 'http', 'https', 'requirement', 'test', 'document'] as allowed_schemes,
     ['file', 'requirement', 'test', 'document'] as fragment_required_schemes

// 基本検証
WITH data, allowed_schemes, fragment_required_schemes,
     CASE 
       WHEN data.id IS NULL OR NOT data.id IS :: STRING THEN 'id is required and must be a string'
       WHEN size(trim(data.id)) = 0 THEN 'id cannot be empty'
       ELSE null
     END as id_error

// スキーマ・フラグメント抽出
WITH data, allowed_schemes, fragment_required_schemes, id_error,
     CASE WHEN id_error IS NULL AND contains(data.id, ':') 
          THEN split(data.id, ':')[1] 
          ELSE null 
     END as scheme,
     CASE WHEN id_error IS NULL AND contains(data.id, '#') 
          THEN split(data.id, '#')[2] 
          ELSE '' 
     END as fragment

// スキーマ検証
WITH data, fragment_required_schemes, id_error, scheme, fragment,
     CASE 
       WHEN id_error IS NULL AND scheme IS NOT NULL AND NOT scheme IN allowed_schemes 
         THEN 'Invalid scheme \'' + scheme + '\'. Allowed: file, http, https, requirement, test, document'
       ELSE null
     END as scheme_error

// フラグメント必須チェック
WITH data, id_error, scheme, fragment, scheme_error,
     CASE 
       WHEN id_error IS NULL AND scheme_error IS NULL AND scheme IN fragment_required_schemes AND fragment = ''
         THEN 'Fragment is required for scheme \'' + scheme + '\'. Use format like ' + scheme + ':///path#FRAGMENT'
       ELSE null
     END as fragment_required_error

// フラグメントパターン検証
WITH data, id_error, scheme, fragment, scheme_error, fragment_required_error,
     CASE 
       WHEN id_error IS NULL AND scheme_error IS NULL AND fragment_required_error IS NULL AND fragment <> '' THEN
         CASE 
           WHEN scheme = 'file' AND NOT fragment =~ '^L\\d+(-L\\d+)?$' 
             THEN 'Invalid file fragment. Expected: L10 or L10-L25'
           WHEN scheme = 'requirement' AND NOT fragment =~ '^REQ-[A-Z0-9]+-\\d+$' 
             THEN 'Invalid requirement fragment. Expected: REQ-AUTH-001'
           WHEN scheme = 'test' AND NOT fragment =~ '^TEST-[A-Z0-9]+-\\d+$' 
             THEN 'Invalid test fragment. Expected: TEST-AUTH-001'
           WHEN scheme = 'document' AND NOT fragment =~ '^(section|page)-[a-zA-Z0-9-]+$' 
             THEN 'Invalid document fragment. Expected: section-auth or page-10'
           ELSE null
         END
       ELSE null
     END as fragment_pattern_error

// URI形式検証（プロジェクト形式）
WITH data, id_error, scheme_error, fragment_required_error, fragment_pattern_error,
     CASE 
       WHEN id_error IS NULL AND scheme_error IS NULL AND fragment_required_error IS NULL AND fragment_pattern_error IS NULL THEN
         CASE 
           WHEN data.id =~ '^<[a-zA-Z0-9_-]+>/srs/.+$' THEN null
           ELSE 'URI must match pattern: <project>/srs/path'
         END
       ELSE null
     END as format_error

WITH [id_error, scheme_error, fragment_required_error, fragment_pattern_error, format_error] as all_errors
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
         END
} as result