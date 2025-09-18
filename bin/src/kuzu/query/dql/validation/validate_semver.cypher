// SemVer形式検証（TypeScript semverValidator.ts の完全代替）
// パラメータ: $version, $strictMode (optional)
// 
// 機能:
// - 基本形式検証: x.y.z パターン
// - 厳密形式検証: SemVer 2.0仕様準拠
// - 'v'プレフィックス対応
// - セグメント詳細検証

WITH $version as input_version,
     COALESCE($strictMode, false) as strict_mode

// 'v'プレフィックス除去
WITH CASE 
       WHEN starts_with(input_version, 'v') THEN substring(input_version, 2, size(input_version)-1)
       ELSE input_version 
     END as clean_version,
     strict_mode

// 基本形式検証 (x.y.z パターン)
WITH clean_version,
     strict_mode,
     clean_version =~ '^\\d+(\.\\d+)*$' as basic_valid,
     clean_version =~ '^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-((?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\\.(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\\+([0-9a-zA-Z-]+(?:\\.[0-9a-zA-Z-]+)*))?$' as strict_valid

// セグメント検証
WITH clean_version, strict_mode, basic_valid, strict_valid,
     string_split(clean_version, '.') as segments

UNWIND segments as segment 
WITH segment, row_number() OVER() as segment_index,
     clean_version, strict_mode, basic_valid, strict_valid, segments
WITH clean_version, strict_mode, basic_valid, strict_valid, segments,
     collect(
       CASE 
         WHEN size(segment) = 0 THEN 'セグメント ' + toString(segment_index) + ' が空です'
         WHEN NOT segment =~ '^\\d+$' THEN 'セグメント ' + toString(segment_index) + ' に数値以外の文字が含まれています'
         WHEN size(segment) > 1 AND starts_with(segment, '0') THEN 'セグメント ' + toString(segment_index) + ' に不要な先頭のゼロが含まれています'
         ELSE null
       END
     ) as segment_errors

WITH clean_version, strict_mode, basic_valid, strict_valid,
     filter(error IN segment_errors WHERE error IS NOT null) as filtered_errors

RETURN {
  is_valid: CASE 
              WHEN strict_mode THEN strict_valid AND size(filtered_errors) = 0
              ELSE basic_valid AND size(filtered_errors) = 0
            END,
  original_version: $version,
  clean_version: clean_version,
  validation_mode: CASE WHEN strict_mode THEN 'strict' ELSE 'basic' END,
  errors: filtered_errors,
  format_details: {
    basic_format_valid: basic_valid,
    strict_semver_valid: strict_valid,
    segment_count: size(string_split(clean_version, '.')),
    has_v_prefix: starts_with($version, 'v')
  }
} as result