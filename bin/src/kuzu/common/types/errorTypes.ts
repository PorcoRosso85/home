/**
 * 共通エラー型定義
 * 規約準拠: 共用体型によるエラーハンドリング、throw文禁止
 */

// 基本エラー型（Tagged Union）
export type QuerySuccess<T> = {
  status: "success";
  data: T;
};

export type ValidationError = {
  status: "validation_error";
  field?: string;
  message: string;
  code?: string;
};

export type ExecutionError = {
  status: "execution_error";
  code: string;
  message: string;
  details?: any;
};

export type NotFoundError = {
  status: "not_found";
  resource: string;
  message: string;
};

export type FileSystemError = {
  status: "file_error";
  path: string;
  message: string;
  operation: "read" | "write" | "create" | "delete";
};

export type ConfigurationError = {
  status: "config_error";
  key: string;
  message: string;
};

// 汎用結果型（共用体型）
export type CommonResult<T> = 
  | QuerySuccess<T>
  | ValidationError
  | ExecutionError
  | NotFoundError
  | FileSystemError
  | ConfigurationError;

// 型ガード関数（パターンマッチ準備）
export function isSuccess<T>(result: CommonResult<T>): result is QuerySuccess<T> {
  return result.status === "success";
}

export function isError<T>(result: CommonResult<T>): result is Exclude<CommonResult<T>, QuerySuccess<T>> {
  return result.status !== "success";
}
