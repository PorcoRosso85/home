// ログ型定義
export type LogRow = {
  // 必須フィールド
  code: string;  // 3桁の数字（000-999）
  error: Record<string, unknown>;  // エラーオブジェクト
  
  // 任意フィールド
  id?: number;
  timestamp?: Date | string;
  level?: string;
  message?: string;
  metadata?: unknown;
  
  // その他の任意フィールド
  [key: string]: unknown;
};
