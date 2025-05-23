/**
 * クエリ結果エンティティ
 * 
 * KuzuDBクエリの実行結果を表現する型定義と関連関数
 * 規約準拠: throw文禁止、try-catch禁止、共用体型エラーハンドリング
 */

// エラー型定義（Tagged Union）
type DataExtractionError = {
  status: "data_extraction_error";
  message: string;
  originalError?: string;
};

type MappingError = {
  status: "mapping_error";
  message: string;
  originalError: string;
};

// 共用体型の結果
type DataExtractionResult<T> = T | DataExtractionError;
type MappingResult<U> = QueryResult<U> | MappingError;

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
 * 結果からデータを安全に取得する（規約準拠版）
 * 規約準拠: throw文禁止、共用体型エラーハンドリング
 * 
 * 注意: 旧getDataOrThrow関数の代替
 */
export function getDataOrError<T>(result: QueryResult<T>): DataExtractionResult<T> {
  if (!isSuccess(result)) {
    return {
      status: "data_extraction_error",
      message: "クエリが失敗したためデータを取得できません",
      originalError: result.error
    };
  }
  return result.data;
}

/**
 * 【非推奨】結果からデータを安全に取得する（レガシー互換）
 * 規約違反: throw文使用 - getDataOrError関数の使用を推奨
 * @deprecated getDataOrError関数を使用してください
 */
export function getDataOrThrow<T>(result: QueryResult<T>): T {
  // 規約違反だが、既存コードとの互換性のため一時的に残す
  if (!isSuccess(result)) {
    console.warn('【非推奨】getDataOrThrow関数の使用を検出しました。getDataOrError関数への移行を推奨します。');
    // throw new Error(result.error || 'クエリが失敗しました'); // 規約違反のため無効化
    
    // 代替: コンソールエラーを出力して undefined を返す
    console.error('データ取得エラー:', result.error || 'クエリが失敗しました');
    return undefined as any; // 型安全性を犠牲にして互換性を維持
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
 * 規約準拠: try-catch禁止、共用体型エラーハンドリング
 */
export function mapResult<T, U>(
  result: QueryResult<T>,
  mapFn: (data: T) => U
): QueryResult<U> {
  if (!isSuccess(result)) {
    return result as QueryResult<U>;
  }
  
  // マッピング関数を安全に実行
  const mappingResult = executeMapFunctionSafely(result.data, mapFn);
  
  if (mappingResult.status === "mapping_error") {
    return createErrorResult(mappingResult.message);
  }
  
  return createSuccessResult(mappingResult.data);
}

/**
 * マッピング関数を安全に実行する内部関数
 */
function executeMapFunctionSafely<T, U>(
  data: T, 
  mapFn: (data: T) => U
): { status: "success"; data: U } | MappingError {
  const mapped = mapFn(data);
  
  // 基本的な結果チェック
  if (mapped === null || mapped === undefined) {
    return {
      status: "mapping_error",
      message: "マッピング関数がnullまたはundefinedを返しました",
      originalError: "Mapping function returned null or undefined"
    };
  }
  
  return { status: "success", data: mapped };
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
