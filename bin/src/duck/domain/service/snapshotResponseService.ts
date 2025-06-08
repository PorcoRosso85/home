/**
 * Snapshot Response Service
 * スナップショットレスポンスの構築に関するビジネスロジック
 * 
 * このサービスは複数のDuckLakeデータソースを統合し、
 * 統一されたスナップショットレスポンスを構築する責務を持つ
 */

import type { 
  TableChangesMetadata, 
  SnapshotData, 
  ColumnInfo, 
  ParquetFileInfo 
} from "../ducklakeTypes.ts";
import type { SnapshotResponse } from "../types.ts";

/**
 * 複数のDuckLake APIレスポンスを統合してSnapshotResponseを構築
 * これはドメイン知識：「スナップショットとは何か」を定義する
 */
export function buildSnapshotResponse<T = Record<string, any>>(
  sources: {
    tableChangesMetadata: TableChangesMetadata;
    snapshotData: SnapshotData<T>;
    columnInfo?: ColumnInfo[];
    parquetFiles?: ParquetFileInfo[];
    tableName: string;
  }
): SnapshotResponse<T> {
  const { tableChangesMetadata, snapshotData, columnInfo, parquetFiles, tableName } = sources;
  
  // ビジネスルール：スキーマ情報がない場合のデフォルト構造
  const tableSchema = columnInfo && columnInfo.length > 0
    ? {
        name: tableName,
        columns: columnInfo.map(col => ({
          name: col.column_name,
          type: col.data_type
        }))
      }
    : { name: tableName, columns: [] };
  
  // ビジネスルール：operation_typesの正規化
  const operationTypes = tableChangesMetadata.operation_types
    ? tableChangesMetadata.operation_types.split(',').sort()
    : [];
  
  // オプショナルなファイル情報
  const filePaths = parquetFiles
    ? parquetFiles.map(f => f.path)
    : undefined;
  
  return {
    version: Number(tableChangesMetadata.snapshot_id),
    timestamp: new Date().toISOString(),
    operation_types: operationTypes,
    table_schema: tableSchema,
    snapshotData: snapshotData,
    metadata: {
      row_count: snapshotData.length,
      total_changes: Number(tableChangesMetadata.total_changes || 0),
      insert_count: Number(tableChangesMetadata.insert_count || 0),
      update_count: Number(tableChangesMetadata.update_count || 0),
      delete_count: Number(tableChangesMetadata.delete_count || 0),
      ...(filePaths && { file_paths: filePaths })
    }
  };
}

/**
 * スナップショットレスポンスの検証
 * ビジネスルール：有効なスナップショットレスポンスの条件
 */
export function validateSnapshotResponse<T>(response: SnapshotResponse<T>): boolean {
  return (
    response.version > 0 &&
    Array.isArray(response.snapshotData) &&
    Array.isArray(response.operation_types) &&
    response.metadata.row_count >= 0 &&
    response.metadata.total_changes >= 0
  );
}

/**
 * スナップショットレスポンスの比較
 * ビジネスロジック：2つのスナップショット間の差分を計算
 */
export function compareSnapshotResponses<T>(
  older: SnapshotResponse<T>,
  newer: SnapshotResponse<T>
): {
  versionDiff: number;
  rowCountDiff: number;
  hasSchemaChange: boolean;
} {
  return {
    versionDiff: newer.version - older.version,
    rowCountDiff: newer.metadata.row_count - older.metadata.row_count,
    hasSchemaChange: JSON.stringify(older.table_schema) !== JSON.stringify(newer.table_schema)
  };
}
