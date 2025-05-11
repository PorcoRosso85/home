/**
 * Query Client - 統一公開API
 * 
 * KuzuDBへのアクセスを統一するクライアントインターフェース
 */

import type { QueryResult } from '../domain/entities/queryResult';
import { 
  executeQuery,
  executeQueryWithRetry,
  executeBatchQueries,
  executeQueryWithProgress,
  executeQueryWithCancel,
  executeQueryWithTiming
} from '../application/commands/executeQuery';
import {
  generateQueriesForEntity,
  generateAllQueries,
  generateQueryFromDefinition,
  generateQueryTemplate,
  generateQueriesWithProgress,
  validateQueryGenerationConfig,
  type EntityDefinition
} from '../application/commands/generateQueries';

/**
 * メインのQueryClientクラス（関数ベース）
 */
export type QueryClient = {
  /**
   * クエリ実行
   */
  executeQuery: (queryName: string, params?: Record<string, any>) => Promise<QueryResult<any>>;
  executeQueryWithRetry: (queryName: string, params?: Record<string, any>, maxRetries?: number, retryDelay?: number) => Promise<QueryResult<any>>;
  executeBatchQueries: (queries: Array<{ queryName: string; params: Record<string, any> }>) => Promise<QueryResult<any[]>>;
  executeQueryWithProgress: (queryName: string, params?: Record<string, any>, onProgress?: (message: string) => void) => Promise<QueryResult<any>>;
  executeQueryWithCancel: (queryName: string, params?: Record<string, any>, abortSignal?: AbortSignal) => Promise<QueryResult<any>>;
  executeQueryWithTiming: (queryName: string, params?: Record<string, any>) => Promise<QueryResult<{ data: any; executionTime: number }>>;
  
  /**
   * クエリ生成
   */
  generateQueriesForEntity: (entityPath: string, outputDir?: string) => Promise<QueryResult<void>>;
  generateAllQueries: (inputDir?: string, outputDir?: string) => Promise<QueryResult<number>>;
  generateQueryFromDefinition: (entityDefinition: EntityDefinition, templateType: string) => Promise<QueryResult<string>>;
  generateQueryTemplate: (
    entityType: 'node' | 'edge',
    templateType: 'create' | 'match' | 'update' | 'delete',
    tableName: string,
    properties: Record<string, { type: string; primary_key?: boolean }>,
    fromTable?: string,
    toTable?: string
  ) => Promise<QueryResult<string>>;
  generateQueriesWithProgress: (inputDir?: string, outputDir?: string, onProgress?: (message: string, total?: number, current?: number) => void) => Promise<QueryResult<number>>;
  validateQueryGenerationConfig: (inputDir: string, outputDir: string) => Promise<QueryResult<{ valid: boolean; issues: string[] }>>;
  
  /**
   * 接続管理
   */
  getConnection: () => any;
  setConnection: (connection: any) => void;
  isConnected: () => boolean;
};

/**
 * QueryClientを作成する
 */
export async function createQueryClient(connection?: any): Promise<QueryClient> {
  let _connection = connection;
  
  return {
    // クエリ実行メソッド
    async executeQuery(queryName: string, params?: Record<string, any>): Promise<QueryResult<any>> {
      if (!_connection) {
        return {
          success: false,
          error: 'Connection is not established'
        };
      }
      return executeQuery(_connection, queryName, params);
    },
    
    async executeQueryWithRetry(queryName: string, params?: Record<string, any>, maxRetries: number = 3, retryDelay: number = 1000): Promise<QueryResult<any>> {
      if (!_connection) {
        return {
          success: false,
          error: 'Connection is not established'
        };
      }
      return executeQueryWithRetry(_connection, queryName, params, maxRetries, retryDelay);
    },
    
    async executeBatchQueries(queries: Array<{ queryName: string; params: Record<string, any> }>): Promise<QueryResult<any[]>> {
      if (!_connection) {
        return {
          success: false,
          error: 'Connection is not established'
        };
      }
      return executeBatchQueries(_connection, queries);
    },
    
    async executeQueryWithProgress(queryName: string, params?: Record<string, any>, onProgress?: (message: string) => void): Promise<QueryResult<any>> {
      if (!_connection) {
        return {
          success: false,
          error: 'Connection is not established'
        };
      }
      return executeQueryWithProgress(_connection, queryName, params, onProgress);
    },
    
    async executeQueryWithCancel(queryName: string, params?: Record<string, any>, abortSignal?: AbortSignal): Promise<QueryResult<any>> {
      if (!_connection) {
        return {
          success: false,
          error: 'Connection is not established'
        };
      }
      return executeQueryWithCancel(_connection, queryName, params, abortSignal);
    },
    
    async executeQueryWithTiming(queryName: string, params?: Record<string, any>): Promise<QueryResult<{ data: any; executionTime: number }>> {
      if (!_connection) {
        return {
          success: false,
          error: 'Connection is not established'
        };
      }
      return executeQueryWithTiming(_connection, queryName, params);
    },
    
    // クエリ生成メソッド
    async generateQueriesForEntity(entityPath: string, outputDir?: string): Promise<QueryResult<void>> {
      return generateQueriesForEntity(entityPath, outputDir);
    },
    
    async generateAllQueries(inputDir?: string, outputDir?: string): Promise<QueryResult<number>> {
      return generateAllQueries(inputDir, outputDir);
    },
    
    async generateQueryFromDefinition(entityDefinition: EntityDefinition, templateType: string): Promise<QueryResult<string>> {
      return generateQueryFromDefinition(entityDefinition, templateType);
    },
    
    async generateQueryTemplate(
      entityType: 'node' | 'edge',
      templateType: 'create' | 'match' | 'update' | 'delete',
      tableName: string,
      properties: Record<string, { type: string; primary_key?: boolean }>,
      fromTable?: string,
      toTable?: string
    ): Promise<QueryResult<string>> {
      return generateQueryTemplate(entityType, templateType, tableName, properties, fromTable, toTable);
    },
    
    async generateQueriesWithProgress(inputDir?: string, outputDir?: string, onProgress?: (message: string, total?: number, current?: number) => void): Promise<QueryResult<number>> {
      return generateQueriesWithProgress(inputDir, outputDir, onProgress);
    },
    
    async validateQueryGenerationConfig(inputDir: string, outputDir: string): Promise<QueryResult<{ valid: boolean; issues: string[] }>> {
      return validateQueryGenerationConfig(inputDir, outputDir);
    },
    
    // 接続管理メソッド
    getConnection(): any {
      return _connection;
    },
    
    setConnection(connection: any): void {
      _connection = connection;
    },
    
    isConnected(): boolean {
      return _connection !== null && _connection !== undefined;
    }
  };
}

/**
 * グローバルQueryClientシングルトン
 */
let globalQueryClient: QueryClient | null = null;

/**
 * グローバルQueryClientを初期化する
 */
export async function initializeGlobalQueryClient(connection?: any): Promise<QueryClient> {
  if (!globalQueryClient) {
    globalQueryClient = await createQueryClient(connection);
  } else if (connection) {
    globalQueryClient.setConnection(connection);
  }
  return globalQueryClient;
}

/**
 * グローバルQueryClientを取得する
 */
export function getGlobalQueryClient(): QueryClient {
  if (!globalQueryClient) {
    throw new Error('QueryClient is not initialized. Call initializeGlobalQueryClient() first.');
  }
  return globalQueryClient;
}

/**
 * グローバルQueryClientをリセットする
 */
export function resetGlobalQueryClient(): void {
  globalQueryClient = null;
}
