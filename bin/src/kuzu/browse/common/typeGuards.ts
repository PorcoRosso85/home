/**
 * CONVENTION.yaml準拠の型判定関数
 * 規約: Tagged Unionパターンマッチによる明示的分岐
 */

import type { BaseError } from './types';

/**
 * エラー結果かどうかを判定する型ガード関数
 * 規約準拠: プロパティ存在チェックによる分岐
 */
export const isErrorResult = (result: any): result is BaseError => 
  result && typeof result === 'object' && 'code' in result && 'message' in result;

/**
 * 成功結果かどうかを判定する型ガード関数
 * 規約準拠: プロパティ存在チェックによる分岐
 */
export const isSuccessResult = (result: any): boolean => 
  result && typeof result === 'object' && 'data' in result;

/**
 * バージョン機能専用型ガード
 */
export const isVersionStatesError = (result: any): boolean =>
  isErrorResult(result);

export const isVersionStatesSuccess = (result: any): boolean =>
  isSuccessResult(result);

/**
 * LocationURI機能専用型ガード
 */
export const isLocationUrisError = (result: any): boolean =>
  isErrorResult(result);

export const isLocationUrisSuccess = (result: any): boolean =>
  isSuccessResult(result);

/**
 * 結果を処理する汎用関数
 * 規約準拠: パターンマッチ風の明示的分岐
 */
export const handleResult = <T, R>(
  result: T,
  onSuccess: (data: any) => R,
  onError: (error: BaseError) => R
): R => {
  return isErrorResult(result) 
    ? onError(result)
    : onSuccess((result as any).data);
};
