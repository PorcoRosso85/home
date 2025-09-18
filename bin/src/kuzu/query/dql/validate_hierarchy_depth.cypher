// 階層深度バリデーション（9階層以上エラー検出）
// パラメータ: $fullPath

WITH string_split(substring($fullPath, 2, size($fullPath)-1), "/") as parts
RETURN 
  CASE 
    WHEN size(parts) > 8 THEN false
    ELSE true 
  END as is_valid,
  size(parts) as actual_depth,
  8 as max_allowed_depth,
  CASE 
    WHEN size(parts) > 8 THEN "ERROR: Maximum hierarchy depth exceeded"
    ELSE "OK"
  END as validation_message;