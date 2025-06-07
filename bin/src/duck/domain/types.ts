/**
 * DuckLake Domain Types
 * 規約準拠：共用体型によるエラー処理
 */

// クエリ実行結果の共用体型
export type QuerySuccess = {
  success: true;
  data: any[];
  rowCount: number;
  columns: string[];
};

export type QueryError = {
  success: false;
  error: string;
  code: "QUERY_ERROR" | "CONNECTION_ERROR" | "VALIDATION_ERROR";
};

export type QueryResult = QuerySuccess | QueryError;

// スナップショット情報
export type SnapshotInfo = {
  snapshotId: number;
  timestamp: string;
  tableCount: number;
  description?: string;
};

// ファイル情報
export type FileInfo = {
  path: string;
  size: number;
  type: "data" | "delete";
  createdAt: string;
};

// DuckLake状態
export type DuckLakeStatus = {
  catalogName: string;
  snapshots: SnapshotInfo[];
  fileCount: number;
  totalSize: number;
};

// テーブル変更情報
export type TableChange = {
  snapshotId: number;
  rowId: number;
  changeType: "insert" | "update" | "delete";
  data: Record<string, any>;
};

// 結果判定ヘルパー
export function isQuerySuccess(result: QueryResult): result is QuerySuccess {
  return result.success === true;
}

export function isQueryError(result: QueryResult): result is QueryError {
  return result.success === false;
}
