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
 * グラフノード
 */
export interface GraphNode {
  id: string | number;
  type: string;
  properties: Record<string, any>;
}

/**
 * グラフエッジ
 */
export interface GraphEdge {
  id?: string | number;
  type: string;
  source: string | number;
  target: string | number;
  properties?: Record<string, any>;
}

/**
 * ステータスメッセージ
 */
export interface StatusMessage {
  text: string;
  type: 'info' | 'success' | 'error' | 'loading';
}
