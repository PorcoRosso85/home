/**
 * バージョン形式の定数と正規表現パターン
 * 
 * TODO: プレフィックス'v'の扱いについての注釈を追加
 * TODO: SemVer仕様に基づく検証ルールを実装
 */

/**
 * バージョン文字列の表示形式
 * 注意: データベースには'v'プレフィックスなしで保存されているが、
 * 表示時には'v'プレフィックスを付ける
 */
export const VERSION_DISPLAY_PREFIX = 'v';

/**
 * バージョン文字列の検証に使用する正規表現
 * 基本的なセマンティックバージョニングの形式（x.y.z）を検証
 * 
 * 注意: プレフィックス'v'は任意で、内部処理時には無視される
 */
export const BASIC_VERSION_REGEX = /^v?(\d+)(\.\d+)*$/;

/**
 * 厳密なSemVer 2.0の検証に使用する正規表現
 * MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD] の形式を検証
 * 
 * 注意: プレフィックス'v'は任意で、内部処理時には無視される
 */
export const STRICT_SEMVER_REGEX = /^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;

/**
 * バージョンセグメントの最大値
 * 2^31 - 1 (符号付き32ビット整数の最大値) を使用
 */
export const MAX_SEGMENT_VALUE = 2147483647;

/**
 * バージョンの種類に関する定数
 */
export const VERSION_TYPES = {
  RELEASE: 'release',
  PRERELEASE: 'prerelease',
  BUILD: 'build'
} as const;

/**
 * バージョン比較の結果に関する定数
 */
export const VERSION_COMPARE_RESULT = {
  LESS_THAN: -1,
  EQUAL: 0,
  GREATER_THAN: 1
} as const;
