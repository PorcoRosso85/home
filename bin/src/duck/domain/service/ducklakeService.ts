/**
 * DuckLake公式関数のラッパーサービス
 * 
 * DuckLakeの公式仕様に準拠した関数名のマッピングと
 * TypeScriptの命名規則への変換を提供
 */

import type {
  TableChangesRow,
  SnapshotData,
  DuckLakeSnapshot,
  DuckLakeTableInfo,
  DuckLakeCleanupResult,
  DuckLakeExpireResult,
  DuckLakeMergeResult
} from "../ducklakeTypes.ts";

// DuckLake公式関数名からTypeScript命名規則へのマッピング
export const DUCKLAKE_FUNCTION_MAPPING = {
  // スナップショット関連
  'ducklake_snapshots': 'ducklakeSnapshots',
  'ducklake_table_changes': 'ducklakeTableChanges',
  'ducklake_table_insertions': 'ducklakeTableInsertions',
  'ducklake_table_deletions': 'ducklakeTableDeletions',
  'ducklake_table_info': 'ducklakeTableInfo',
  
  // メンテナンス関連
  'ducklake_cleanup_old_files': 'ducklakeCleanupOldFiles',
  'ducklake_expire_snapshots': 'ducklakeExpireSnapshots',
  'ducklake_merge_adjacent_files': 'ducklakeMergeAdjacentFiles'
} as const;

// DuckLake関数の引数型定義
export type DuckLakeTableChangesParams = {
  catalog: string;
  tableName: string;
  startSnapshot: number | string;  // VERSION番号またはタイムスタンプ
  endSnapshot: number | string;
};

export type DuckLakeExpireParams = {
  catalog: string;
  versions?: number[];  // 削除する特定のバージョン
  olderThan?: string;   // この日時より古いものを削除
};

export type DuckLakeMergeParams = {
  catalog: string;
  tableName?: string;  // 特定のテーブルのみ（省略時は全テーブル）
  targetSizeMb?: number;  // 目標ファイルサイズ（MB）
};

// クエリビルダー関数
export function buildDuckLakeQuery(functionName: keyof typeof DUCKLAKE_FUNCTION_MAPPING, params: Record<string, any>): string {
  switch (functionName) {
    case 'ducklake_snapshots':
      return `SELECT * FROM ducklake_snapshots('${params.catalog}')`;
    
    case 'ducklake_table_changes':
      return `SELECT * FROM ${params.catalog}.table_changes('${params.tableName}', ${params.startSnapshot}, ${params.endSnapshot})`;
    
    case 'ducklake_table_insertions':
      return `SELECT * FROM ${params.catalog}.table_insertions('${params.tableName}', ${params.startSnapshot}, ${params.endSnapshot})`;
    
    case 'ducklake_table_deletions':
      return `SELECT * FROM ${params.catalog}.table_deletions('${params.tableName}', ${params.startSnapshot}, ${params.endSnapshot})`;
    
    case 'ducklake_table_info':
      return `SELECT * FROM ducklake_table_info('${params.catalog}')`;
    
    case 'ducklake_cleanup_old_files':
      return `SELECT ducklake_cleanup_old_files('${params.catalog}')`;
    
    case 'ducklake_expire_snapshots':
      if (params.versions) {
        const versionList = params.versions.join(',');
        return `SELECT ducklake_expire_snapshots('${params.catalog}', ARRAY[${versionList}])`;
      } else if (params.olderThan) {
        return `SELECT ducklake_expire_snapshots('${params.catalog}', older_than => '${params.olderThan}')`;
      }
      throw new Error("Either versions or olderThan must be specified");
    
    case 'ducklake_merge_adjacent_files':
      const args = [`'${params.catalog}'`];
      if (params.tableName) {
        args.push(`'${params.tableName}'`);
      }
      if (params.targetSizeMb) {
        args.push(`target_size_mb => ${params.targetSizeMb}`);
      }
      return `SELECT ducklake_merge_adjacent_files(${args.join(', ')})`;
    
    default:
      throw new Error(`Unknown DuckLake function: ${functionName}`);
  }
}

// バージョン指定のタイムトラベルクエリビルダー
export function buildTimeTravel(catalog: string, tableName: string, version: number): string {
  return `SELECT * FROM ${catalog}.${tableName} AT (VERSION => ${version})`;
}

// タイムスタンプ指定のタイムトラベルクエリビルダー
export function buildTimeTravelByTimestamp(catalog: string, tableName: string, timestamp: string): string {
  return `SELECT * FROM ${catalog}.${tableName} AT (TIMESTAMP => '${timestamp}')`;
}