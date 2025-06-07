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
  data: SnapshotData<T>;
  
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
