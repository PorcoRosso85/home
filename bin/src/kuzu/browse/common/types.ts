/**
 * CONVENTION.yaml準拠の共通型定義
 * 規約: Result型パターン禁止、個別Tagged Union使用
 */

// 汎用的なエラーコード定数
export const ERROR_CODES = {
  DATABASE_ERROR: 'DATABASE_ERROR',
  QUERY_ERROR: 'QUERY_ERROR',
  TRANSFORM_ERROR: 'TRANSFORM_ERROR',
  CONNECTION_ERROR: 'CONNECTION_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  ANALYSIS_ERROR: 'ANALYSIS_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const;

export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];

// 基本エラー型
export type BaseError = {
  code: string;
  message: string;
};

// 各機能固有の成功/エラー型は個別ファイルで定義すること
// Result<T>型の使用は禁止 - CONVENTION.yaml準拠
