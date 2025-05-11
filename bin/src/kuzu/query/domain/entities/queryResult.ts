/**
 * クエリ結果エンティティ
 * 
 * KuzuDBクエリの実行結果を表現する型定義と関連関数
 */

/**
 * クエリ結果の基本構造
 */
export type QueryResult<T> = {
  success: boolean;
  data?: T;
  error?: string;
  available_queries?: string[];
};

/**
 * 成功時の結果を作成する
 */
export function createSuccessResult<T>(data: T): QueryResult<T> {
  return { success: true, data };
}

/**
 * エラー時の結果を作成する
 */
export function createErrorResult<T>(error: string, availableQueries?: string[]): QueryResult<T> {
  return {
    success: false,
    error,
    available_queries: availableQueries,
  };
}

/**
 * 結果が成功かどうかを判定する
 */
export function isSuccess<T>(result: QueryResult<T>): result is QueryResult<T> & { success: true; data: T } {
  return result.success === true && result.data !== undefined;
}

/**
 * 結果の成功判定（レガシー互換）
 */
export function getSuccess<T>(result: QueryResult<T>): boolean {
  return result.success === true;
}

/**
 * 結果からデータを安全に取得する
 */
export function getDataOrThrow<T>(result: QueryResult<T>): T {
  if (!isSuccess(result)) {
    throw new Error(result.error || 'クエリが失敗しました');
  }
  return result.data;
}

/**
 * 結果からデータを取得する（デフォルト値付き）
 */
export function getDataOrDefault<T>(result: QueryResult<T>, defaultValue: T): T {
  return isSuccess(result) ? result.data : defaultValue;
}

/**
 * 結果をマップする（成功時のみ変換）
 */
export function mapResult<T, U>(
  result: QueryResult<T>,
  mapFn: (data: T) => U
): QueryResult<U> {
  if (!isSuccess(result)) {
    return result as QueryResult<U>;
  }
  try {
    const mapped = mapFn(result.data);
    return createSuccessResult(mapped);
  } catch (e) {
    return createErrorResult(
      `結果のマッピング中にエラーが発生しました: ${e instanceof Error ? e.message : String(e)}`
    );
  }
}

/**
 * 複数の結果を結合する
 */
export function combineResults<T>(results: QueryResult<T>[]): QueryResult<T[]> {
  const data: T[] = [];
  const errors: string[] = [];
  
  for (const result of results) {
    if (isSuccess(result)) {
      data.push(result.data);
    } else {
      errors.push(result.error || '不明なエラー');
    }
  }
  
  if (errors.length > 0) {
    return createErrorResult(
      `複数のエラーが発生しました: ${errors.join('; ')}`
    );
  }
  
  return createSuccessResult(data);
}
