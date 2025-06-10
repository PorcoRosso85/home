/**
 * DuckDB Repository
 * DuckDB接続と基本操作を提供
 */

import type { QueryResult, QueryData, QueryError, SnapshotInfo } from "../../domain/types.ts";
import { isQueryError } from "../../domain/types.ts";

// 依存性の型定義
export type DuckDBConnection = {
  runAndReadAll: (query: string) => Promise<{
    getRows: () => any[][];
    columnCount: number;
    columnName: (index: number) => string | null;
  }>;
  run: (query: string) => Promise<any>; // DuckDBMaterializedResultを返す
};

export type DuckDBDependencies = {
  connection: DuckDBConnection;
};

// リポジトリインターフェース
export type DuckDBRepository = {
  executeQuery: (query: string) => Promise<QueryResult>;
  getSnapshots: (catalog: string) => Promise<SnapshotInfo[]>;
  attachDuckLake: (name: string, metadataPath: string, dataPath: string) => Promise<QueryResult>;
  detachDuckLake: (name: string) => Promise<QueryResult>;
  // DuckLake公式関数（規約に従いcamelCase）
  ducklakeTableChanges: (catalog: string, tableName: string, startSnapshot: number, endSnapshot: number) => Promise<QueryResult>;
  ducklakeTableInsertions: (catalog: string, tableName: string, startSnapshot: number, endSnapshot: number) => Promise<QueryResult>;
  ducklakeTableDeletions: (catalog: string, tableName: string, startSnapshot: number, endSnapshot: number) => Promise<QueryResult>;
  ducklakeTableInfo: (catalog: string) => Promise<QueryResult>;
  ducklakeCleanupOldFiles: (catalog: string) => Promise<QueryResult>;
  ducklakeExpireSnapshots: (catalog: string, versions?: number[], olderThan?: string) => Promise<QueryResult>;
  ducklakeMergeAdjacentFiles: (catalog: string, tableName?: string, targetSizeMb?: number) => Promise<QueryResult>;
};

