/**
 * CONVENTION.yaml準拠の共通型定義
 * 規約: Result型パターン禁止、Tagged Union使用
 */

// 成功時の戻り値型
export type Success<T> = {
  data: T;
};

// エラー時の戻り値型
export type ErrorResult = {
  code: string;
  message: string;
};

// 共用体型（Tagged Union）
export type Result<T> = Success<T> | ErrorResult;

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
