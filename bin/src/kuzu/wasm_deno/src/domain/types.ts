// Kuzuで使用する基本的な型定義

// クエリ結果のJSON構造
export interface QueryResult {
  columns: string[];
  rows: any[][];
}

// Kuzuデータベース接続の抽象型
export interface KuzuConnection {
  execute: (query: string) => Promise<any>;
}

// Kuzu関連のエラー型
export interface KuzuError {
  message: string;
  code?: string;
}