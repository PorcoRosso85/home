/**
 * Result型パターンの実装
 * エラー処理規約に準拠
 */

export type Result<T> = 
  | { ok: true; data: T }
  | { ok: false; error: ErrorInfo };

export interface ErrorInfo {
  code: string;
  message: string;
  details?: unknown;
}

export const Result = {
  ok<T>(data: T): Result<T> {
    return { ok: true, data };
  },

  error<T>(code: string, message: string, details?: unknown): Result<T> {
    return { ok: false, error: { code, message, details } };
  },

  isOk<T>(result: Result<T>): result is { ok: true; data: T } {
    return result.ok;
  },

  isError<T>(result: Result<T>): result is { ok: false; error: ErrorInfo } {
    return !result.ok;
  },

  map<T, U>(result: Result<T>, fn: (data: T) => U): Result<U> {
    if (result.ok) {
      return Result.ok(fn(result.data));
    }
    return result;
  },

  flatMap<T, U>(result: Result<T>, fn: (data: T) => Result<U>): Result<U> {
    if (result.ok) {
      return fn(result.data);
    }
    return result;
  }
};