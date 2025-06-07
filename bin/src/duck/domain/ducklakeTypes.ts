/**
 * DuckLake API Response Types
 * DuckLakeの各APIが返す純粋な型定義
 */

// 1. table_changes()の返却型
export type TableChangesRow = {
  snapshot_id: bigint;
  rowid: bigint;
  change_type: 'insert' | 'update_preimage' | 'update_postimage' | 'delete';
  // 以降はテーブルのカラムが動的に追加される
  [columnName: string]: any;
};

// table_changes()の集計結果型
export type TableChangesMetadata = {
  snapshot_id: string;  // MIN(snapshot_id)
  total_changes: string;  // COUNT(DISTINCT rowid)
  insert_count: string;
  update_count: string;
  delete_count: string;
  operation_types: string;  // GROUP_CONCAT(DISTINCT change_type)
};

// 2. AT (VERSION => n)の返却型
// これは完全に動的（テーブルスキーマに依存）
export type SnapshotData<T = Record<string, any>> = T[];

// 3. information_schema.columnsの返却型
export type ColumnInfo = {
  column_name: string;
  data_type: string;
  is_nullable: string;
  column_default: string | null;
  ordinal_position: number;
  // 他のinformation_schemaカラム...
};

// 4. ducklake_snapshots()の返却型
export type DuckLakeSnapshot = {
  snapshot_id: bigint;
  snapshot_time: string;  // timestamp with time zone
  schema_version: bigint;
  changes: Record<string, string[]>;  // {tables_created: ['main.tbl'], ...}
};

// 5. fileRepositoryの返却型
export type ParquetFileInfo = {
  path: string;
  size: number;
  type: 'data' | 'delete';
  createdAt: string;
  name: string;
};
