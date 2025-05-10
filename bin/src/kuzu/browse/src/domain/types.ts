/**
 * KuzuDB Parquet Viewer の基本型定義
 */

/**
 * データベース操作結果
 */
export interface DatabaseResult {
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * ステータスメッセージ
 */
export interface StatusMessage {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
}
