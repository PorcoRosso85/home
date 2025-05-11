/**
 * Query Executor - クエリ実行API
 * 
 * クエリの実行に特化したインターフェース
 */

import type { QueryResult } from '../domain/entities/queryResult';
import { createQueryRepository } from '../infrastructure/factories/repositoryFactory';
import type { QueryRepository } from '../domain/repositories/queryRepository';

/**
 * クエリ実行に関する統一インターフェース
 */
export type QueryExecutor = {
  /**
   * 単一クエリを実行する
   */
  execute: (queryName: string, params?: Record<string, any>) => Promise<QueryResult<any>>;
  
  /**
   * 複数のクエリを連続実行する
   */
  executeSequence: (queries: Array<{ queryName: string; params: Record<string, any> }>) => Promise<QueryResult<any[]>>;
  
  /**
   * トランザクション内でクエリを実行する
   */
  executeInTransaction: (queries: Array<{ queryName: string; params: Record<string, any> }>) => Promise<QueryResult<any[]>>;
  
  /**
   * 結果をキャッシュしてクエリを実行する
   */
  executeWithCache: (queryName: string, params?: Record<string, any>, ttl?: number) => Promise<QueryResult<any>>;
  
  /**
   * クエリの実行計画を取得する
   */
  explain: (queryName: string, params?: Record<string, any>) => Promise<QueryResult<any>>;
  
  /**
   * クエリの実行統計を取得する
   */
  getExecutionStats: () => Promise<QueryResult<any>>;
  
  /**
   * 利用可能なクエリのリストを取得する
   */
  listAvailableQueries: () => Promise<QueryResult<string[]>>;
  
  /**
   * クエリの内容を取得する（確認用）
   */
  getQueryContent: (queryName: string) => Promise<QueryResult<string>>;
};

/**
 * QueryExecutorの実装
 */