// 高階関数による依存性注入
export function createDuckDBRepository(deps: DuckDBDependencies): DuckDBRepository {
  const { connection } = deps;
  
  async function executeQuery(query: string): Promise<QueryResult> {
    // 結果を返すクエリかどうかを判定
    const isSelectQuery = query.trim().toUpperCase().startsWith("SELECT") ||
                         query.trim().toUpperCase().startsWith("FROM") ||
                         query.trim().toUpperCase().startsWith("SHOW") ||
                         query.trim().toUpperCase().startsWith("DESCRIBE");
    
    if (!isSelectQuery) {
      // DML/DDL操作
      try {
        await connection.run(query);
        // 成功時は空のデータを返す
        return { rows: [], rowCount: 0, columns: [] };
      } catch (err) {
        // エラー時はエラー型を返す
        return {
          code: "QUERY_ERROR",
          message: err instanceof Error ? err.message : String(err),
          query: query,
          details: err
        };
      }
    }
    
    // SELECT操作
    try {
      const reader = await connection.runAndReadAll(query);
      const rows = reader.getRows();
      const columnCount = reader.columnCount;
      const columns: string[] = [];
      
      for (let i = 0; i < columnCount; i++) {
        columns.push(reader.columnName(i) || `col_${i}`);
      }
      
      const data = rows.map((row) => {
        const obj: Record<string, any> = {};
        columns.forEach((name, idx) => {
          const value = row[idx];
          // BigIntをNumber型に変換（JSON.stringifyのため）
          if (typeof value === 'bigint') {
            // 安全な範囲内ならNumberに、超える場合は文字列に変換
            if (value <= Number.MAX_SAFE_INTEGER && value >= Number.MIN_SAFE_INTEGER) {
              obj[name] = Number(value);
            } else {
              obj[name] = value.toString();
            }
          } else {
            obj[name] = value;
          }
        });
        return obj;
      });
      
      // 成功時は直接データを返す
      return {
        rows: data,
        rowCount: rows.length,
        columns
      };
    } catch (err) {
      // エラー時はエラー型を返す
      return {
        code: "QUERY_ERROR",
        message: err instanceof Error ? err.message : String(err),
        query: query,
        details: err
      };
    }
  }
  
  async function getSnapshots(catalog: string): Promise<SnapshotInfo[]> {
    // 公式関数 ducklake_snapshots() を使用
    const result = await executeQuery(`SELECT * FROM ducklake_snapshots('${catalog}')`);
    
    // エラーチェック（規約準拠）
    if (isQueryError(result)) {
      return [];
    }
    
    return result.rows.map((row) => ({
      snapshotId: row.snapshot_id || 0,
      timestamp: row.snapshot_time || "",
      tableCount: row.table_count || 0,
      description: row.description || ""
    }));
  }
  
  async function attachDuckLake(
    name: string,
    metadataPath: string,
    dataPath: string
  ): Promise<QueryResult> {
    const query = `ATTACH 'ducklake:${metadataPath}' AS ${name} (DATA_PATH '${dataPath}')`;
    return executeQuery(query);
  }
  
  async function detachDuckLake(name: string): Promise<QueryResult> {
    const query = `DETACH ${name}`;
    return executeQuery(query);
  }
  
  // DuckLake公式関数の実装
  async function ducklakeTableChanges(
    catalog: string,
    tableName: string,
    startSnapshot: number,
    endSnapshot: number
  ): Promise<QueryResult> {
    const query = `SELECT * FROM ${catalog}.table_changes('${tableName}', ${startSnapshot}, ${endSnapshot})`;
    return executeQuery(query);
  }
  
  async function ducklakeTableInsertions(
    catalog: string,
    tableName: string,
    startSnapshot: number,
    endSnapshot: number
  ): Promise<QueryResult> {
    const query = `SELECT * FROM ${catalog}.table_insertions('${tableName}', ${startSnapshot}, ${endSnapshot})`;
    return executeQuery(query);
  }
  
  async function ducklakeTableDeletions(
    catalog: string,
    tableName: string,
    startSnapshot: number,
    endSnapshot: number
  ): Promise<QueryResult> {
    const query = `SELECT * FROM ${catalog}.table_deletions('${tableName}', ${startSnapshot}, ${endSnapshot})`;
    return executeQuery(query);
  }
  
  async function ducklakeTableInfo(catalog: string): Promise<QueryResult> {
    const query = `SELECT * FROM ducklake_table_info('${catalog}')`;
    return executeQuery(query);
  }
  
  async function ducklakeCleanupOldFiles(catalog: string): Promise<QueryResult> {
    const query = `SELECT ducklake_cleanup_old_files('${catalog}')`;
    return executeQuery(query);
  }
  
  async function ducklakeExpireSnapshots(
    catalog: string,
    versions?: number[],
    olderThan?: string
  ): Promise<QueryResult> {
    let query: string;
    
    if (versions && versions.length > 0) {
      const versionList = versions.join(',');
      query = `SELECT ducklake_expire_snapshots('${catalog}', ARRAY[${versionList}])`;
    } else if (olderThan) {
      query = `SELECT ducklake_expire_snapshots('${catalog}', older_than => '${olderThan}')`;
    } else {
      // エラー型を返す
      return {
        code: "INVALID_PARAMETERS",
        message: "[DuckLake Expire Snapshots] Either versions or olderThan must be specified",
        query: "ducklake_expire_snapshots",
        details: { catalog, versions, olderThan }
      };
    }
    
    return executeQuery(query);
  }
  
  async function ducklakeMergeAdjacentFiles(
    catalog: string,
    tableName?: string,
    targetSizeMb?: number
  ): Promise<QueryResult> {
    const args = [`'${catalog}'`];
    
    if (tableName) {
      args.push(`'${tableName}'`);
    }
    
    if (targetSizeMb) {
      args.push(`target_size_mb => ${targetSizeMb}`);
    }
    
    const query = `SELECT ducklake_merge_adjacent_files(${args.join(', ')})`;
    return executeQuery(query);
  }
  
  return {
    executeQuery,
    getSnapshots,
    attachDuckLake,
    detachDuckLake,
    ducklakeTableChanges,
    ducklakeTableInsertions,
    ducklakeTableDeletions,
    ducklakeTableInfo,
    ducklakeCleanupOldFiles,
    ducklakeExpireSnapshots,
    ducklakeMergeAdjacentFiles
  };
}