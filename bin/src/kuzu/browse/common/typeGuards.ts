/**
 * CONVENTION.yaml準拠の型判定関数
 * 規約: Tagged Unionパターンマッチによる明示的分岐
 */

import type { Result, ErrorResult, Success } from './types';

/**
 * エラー結果かどうかを判定する型ガード関数
 * 規約準拠: プロパティ存在チェックによる分岐
 */
export const isErrorResult = <T>(result: Result<T>): result is ErrorResult => 
  'code' in result && 'message' in result;

/**
 * 成功結果かどうかを判定する型ガード関数
 * 規約準拠: プロパティ存在チェックによる分岐
 */
export const isSuccessResult = <T>(result: Result<T>): result is Success<T> => 
  'data' in result;

/**
 * 結果を処理する汎用関数
 * 規約準拠: パターンマッチ風の明示的分岐
 */
export const handleResult = <T, R>(
  result: Result<T>,
  onSuccess: (data: T) => R,
  onError: (error: ErrorResult) => R
): R => {
  return isErrorResult(result) 
    ? onError(result)
    : onSuccess(result.data);
};
