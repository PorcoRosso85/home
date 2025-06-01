/**
 * CONVENTION.yaml準拠の統一エラーハンドリング
 * 規約: try/catch禁止、明示的分岐処理
 */

import type { BaseError, ErrorCode } from './types';

/**
 * エラー型を作成する関数
 * 規約準拠: 例外を投げずにエラー型を返却
 */
export const createError = (code: ErrorCode, message: string): BaseError => ({
  code,
  message
});

/**
 * 成功型を作成する関数 - ジェネリック版
 * 規約準拠: 明示的な成功型返却
 */
export const createSuccess = <T>(data: T) => ({
  data
});

/**
 * バージョン機能専用成功型作成
 */
export const createVersionStatesSuccess = (data: any[]) => ({
  data
});

/**
 * LocationURI機能専用成功型作成
 */
export const createLocationUrisSuccess = (data: any[]) => ({
  data
});

/**
 * エラーメッセージからエラーコードを分類する関数
 * 規約準拠: if/else分岐による明示的処理
 */
export const classifyError = (errorMessage: string): ErrorCode => {
  if (errorMessage.includes('database') || errorMessage.includes('connection')) {
    return 'DATABASE_ERROR';
  }
  if (errorMessage.includes('query') || errorMessage.includes('Query')) {
    return 'QUERY_ERROR';
  }
  if (errorMessage.includes('transform') || errorMessage.includes('map')) {
    return 'TRANSFORM_ERROR';
  }
  if (errorMessage.includes('analysis') || errorMessage.includes('claude')) {
    return 'ANALYSIS_ERROR';
  }
  if (errorMessage.includes('validation') || errorMessage.includes('valid')) {
    return 'VALIDATION_ERROR';
  }
  return 'UNKNOWN_ERROR';
};

/**
 * エラーメッセージを統一フォーマットで作成する関数
 */
export const formatErrorMessage = (operation: string, originalMessage: string): string => 
  `${operation}でエラーが発生しました: ${originalMessage}`;
