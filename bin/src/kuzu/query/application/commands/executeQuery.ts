/**
 * Execute Query Command
 * 
 * クエリ実行に関するコマンド関数群
 */

import type { QueryResult } from '../../domain/entities/queryResult';
import { createQueryRepository } from '../../infrastructure/factories/repositoryFactory';

/**
 * 単一クエリを実行する
 */
export async function executeQuery(
  connection: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  try {
    const repository = await createQueryRepository();
    return await repository.executeQuery(connection, queryName, params);
  } catch (error) {
    return {
      success: false,
      error: `クエリ実行中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

/**
 * クエリをリトライ付きで実行する
 */
export async function executeQueryWithRetry(
  connection: any,
  queryName: string,
  params: Record<string, any> = {},
  maxRetries: number = 3,
  retryDelay: number = 1000
): Promise<QueryResult<any>> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = await executeQuery(connection, queryName, params);
      
      if (result.success) {
        return result;
      }
      
      lastError = new Error(result.error);
      
      // 最後の試行でなければ、遅延を入れて再試行
      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // 最後の試行でなければ、遅延を入れて再試行
      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
  }
  
  return {
    success: false,
    error: `${maxRetries}回の試行後に失敗しました: ${lastError?.message || '不明なエラー'}`
  };
}

/**
 * 複数のクエリをバッチで実行する
 */
export async function executeBatchQueries(
  connection: any,
  queries: Array<{ queryName: string; params: Record<string, any> }>
): Promise<QueryResult<any[]>> {
  const results: any[] = [];
  const errors: string[] = [];
  
  for (const query of queries) {
    const result = await executeQuery(connection, query.queryName, query.params);
    
    if (result.success) {
      results.push(result.data);
    } else {
      errors.push(`${query.queryName}: ${result.error}`);
    }
  }
  
  if (errors.length > 0) {
    return {
      success: false,
      error: `複数のクエリで失敗が発生しました: ${errors.join('; ')}`
    };
  }
  
  return {
    success: true,
    data: results
  };
}

/**
 * クエリの実行状況を報告する
 */
export async function executeQueryWithProgress(
  connection: any,
  queryName: string,
  params: Record<string, any> = {},
  onProgress?: (message: string) => void
): Promise<QueryResult<any>> {
  onProgress?.(`クエリ "${queryName}" の実行を開始します...`);
  
  try {
    const repository = await createQueryRepository();
    onProgress?.(`リポジトリを初期化しました`);
    
    const result = await repository.executeQuery(connection, queryName, params);
    
    if (result.success) {
      onProgress?.(`クエリ実行が正常に完了しました`);
    } else {
      onProgress?.(`クエリ実行が失敗しました: ${result.error}`);
    }
    
    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    onProgress?.(`エラーが発生しました: ${errorMessage}`);
    
    return {
      success: false,
      error: errorMessage
    };
  }
}

/**
 * クエリ実行のキャンセルをサポートする
 */
export async function executeQueryWithCancel(
  connection: any,
  queryName: string,
  params: Record<string, any> = {},
  abortSignal?: AbortSignal
): Promise<QueryResult<any>> {
  if (abortSignal?.aborted) {
    return {
      success: false,
      error: 'クエリ実行がキャンセルされました'
    };
  }
  
  return new Promise(async (resolve, reject) => {
    // AbortSignalリスナーの設定
    const onAbort = () => {
      resolve({
        success: false,
        error: 'クエリ実行がキャンセルされました'
      });
    };
    
    abortSignal?.addEventListener('abort', onAbort);
    
    try {
      const result = await executeQuery(connection, queryName, params);
      resolve(result);
    } catch (error) {
      resolve({
        success: false,
        error: error instanceof Error ? error.message : String(error)
      });
    } finally {
      // リスナーをクリーンアップ
      abortSignal?.removeEventListener('abort', onAbort);
    }
  });
}

/**
 * クエリの実行時間を計測する
 */
export async function executeQueryWithTiming(
  connection: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<QueryResult<{ data: any; executionTime: number }>> {
  const startTime = performance.now();
  
  try {
    const result = await executeQuery(connection, queryName, params);
    const executionTime = performance.now() - startTime;
    
    if (result.success) {
      return {
        success: true,
        data: {
          data: result.data,
          executionTime
        }
      };
    } else {
      return result as QueryResult<{ data: any; executionTime: number }>;
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    };
  }
}