export async function createQueryExecutor(connection: any): Promise<QueryExecutor> {
  const repository = await createQueryRepository();
  const queryCache = new Map<string, { data: any; timestamp: number }>();
  
  return {
    async execute(queryName: string, params?: Record<string, any>): Promise<QueryResult<any>> {
      try {
        return await repository.executeQuery(connection, queryName, params);
      } catch (error) {
        return {
          success: false,
          error: `Failed to execute query "${queryName}": ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async executeSequence(queries: Array<{ queryName: string; params: Record<string, any> }>): Promise<QueryResult<any[]>> {
      try {
        const results: any[] = [];
        
        for (const query of queries) {
          const result = await this.execute(query.queryName, query.params);
          
          if (!result.success) {
            return {
              success: false,
              error: `Failed to execute query "${query.queryName}" in sequence: ${result.error}`
            };
          }
          
          results.push(result.data);
        }
        
        return {
          success: true,
          data: results
        };
      } catch (error) {
        return {
          success: false,
          error: `Failed to execute query sequence: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async executeInTransaction(queries: Array<{ queryName: string; params: Record<string, any> }>): Promise<QueryResult<any[]>> {
      try {
        // トランザクション開始
        const beginResult = await this.execute('begin_transaction');
        if (!beginResult.success) {
          return {
            success: false,
            error: `Failed to begin transaction: ${beginResult.error}`
          };
        }
        
        const results: any[] = [];
        
        try {
          // クエリを順次実行
          for (const query of queries) {
            const result = await this.execute(query.queryName, query.params);
            
            if (!result.success) {
              // エラー発生時はロールバック
              await this.execute('rollback_transaction');
              return {
                success: false,
                error: `Transaction failed at query "${query.queryName}": ${result.error}`
              };
            }
            
            results.push(result.data);
          }
          
          // コミット
          const commitResult = await this.execute('commit_transaction');
          if (!commitResult.success) {
            await this.execute('rollback_transaction');
            return {
              success: false,
              error: `Failed to commit transaction: ${commitResult.error}`
            };
          }
          
          return {
            success: true,
            data: results
          };
        } catch (error) {
          // エラー時はロールバック
          await this.execute('rollback_transaction');
          throw error;
        }
      } catch (error) {
        return {
          success: false,
          error: `Transaction execution failed: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async executeWithCache(queryName: string, params?: Record<string, any>, ttl: number = 60000): Promise<QueryResult<any>> {
      try {
        const cacheKey = `${queryName}:${JSON.stringify(params)}`;
        const cached = queryCache.get(cacheKey);
        
        // キャッシュが有効かチェック
        if (cached && (Date.now() - cached.timestamp) < ttl) {
          return {
            success: true,
            data: cached.data
          };
        }
        
        // キャッシュがない、または期限切れの場合は実行
        const result = await this.execute(queryName, params);
        
        // 成功時はキャッシュに保存
        if (result.success && result.data !== undefined) {
          queryCache.set(cacheKey, {
            data: result.data,
            timestamp: Date.now()
          });
        }
        
        return result;
      } catch (error) {
        return {
          success: false,
          error: `Failed to execute query with cache: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async explain(queryName: string, params?: Record<string, any>): Promise<QueryResult<any>> {
      try {
        // クエリの内容を取得
        const queryResult = await repository.getQuery(queryName);
        if (!queryResult.success) {
          return {
            success: false,
            error: `Failed to get query for explanation: ${queryResult.error}`
          };
        }
        
        // EXPLAINを付与したクエリを実行
        const explainQuery = `EXPLAIN ${queryResult.data}`;
        
        // パラメータを含むクエリを作成
        let finalQuery = explainQuery;
        if (params && Object.keys(params).length > 0) {
          const browserRepo = await import('../infrastructure/repositories/browserQueryRepository');
          finalQuery = browserRepo.buildParameterizedQuery(explainQuery, params);
        }
        
        // カスタム実行（EXPLAINがクエリ名として存在しない可能性があるため）
        const result = await connection.query(finalQuery);
        
        return {
          success: true,
          data: result
        };
      } catch (error) {
        return {
          success: false,
          error: `Failed to explain query: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async getExecutionStats(): Promise<QueryResult<any>> {
      try {
        // 実行統計情報を取得するクエリを実行
        return await this.execute('get_execution_stats');
      } catch (error) {
        return {
          success: false,
          error: `Failed to get execution stats: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async listAvailableQueries(): Promise<QueryResult<string[]>> {
      try {
        const queries = await repository.getAvailableQueries();
        return {
          success: true,
          data: queries
        };
      } catch (error) {
        return {
          success: false,
          error: `Failed to list available queries: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },
    
    async getQueryContent(queryName: string): Promise<QueryResult<string>> {
      try {
        return await repository.getQuery(queryName);
      } catch (error) {
        return {
          success: false,
          error: `Failed to get query content: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    }
  };
}

/**
 * グローバルQueryExecutorシングルトン
 */
let globalQueryExecutor: QueryExecutor | null = null;

/**
 * グローバルQueryExecutorを初期化する
 */
export async function initializeGlobalQueryExecutor(connection: any): Promise<QueryExecutor> {
  globalQueryExecutor = await createQueryExecutor(connection);
  return globalQueryExecutor;
}

/**
 * グローバルQueryExecutorを取得する
 */
export function getGlobalQueryExecutor(): QueryExecutor {
  if (!globalQueryExecutor) {
    throw new Error('QueryExecutor is not initialized. Call initializeGlobalQueryExecutor() first.');
  }
  return globalQueryExecutor;
}

/**
 * グローバルQueryExecutorをリセットする
 */
export function resetGlobalQueryExecutor(): void {
  globalQueryExecutor = null;
}

/**
 * 簡易ヘルパー関数：QueryExecutorの基本機能のみ
 */
export type SimpleQueryExecutor = {
  query: (queryName: string, params?: Record<string, any>) => Promise<QueryResult<any>>;
  listQueries: () => Promise<QueryResult<string[]>>;
  explainQuery: (queryName: string, params?: Record<string, any>) => Promise<QueryResult<any>>;
};

export async function createSimpleQueryExecutor(connection: any): Promise<SimpleQueryExecutor> {
  const executor = await createQueryExecutor(connection);
  
  return {
    query: executor.execute,
    listQueries: executor.listAvailableQueries,
    explainQuery: executor.explain
  };
}
