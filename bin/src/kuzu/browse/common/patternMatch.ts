/**
 * CONVENTION.yaml準拠パターンマッチ処理関数
 * 規約: switch文による明示的分岐を優先
 */

import type { QueryExecutionResult, DatabaseConnectionResult } from '../types/queryTypes';

/**
 * クエリ実行結果のパターンマッチ処理
 * 規約準拠: switch文による網羅的分岐
 */
export function handleQueryResult(result: QueryExecutionResult): string {
  switch (result.status) {
    case "success":
      return `クエリ実行成功: ${JSON.stringify(result.data)}`;
    case "validation_error":
      return `バリデーションエラー [${result.field}]: ${result.message}`;
    case "execution_error":
      return `実行エラー [${result.code}]: ${result.message}`;
    case "connection_error":
      return `接続エラー: ${result.message}`;
    case "not_found":
      return `リソースが見つかりません: ${result.resource}`;
    default:
      // 網羅性チェック（TypeScriptでnever型になる）
      const _exhaustive: never = result;
      return `未処理のケース`;
  }
}

/**
 * データベース接続結果のパターンマッチ処理
 * 規約準拠: switch文による明示的分岐
 */
export function handleConnectionResult(result: DatabaseConnectionResult): string {
  switch (result.status) {
    case "connected":
      return `データベース接続成功`;
    case "connection_failed":
      return `接続失敗 [${result.code}]: ${result.message}`;
    case "invalid_config":
      return `設定エラー [${result.field}]: ${result.message}`;
    default:
      const _exhaustive: never = result;
      return `未処理の接続ケース`;
  }
}

/**
 * エラーレベルの判定
 * 規約準拠: switch文による分類
 */
export function getErrorSeverity(result: QueryExecutionResult): 'info' | 'warning' | 'error' | 'critical' {
  switch (result.status) {
    case "success":
      return 'info';
    case "validation_error":
      return 'warning';
    case "execution_error":
      return 'error';
    case "connection_error":
    case "not_found":
      return 'critical';
    default:
      const _exhaustive: never = result;
      return 'error';
  }
}
