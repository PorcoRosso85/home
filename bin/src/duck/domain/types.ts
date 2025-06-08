/**
 * DuckLake Domain Types
 * 規約準拠：共用体型によるエラー処理
 */

// クエリ実行結果のデータ型
export type QueryData = {
  rows: any[];
  rowCount: number;
  columns: string[];
};

// クエリエラー型
export type QueryError = {
  code: "QUERY_ERROR" | "CONNECTION_ERROR" | "VALIDATION_ERROR";
  message: string;
  query?: string;
  details?: any;
};

// クエリ実行結果の共用体型（成功時は直接データ、エラー時はエラー型）
export type QueryResult = QueryData | QueryError;

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
  type: 'data' | 'delete';
  createdAt: string;
  timestamp?: string;
};

// DuckLake APIレスポンス型をインポート
import type { 
  TableChangesMetadata, 
  SnapshotData, 
  ColumnInfo, 
  ParquetFileInfo 
} from "./ducklakeTypes.ts";

// スナップショットレスポンススキーマ（完全版）
export type SnapshotResponse<T = Record<string, any>> = {
  // TableChangesMetadataから導出
  version: number;              // Number(metadata.snapshot_id)
  timestamp: string;            // new Date().toISOString()
  operation_types: string[];    // metadata.operation_types.split(',')
  
  // ColumnInfoから構築
  table_schema: {
    name: string;
    columns: Array<{
      name: string;      // column_name
      type: string;      // data_type
    }>;
  };
  
  // SnapshotData<T>をそのまま使用
  snapshotData: SnapshotData<T>;
  
  // 各種メタデータを数値変換して格納
  metadata: {
    row_count: number;          // data.length
    total_changes: number;      // Number(metadata.total_changes)
    insert_count: number;       // Number(metadata.insert_count)
    update_count: number;       // Number(metadata.update_count)
    delete_count: number;       // Number(metadata.delete_count)
    file_paths?: string[];      // ParquetFileInfo[].map(f => f.path)
  };
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

// 結果判定ヘルパー（規約準拠：プロパティチェックによる判定）
export function isQueryError(result: QueryResult): result is QueryError {
  return 'code' in result && 'message' in result;
}

export function isQueryData(result: QueryResult): result is QueryData {
  return 'rows' in result && 'rowCount' in result && 'columns' in result;
}