/**
 * DuckDB Repository
 * DuckDB接続と基本操作を提供
 */

import type { QueryResult, QuerySuccess, QueryError, SnapshotInfo } from "../../domain/types.ts";

// 依存性の型定義
export type DuckDBConnection = {
  runAndReadAll: (query: string) => Promise<{
    getRows: () => any[][];
    columnCount: number;
    columnName: (index: number) => string | null;
  }>;
  run: (query: string) => Promise<void>;
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
      const result = await connection.run(query).then(
        () => ({ success: true as const, data: [], rowCount: 0, columns: [] }),
        (err) => ({
          success: false as const,
          error: err instanceof Error ? err.message : String(err),
          code: "QUERY_ERROR" as const
        })
      );
      return result;
    }
    
    // SELECT操作
    const result = await connection.runAndReadAll(query).then(
      (reader) => {
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
        
        return {
          success: true as const,
          data,
          rowCount: rows.length,
          columns
        };
      },
      (err) => ({
        success: false as const,
        error: err instanceof Error ? err.message : String(err),
        code: "QUERY_ERROR" as const
      })
    );
    
    return result;
  }
  
  async function getSnapshots(catalog: string): Promise<SnapshotInfo[]> {
    const result = await executeQuery(`SELECT * FROM ducklake_snapshots('${catalog}')`);
    
    if (!result.success) {
      return [];
    }
    
    return result.data.map((row) => ({
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
