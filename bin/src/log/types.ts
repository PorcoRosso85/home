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