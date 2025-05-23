/**
 * Execute Query Command
 * 
 * クエリ実行に関するコマンド関数群
 * 規約準拠: throw文禁止、共用体型エラーハンドリング、try-catch禁止
 */

import type { QueryResult } from '../../domain/entities/queryResult';
import { createQueryRepository } from '../../infrastructure/factories/repositoryFactory';

// エラー型定義（Tagged Union）
type RepositoryCreationError = {
  status: "repository_creation_error";
  message: string;
};

type QueryExecutionError = {
  status: "query_execution_error";
  message: string;
  queryName: string;
};

type RetryTimeoutError = {
  status: "retry_timeout_error";
  message: string;
  attempts: number;
  maxRetries: number;
};

// 共用体型
type ExecuteQueryResult<T> = QueryResult<T> | RepositoryCreationError | QueryExecutionError;
type ExecuteQueryWithRetryResult<T> = QueryResult<T> | RetryTimeoutError | QueryExecutionError;

/**
 * 単一クエリを実行する
 * 規約準拠: throw文禁止、共用体型エラーハンドリング
 */
export async function executeQuery(
  connection: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<ExecuteQueryResult<any>> {
  // リポジトリ作成を安全に実行
  const repositoryResult = await createQueryRepositorySafely();
  if (repositoryResult.status === "repository_creation_error") {
    return repositoryResult;
  }
  
  // クエリ実行を安全に実行
  const queryResult = await repositoryResult.data.executeQuery(connection, queryName, params);
  
  // 既にQueryResult型なのでそのまま返す
  return queryResult;
}

/**
 * リポジトリを安全に作成する内部関数
 */
async function createQueryRepositorySafely(): Promise<{ status: "success"; data: any } | RepositoryCreationError> {
  const repository = await createQueryRepository();
  
  if (!repository) {
    return {
      status: "repository_creation_error",
      message: "クエリリポジトリの作成に失敗しました"
    };
  }
  
  return { status: "success", data: repository };
}

/**
 * クエリをリトライ付きで実行する
 * 規約準拠: try-catch禁止、new Error禁止、共用体型エラーハンドリング
 */
export async function executeQueryWithRetry(
  connection: any,
  queryName: string,
  params: Record<string, any> = {},
  maxRetries: number = 3,
  retryDelay: number = 1000
): Promise<ExecuteQueryWithRetryResult<any>> {
  let lastErrorMessage = "";
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const result = await executeQuery(connection, queryName, params);
    
    // 成功時は即座に返す
    if (result.status === "success" || result.success) {
      return result;
    }
    
    // エラーメッセージを記録
    lastErrorMessage = getErrorMessage(result);
    
    // 最後の試行でなければ、遅延を入れて再試行
    if (attempt < maxRetries - 1) {
      await delay(retryDelay);
    }
  }
  
  // 全試行失敗時
  return {
    status: "retry_timeout_error",
    message: `${maxRetries}回の試行後に失敗しました: ${lastErrorMessage}`,
    attempts: maxRetries,
    maxRetries
  };
}

/**
 * エラーメッセージを安全に取得する内部関数
 */
function getErrorMessage(result: any): string {
  if (result.error) return result.error;
  if (result.message) return result.message;
  return "不明なエラー";
}

/**
 * 遅延を作成する内部関数（Promise版setTimeout）
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 複数のクエリをバッチで実行する
 * 規約準拠: 共用体型エラーハンドリング
 */
export async function executeBatchQueries(
  connection: any,
  queries: Array<{ queryName: string; params: Record<string, any> }>
): Promise<QueryResult<any[]>> {
  const results: any[] = [];
  const errors: string[] = [];
  
  for (const query of queries) {
    const result = await executeQuery(connection, query.queryName, query.params);
    
    // 成功判定を統一
    if ((result.success === true) || (result.status === "success")) {
      const data = result.data || result;
      results.push(data);
    } else {
      const errorMessage = getErrorMessage(result);
      errors.push(`${query.queryName}: ${errorMessage}`);
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
 * 規約準拠: try-catch禁止、共用体型エラーハンドリング
 */
export async function executeQueryWithProgress(
  connection: any,
  queryName: string,
  params: Record<string, any> = {},
  onProgress?: (message: string) => void
): Promise<ExecuteQueryResult<any>> {
  onProgress?.(`クエリ "${queryName}" の実行を開始します...`);
  
  // リポジトリ作成を安全に実行
  const repositoryResult = await createQueryRepositorySafely();
  if (repositoryResult.status === "repository_creation_error") {
    onProgress?.(`リポジトリの初期化に失敗しました: ${repositoryResult.message}`);
    return repositoryResult;
  }
  
  onProgress?.(`リポジトリを初期化しました`);
  
  // クエリ実行を安全に実行
  const result = await repositoryResult.data.executeQuery(connection, queryName, params);
  
  // 結果に応じた進捗報告
  if ((result.success === true) || (result.status === "success")) {
    onProgress?.(`クエリ実行が正常に完了しました`);
  } else {
    const errorMessage = getErrorMessage(result);
    onProgress?.(`クエリ実行が失敗しました: ${errorMessage}`);
  }
  
  return result;
}

/**
 * クエリ実行のキャンセルをサポートする
 * 規約準拠: try-catch禁止、Promise内でのエラーハンドリング改善
 */
export async function executeQueryWithCancel(
  connection: any,
  queryName: string,
  params: Record<string, any> = {},
  abortSignal?: AbortSignal
): Promise<ExecuteQueryResult<any>> {
  if (abortSignal?.aborted) {
    return {
      success: false,
      error: 'クエリ実行がキャンセルされました'
    };
  }
  
  return new Promise(async (resolve) => {
    // AbortSignalリスナーの設定
    const onAbort = () => {
      resolve({
        success: false,
        error: 'クエリ実行がキャンセルされました'
      });
    };
    
    abortSignal?.addEventListener('abort', onAbort);
    
    // クエリ実行（既に安全にラップ済み）
    const result = await executeQuery(connection, queryName, params);
    resolve(result);
    
    // リスナーをクリーンアップ
    abortSignal?.removeEventListener('abort', onAbort);
  });
}

/**
 * クエリの実行時間を計測する
 * 規約準拠: try-catch禁止、共用体型エラーハンドリング
 */
export async function executeQueryWithTiming(
  connection: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<QueryResult<{ data: any; executionTime: number }>> {
  const startTime = performance.now();
  
  const result = await executeQuery(connection, queryName, params);
  const executionTime = performance.now() - startTime;
  
  // 成功時は実行時間を追加
  if ((result.success === true) || (result.status === "success")) {
    const data = result.data || result;
    return {
      success: true,
      data: {
        data,
        executionTime
      }
    };
  } else {
    // エラー時はそのまま返す（型キャストで対応）
    return result as QueryResult<{ data: any; executionTime: number }>;
  }
}
