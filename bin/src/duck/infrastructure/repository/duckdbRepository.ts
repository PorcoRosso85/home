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
          obj[name] = row[idx];
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
    const result = await executeQuery(`SELECT * FROM ducklake_snapshots('${catalog}')`);
    
    // エラーチェック（規約準拠）
    if (isQueryError(result)) {
      return [];
    }
    
    return result.rows.map((row) => ({
      snapshotId: row.snapshot_id || 0,
      timestamp: row.committed_at || "",
      tableCount: row.table_count || 0,
      description: row.description
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
  
  return {
    executeQuery,
    getSnapshots,
    attachDuckLake,
    detachDuckLake
  };
}