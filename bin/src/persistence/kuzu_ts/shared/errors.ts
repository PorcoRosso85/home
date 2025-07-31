/**
 * 型安全なエラー定義
 * 
 * requirement/graph互換のエラー型を提供
 */

/**
 * ファイル操作エラー
 */
export interface FileOperationError {
  type: "FileOperationError";
  message: string;
  operation: string;
  file_path: string;
  permission_issue?: boolean;
  exists?: boolean;
}

/**
 * バリデーションエラー
 */
export interface ValidationError {
  type: "ValidationError";
  message: string;
  field: string;
  value: string;
  constraint: string;
  suggestion?: string;
}

/**
 * リソース未発見エラー
 */
export interface NotFoundError {
  type: "NotFoundError";
  message: string;
  resource_type: string;
  resource_id: string;
  search_locations?: string[];
}

/**
 * エラー型のユニオン型
 */
export type KuzuError = FileOperationError | ValidationError | NotFoundError;

/**
 * FileOperationError生成ヘルパー
 */
export function createFileOperationError(
  message: string,
  operation: string,
  file_path: string,
  options?: {
    permission_issue?: boolean;
    exists?: boolean;
  }
): FileOperationError {
  return {
    type: "FileOperationError",
    message,
    operation,
    file_path,
    ...options,
  };
}

/**
 * ValidationError生成ヘルパー
 */
export function createValidationError(
  message: string,
  field: string,
  value: string,
  constraint: string,
  suggestion?: string
): ValidationError {
  return {
    type: "ValidationError",
    message,
    field,
    value,
    constraint,
    suggestion,
  };
}

/**
 * NotFoundError生成ヘルパー
 */
export function createNotFoundError(
  message: string,
  resource_type: string,
  resource_id: string,
  search_locations?: string[]
): NotFoundError {
  return {
    type: "NotFoundError",
    message,
    resource_type,
    resource_id,
    search_locations,
  };
}

/**
 * エラー型判定ヘルパー
 */
export function isFileOperationError(error: unknown): error is FileOperationError {
  return (
    typeof error === "object" &&
    error !== null &&
    "type" in error &&
    error.type === "FileOperationError"
  );
}

export function isValidationError(error: unknown): error is ValidationError {
  return (
    typeof error === "object" &&
    error !== null &&
    "type" in error &&
    error.type === "ValidationError"
  );
}

export function isNotFoundError(error: unknown): error is NotFoundError {
  return (
    typeof error === "object" &&
    error !== null &&
    "type" in error &&
    error.type === "NotFoundError"
  );
}

export function isKuzuError(error: unknown): error is KuzuError {
  return isFileOperationError(error) || isValidationError(error) || isNotFoundError(error);
}