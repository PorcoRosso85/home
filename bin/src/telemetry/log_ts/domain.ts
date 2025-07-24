/**
 * Domain layer for log module - pure business logic
 * 
 * Contains type definitions and pure functions for log data transformation.
 * No external dependencies.
 */

/**
 * ログデータの基本型定義
 * 
 * uri と message は必須フィールド
 * 追加のフィールドは自由に拡張可能
 */
export type LogData = {
  uri: string;
  message: string;
} & Record<string, unknown>;

/**
 * 辞書型データをJSONL形式の文字列に変換
 * 
 * Pure function that converts data to JSONL format (single-line JSON).
 * 
 * @param data 変換対象のデータ
 * @returns 改行を含まない1行のJSON文字列
 */
export function toJsonl(data: Record<string, unknown>): string {
  return JSON.stringify(data);
}